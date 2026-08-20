# Multi-Account Preprocessing: Design Decision (Cross-account read vs. S3 replication)

**Decision:** for the multi-account deployment we use **S3 replication into a transient bucket in the
Dashboard account** (Option B below), not direct cross-account reads. This note records the
difficulties of the alternative (giving the preprocessing compute cross-account read access to the
AWS Config Logs bucket) and the cost comparison that led to the decision.

## Context

The preprocessing feature splits oversized AWS Config files (files that exceed Athena's ~32 MB
per-row limit) into smaller files. In a **multi-account** deployment:

- The **AWS Config Logs bucket** lives in the **AWS Config account** (the account we most want to
  protect - it holds the organization's audit data).
- All preprocessing compute (the Producer Lambda and the Fargate task) runs in the **Dashboard
  account**.

The core problem: the compute in the Dashboard account must read Config files that live in the AWS
Config account. There are two broad ways to bridge that gap:

- **Option A - Direct cross-account read:** the Producer Lambda and/or the Fargate task read the AWS
  Config Logs bucket directly across the account boundary.
- **Option B - S3 replication:** the AWS Config Logs bucket replicates its objects into a transient
  bucket in the Dashboard account, and preprocessing then runs entirely within the Dashboard
  account (the same way it does in a single-account deployment).

## Why we are considering replication (Option B)

Two independent reasons pushed us toward replication.

### 1. Cross-account access to the protected bucket is hard to do safely

To let the Dashboard-account compute read the AWS Config Logs bucket, we evaluated several
mechanisms, each with a real drawback:

- **Modify the AWS Config Logs bucket policy (and its KMS key policy) to grant the Dashboard roles
  read/decrypt.** For **S3**, cross-account access *always* requires a statement on the bucket's
  resource policy (unlike KMS, there is no "delegate to IAM via root" shortcut for S3). That means
  the deployment must **write** the AWS Config Logs bucket policy - and, if the bucket is
  KMS-encrypted, the **KMS key policy** (via `PutKeyPolicy`, which *replaces* the entire key policy).
  Problems:
  - The automation would need `s3:PutBucketPolicy` and `kms:PutKeyPolicy` on the most sensitive
    account. These are exactly the permissions security teams lock down, frequently with **SCPs**
    that deny them outright. If such an SCP exists, the deployment fails.
  - Concentrating "can rewrite the audit bucket / key policy" in an automated component on the
    protected account is a large trust and blast-radius ask that customers may reject.

- **Assume-role into the AWS Config account.** Create an IAM role in the AWS Config account that
  the Dashboard roles assume, with read access to the bucket (+ `kms:Decrypt`). This avoids
  modifying the bucket/key policies and is SCP-friendlier (it only creates a new role). But it moves
  the complexity into code:
  - **A single `s3:CopyObject` cannot cross the account boundary.** A copy is executed by one
    principal, which must hold *both* `GetObject` on the source and `PutObject` on the destination.
    With assume-role, the assumed AWS Config-account credentials can read the source but cannot write
    the Dashboard bucket, and the Dashboard credentials can write but cannot read the source. So the
    small-file "server-side copy" fast path (used in single-account) does not work; it must become a
    download-then-upload through the compute, or every file must go to Fargate.
  - The **Fargate task** would assume the role to stream the source and use its own role to write
    the Dashboard bucket - workable, but it needs **credential refresh** for long-running splits
    (assumed-role credentials expire, default 1 hour).
  - To avoid the download-then-upload logic in the Lambda, one option was to **route every file to
    Fargate** in multi-account. That removes the Lambda's cross-account read, but it means a Fargate
    task launches for *every* Config file - which is the cost problem quantified below.

In short: the direct-read options either require writing the protected account's resource policies
(SCP-prone, high trust) or push non-trivial credential-handling logic into the compute and, in the
simplest variant, run Fargate on every file.

### 2. Cost at organization scale

Routing every Config file to a Fargate task does not scale economically. AWS Config delivers:

- **ConfigHistory files every 6 hours**, with **one file per (resource type x region)** that changed
  in the window - so the count scales with how many resource types churn, not with the number of
  changes.
- **ConfigSnapshot files** on the configured delivery frequency (1/3/6/12/24 hours), one file per
  account-region per delivery.

For an organization of **100 accounts x 10 regions = 1,000 account-regions**, a realistic daily
volume is **~100,000 history files/day** (range ~50k-200k, workload-dependent) plus **~1,000
snapshot files/day** at 24h snapshot frequency.

Replication, by contrast, lets preprocessing run within the Dashboard account exactly as it does in
a single-account deployment: only genuinely **oversized** files ever reach Fargate; everything else
is cheap. The transient bucket (with a tight lifecycle) costs almost nothing.

## Cost comparison

Assumptions:

- Org scale: 1,000 account-regions -> ~100,000 ConfigHistory files/day + ~1,000 ConfigSnapshot
  files/day (24h snapshot frequency).
- **Same-region** replication (no cross-region data-transfer charge).
- Fargate task: 1 vCPU + 4 GB ~= $0.058/hour ~= $0.00097/minute.
- **Fargate average task duration: 3 minutes** (largest files observed ~5 minutes) -> ~$0.0029/task.
- Option B assumption: Fargate runs on **20% of daily snapshots** (~200 tasks/day) - i.e. only the
  oversized files, tied to the small snapshot count rather than total file count.
- Prices are approximate, us-east-1-class, and for relative comparison only.

### Option A - Fargate on every file

| Item | Daily | Monthly |
|---|---|---|
| Fargate tasks (~101,000/day x $0.0029) | ~$293 | **~$8,800** |
| Operational load | ~101,000 `RunTask` calls/day (throttling / concurrency risk) | - |

### Option B - Same-region replication + Fargate on 20% of snapshots

| Item | Daily | Monthly |
|---|---|---|
| Fargate tasks (~200/day x $0.0029) | ~$0.58 | ~$17 |
| Replication PUT requests (~101,000/day x $0.005/1,000) | ~$0.51 | ~$15 |
| Transient bucket storage (~100 GB, ~1-day lifecycle) | ~$0.08 | ~$2 |
| **Total** | **~$1.10** | **~$34** |

### Side by side

| | Option A (Fargate/file) | Option B (replication + 20% snapshots) |
|---|---|---|
| Fargate tasks/day | ~101,000 | ~200 |
| Fargate cost/month | ~$8,800 | ~$17 |
| Replication PUTs/month | - | ~$15 |
| Transient storage/month | - | ~$2 |
| **Total/month** | **~$8,800** | **~$34** |
| Ops load | ~101k tasks/day | ~200 tasks/day |

### Sensitivity

- **History at 200k/day:** Option A ~= **~$17,500/month**; Option B ~= **~$52/month** (replication
  ~$30, Fargate ~$17, storage ~$5).
- **Snapshots at 6h (4,000/day), Fargate = 20% = 800 tasks/day:** Option B ~= **~$85/month**.
- **Break-even:** at 3-minute tasks, Fargate-per-file only matches Option B's ~$34/month at roughly
  a few hundred files/day total - far below organization scale. Fargate-per-file is only economical
  for very small deployments.

Note: in Option B the dominant cost is the **replication PUT requests** (scaling with total file
count), not Fargate or storage - and it is still one to two orders of magnitude below Option A.

## Decision and tradeoff

At organization scale, **same-region S3 replication (Option B) is roughly 150-500x cheaper** than
running a Fargate task per file (~$34-85/month vs. ~$8,800-17,500/month), and it removes the
operational risk of launching tens of thousands of Fargate tasks per day. It also reunifies the
multi-account processing logic with the single-account path: only oversized files reach Fargate.

The tradeoff is that replication still touches the AWS Config account - it needs an S3 **replication
role** and a **replication configuration** on the source bucket (`PutBucketReplication`), plus KMS
grants if the source is encrypted. This is a smaller and more standard footprint than granting
policy-write permissions for direct cross-account reads, and the main dashboard stack
(`cloudformation/cid-crcd-stack.yaml`) **already implements this cross-account replication pattern**
(`ConfigBucketReplicationConfigurationLambda`, the replication role, and KMS handling), which we can
mirror rather than invent.

## How it is implemented (two steps)

- **Step 2.1 - Dashboard account (run first):** installs the preprocessing resources and a
  **transient bucket** (versioned, with a tight lifecycle) that receives the replicated AWS Config
  files and is the same-account source that triggers the Producer Lambda. Outputs the transient
  bucket name.
- **Step 2.2 - AWS Config account (run second):** installs cross-account S3 replication from the AWS
  Config Logs bucket to the transient bucket from step 2.1 (its name is provided as an input): the
  replication configuration, the replication IAM role, and, if the AWS Config Logs bucket is
  KMS-encrypted, the KMS grants needed for replication.

The transient bucket name is the only value that must be carried from step 2.1 to step 2.2.
