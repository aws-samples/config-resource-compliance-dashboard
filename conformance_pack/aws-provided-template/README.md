# Threat-Informed Security Best Practices (Fundamental)

This page supports the public **Threat-Informed Security Best Practices (Fundamental)** conformance pack offered in the [AWS Config sample conformance pack templates](https://docs.aws.amazon.com/config/latest/developerguide/threat-informed-security-best-practices-fundamental.html). It is for customers who want to install the conformance pack by working directly with its YAML templates — from the AWS Config console (as a sample template) or with the AWS CLI / CloudFormation.

For background on what the pack is, who it is for, and how its rules are classified, see the [conformance pack overview](../README.md). For the full rule list, naming convention, parameters, and remediation, see the [conformance pack specification](../crcd-conformance-pack-specification.md).

> **Recommended:** For most deployments we recommend the CloudFormation template described in the [conformance pack overview](../README.md). It installs everything in one step, handles the regional availability of rules automatically (skipping any rule not available in a Region), and supports both AWS Organizations and standalone deployments. Use the templates on this page for testing the conformance pack, or when you specifically want to manage the YAML directly or deploy the AWS-provided sample template from the console.
>
> If you have already deployed the conformance pack using that CloudFormation template, no further action is required; the instructions on this page do not apply to you.


## Prerequisites

- **AWS Config** must be enabled in all accounts and Regions where you deploy this conformance pack. This template supports both single-account deployment (`put-conformance-pack`) and organization-wide deployment (`put-organization-conformance-pack`).
- **AWS Config recorder** must record the resource types evaluated by the rules in this pack. The base template requires: `AWS::S3::Bucket`, `AWS::S3::AccessPoint`, `AWS::EC2::Instance`, `AWS::EC2::SecurityGroup`, `AWS::EC2::LaunchTemplate`, `AWS::AutoScaling::LaunchConfiguration`. The full template additionally requires `AWS::IAM::User` to be recorded (in at least one Region) for the IAM MFA rules (`IAM_USER_MFA_ENABLED`, `MFA_ENABLED_FOR_IAM_CONSOLE_ACCESS`) to produce per-user compliance results.
- **Full version only**: Deploy the prerequisites CloudFormation template (`Threat-Informed-Security-Best-Practices-Fundamental-Prerequisites.yaml`) first to create the required Lambda functions. See [Deployment](#deployment) below.


## Rules, Parameters, and Remediation

The complete list of AWS Config rules, the `sire-` naming convention, the input parameters (including which rules consume them), and the remediation guidance are maintained in the [conformance pack specification](../crcd-conformance-pack-specification.md). This README focuses on how to deploy and operate the YAML templates; see the specification for rule-level, parameter, and remediation detail.


## Regional Availability

Some AWS Config managed rules are not available in all AWS Regions. Before deploying this conformance pack, verify that the rules are supported in your target Region by consulting the [AWS Config Managed Rules by Region Availability](https://docs.aws.amazon.com/config/latest/developerguide/managing-rules-by-region-availability.html) page.

If you deploy this conformance pack in a Region where a rule is not available, the deployment will fail. Remove unsupported rules from the template before deploying in those Regions.

## Variants
This conformance pack ships as two templates: **full** and **base**. The full template is a complete superset — it includes everything in the base template plus the IAM rules.

The base template (`Threat-Informed-Security-Best-Practices-Fundamental.yaml`) contains only AWS Config managed rules and can be deployed directly from the AWS Config console — on the **Deploy conformance pack** page, choose **Use sample template** and select **Threat-Informed Security Best Practices (Fundamental)** — with no prerequisites. The full template (`Threat-Informed-Security-Best-Practices-Fundamental-Complete.yaml`) includes all the rules of the base version, and adds IAM protection rules — including two custom Lambda-based rules — and requires deploying the prerequisites template first.

| Version | File | Rules | Prerequisites | Console Dropdown |
|---------|------|-------|---------------|-----------------|
| Base | `Threat-Informed-Security-Best-Practices-Fundamental.yaml` | 10 managed rules | None | Yes |
| Full | `Threat-Informed-Security-Best-Practices-Fundamental-Complete.yaml` | 14 managed + 2 custom rules | Lambda functions via `Threat-Informed-Security-Best-Practices-Fundamental-Prerequisites.yaml` | No (download only) |

### Base template rules

| Rule name | lv1 classification | lv2 classification |
|-----------|--------------------|--------------------|
| `sire-ia-s3-s3-bucket-public-read-prohibited` | Initial Access (`ia`) | S3 Protection (`s3`) |
| `sire-ia-s3-s3-bucket-public-write-prohibited` | Initial Access (`ia`) | S3 Protection (`s3`) |
| `sire-ia-s3-s3-access-point-in-vpc-only` | Initial Access (`ia`) | S3 Protection (`s3`) |
| `sire-ia-s3-s3-access-point-public-access-blocks` | Initial Access (`ia`) | S3 Protection (`s3`) |
| `sire-ia-s3-s3-account-level-public-access-blocks-periodic` | Initial Access (`ia`) | S3 Protection (`s3`) |
| `sire-ia-s3-s3-bucket-level-public-access-prohibited` | Initial Access (`ia`) | S3 Protection (`s3`) |
| `sire-ia-ec2-autoscaling-launchconfig-requires-imdsv2` | Initial Access (`ia`) | EC2 Protection (`ec2`) |
| `sire-ia-ec2-ec2-imdsv2-check` | Initial Access (`ia`) | EC2 Protection (`ec2`) |
| `sire-ia-ec2-ec2-launch-template-imdsv2-check` | Initial Access (`ia`) | EC2 Protection (`ec2`) |
| `sire-ia-ra-vpc-sg-port-restriction-check` | Initial Access (`ia`) | Resource Access Protection (`ra`) |

### Additional rules in the full template

These IAM rules are present only in the full template (the two custom rules require the prerequisites template):

| Rule name | lv1 classification | lv2 classification |
|-----------|--------------------|--------------------|
| `sire-ia-iam-root-account-mfa-enabled` | Initial Access (`ia`) | IAM Protection (`iam`) |
| `sire-ia-iam-iam-root-access-key-check` | Initial Access (`ia`) | IAM Protection (`iam`) |
| `sire-ia-iam-iam-user-mfa-enabled` | Initial Access (`ia`) | IAM Protection (`iam`) |
| `sire-ia-iam-mfa-enabled-for-iam-console-access` | Initial Access (`ia`) | IAM Protection (`iam`) |
| `sire-ia-iam-iam-root-not-used-regularly` (custom) | Initial Access (`ia`) | IAM Protection (`iam`) |
| `sire-ia-iam-iam-user-access-key-check` (custom) | Initial Access (`ia`) | IAM Protection (`iam`) |


## Deployment

For multi-region environments, deploy the **full template in a single primary region** (for full IAM coverage including custom Lambda rules) and the **base template in all other regions**. IAM resources are global, so evaluating them in every region would produce redundant results at unnecessary cost; the base template covers the regional resources (S3 buckets, EC2 instances, security groups, etc.) where they actually exist. Each region should have exactly one conformance pack named `Threat-Informed-Security-Best-Practices-Fundamental` — never deploy both templates in the same region.

| Region | Template | What it covers |
|--------|----------|----------------|
| Primary (e.g., us-east-1) | Full | S3, EC2, Security Groups + IAM managed rules + custom Lambda rules |
| All other regions | Base | S3, EC2, Security Groups |

In a multi-account setup (AWS Organizations), this recommendation applies to every account: deploy the full template in one primary region per account, and the base template in all other regions of that account.


### Single Account Deployment

#### Step 1: Deploy prerequisites in the primary region

Deploy the prerequisites CloudFormation template to create the Lambda functions and IAM roles needed by the full template:

```
aws cloudformation deploy \
  --template-file Threat-Informed-Security-Best-Practices-Fundamental-Prerequisites.yaml \
  --stack-name sire-conformance-pack-prerequisites \
  --capabilities CAPABILITY_NAMED_IAM \
  --region <PRIMARY_REGION>
```

Get the Lambda ARNs from the stack outputs:

```
aws cloudformation describe-stacks \
  --stack-name sire-conformance-pack-prerequisites \
  --query 'Stacks[0].Outputs' \
  --region <PRIMARY_REGION>
```

#### Step 2: Deploy the full template in the primary region

Deploy the complete conformance pack (all rules including IAM + custom Lambda) in the primary region:

```
aws configservice put-conformance-pack \
  --conformance-pack-name Threat-Informed-Security-Best-Practices-Fundamental \
  --template-body file://Threat-Informed-Security-Best-Practices-Fundamental-Complete.yaml \
  --conformance-pack-input-parameters \
    ParameterName=RootNotUsedRegularlyLambdaArn,ParameterValue=<ARN_FROM_STEP_1> \
    ParameterName=UserAccessKeyCheckLambdaArn,ParameterValue=<ARN_FROM_STEP_1> \
    ParameterName=RootUsageThresholdDays,ParameterValue=5 \
  --region <PRIMARY_REGION>
```

`RootUsageThresholdDays` sets the look-back window (in days) for the `sire-ia-iam-iam-root-not-used-regularly` rule; adjust the value (default `5`) as needed.

#### Step 3: Deploy the base template in all other regions

Deploy the base conformance pack (managed rules only, no Lambda prerequisites) in every other region where AWS Config is enabled:

```
REGIONS="us-east-2 us-west-2 eu-west-1 eu-central-1 ap-southeast-1 ap-northeast-1"

for REGION in $REGIONS; do
  echo "Deploying base conformance pack in $REGION..."
  aws configservice put-conformance-pack \
    --conformance-pack-name Threat-Informed-Security-Best-Practices-Fundamental \
    --template-body file://Threat-Informed-Security-Best-Practices-Fundamental.yaml \
    --region $REGION
done
```

### Organization-Wide Deployment

This section describes how to deploy the conformance pack across all accounts in an AWS Organization.

The deployment is split into three steps:

- **Step 1 — Delegated administrator account (once):** deploy the prerequisite
  Lambda functions to every member account (primary Region only) using a
  service-managed CloudFormation StackSet.
- **Step 2 — Delegated administrator account (once):** deploy the **base** conformance
  pack to all non-primary Regions organization-wide.
- **Step 3 — Each member account (repeat):** deploy the **full** conformance
  pack in the primary Region of each account, pointing it at that account's own
  prerequisite Lambda functions.

> **Why the full pack is deployed per account.** The complete pack's two
> custom rules invoke account-local Lambda functions. Each function's ARN
> contains its own account ID, and the functions only allow invocation from the
> account they live in (`SourceAccount: !Ref AWS::AccountId` in the prerequisites
> template). A single organization-level `put-organization-conformance-pack`
> call can only pass one Lambda ARN to every account, so it cannot work for the
> full version of the conformance pack. The base pack has no Lambda dependency and *is* deployed
> organization-wide (in Step 2).

#### Deployment prerequisites

- **AWS Config** enabled organization-wide, in every account and Region you
  target.
- **Service-managed StackSets**: [enable trusted access](https://docs.aws.amazon.com/organizations/latest/userguide/services-that-can-integrate-cloudformation.html#integrate-enable-ta-cloudformation)
  for CloudFormation StackSets in AWS Organizations.
- Run Step 1 and Step 2 from an account designated as the delegated administrator of both [AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-orgs-delegated-admin.html) and [AWS Config](https://docs.aws.amazon.com/config/latest/developerguide/aggregated-register-delegated-administrator.html) (recommended), or from the management (payer) account of your organization.

---

#### Step 1: From the delegated administrator account (primary Region)

Perform all of the following from the delegated administrator account.

> **Steps 1a and 1b work together.** Step 1a *defines* the StackSet but deploys
> nothing; Step 1b *deploys* it to the member accounts. It is the two together
> that create the Lambda functions and IAM roles in every targeted account, so
> run both.

##### Step 1a: Create the StackSet (defines what will be deployed; deploys nothing yet)

Create a service-managed StackSet from the prerequisites template. This only
registers the template and its parameters — no resources are created in any
account until you deploy stack instances in Step 1b.

```
PRIMARY_REGION=<PRIMARY_REGION>

aws cloudformation create-stack-set \
  --stack-set-name sire-conformance-pack-prerequisites \
  --template-body file://Threat-Informed-Security-Best-Practices-Fundamental-Prerequisites.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --permission-model SERVICE_MANAGED \
  --auto-deployment Enabled=true,RetainStacksOnAccountRemoval=false \
  --call-as DELEGATED_ADMIN \
  --region "$PRIMARY_REGION"
```

- `--call-as DELEGATED_ADMIN` - Use it if you run the command from
 the delegated administrator account. If you run the command from the management
 (payer) account instead, omit the flag (or pass `--call-as SELF`).

##### Step 1b: Deploy stack instances to every member account (creates the Lambda functions and IAM roles)

Create stack instances from the StackSet defined in Step 1a, across your organization, **in the primary Region only**. This is the step that actually creates the Lambda functions and IAM roles in each targeted account:

```
PRIMARY_REGION=<PRIMARY_REGION>

aws cloudformation create-stack-instances \
  --stack-set-name sire-conformance-pack-prerequisites \
  --deployment-targets OrganizationalUnitIds=<ROOT_OR_OU_IDS> \
  --regions "$PRIMARY_REGION" \
  --call-as DELEGATED_ADMIN \
  --region "$PRIMARY_REGION"
```

- `<ROOT_OR_OU_IDS>` — the organization root ID (`r-xxxx`) to target all accounts, or a comma-separated list of Organizational Unit IDs (`ou-xxxx-xxxxxxxx`).
- `--call-as DELEGATED_ADMIN` - Use it if you run the command run from
 the delegated administrator account. If you run the command from the management
 (payer) account instead, omit the flag (or pass `--call-as SELF`).

> **Deploy to the primary Region only for this StackSet.** The prerequisites
> template uses fixed IAM role names (`SIREConfPackRuleRootNotUsedRegularly`,
> `SIREConfPackRuleUserAccessKeyCheck`) and fixed Lambda function names
> (`sire-root-not-used-regularly`, `sire-user-access-key-check`). IAM role names
> are global per account, so adding more than one Region to `--regions` would
> cause the second Region's instance to fail on a name collision. IAM is global,
> so a single Region per account is all you need.

**Optional parameters and targeting:**

- **Exclude specific accounts** (for example, accounts where AWS Config is not
  enabled — otherwise those instances fail): add an `Accounts` list and an
  `AccountFilterType` to `--deployment-targets`. To deploy to an OU *except*
  certain accounts:

  ```
  --deployment-targets OrganizationalUnitIds=<OU_IDS>,Accounts=<ACCOUNT_IDS>,AccountFilterType=DIFFERENCE
  ```

  For `create-stack-instances`, `AccountFilterType` accepts `DIFFERENCE` (all
  accounts in the OU *except* the listed ones — useful for excluding suspended
  accounts or accounts without AWS Config) or `INTERSECTION` (only the listed
  accounts within the OU). For the full description of `AccountFilterType`,
  `Accounts`, and `OrganizationalUnitIds`, see the [DeploymentTargets API
  reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_DeploymentTargets.html).


#### Step 2: Deploy the base pack to all other Regions (organization-wide)

Remain in the delegated administrator account.

The base conformance pack has no Lambda dependency, so it is deployed
organization-wide with `put-organization-conformance-pack`. Deploy it to every
Region **except** the primary Region (the primary Region is covered by the
full conformance pack in Step 3):

> Make sure the list of Regions you specify in `OTHER_REGIONS` **does not** have your primary region.

```
OTHER_REGIONS="us-east-2 us-west-2 eu-west-1 eu-central-1 ap-southeast-1 ap-northeast-1"

for REGION in $OTHER_REGIONS; do
  echo "Deploying base conformance pack in $REGION..."
  aws configservice put-organization-conformance-pack \
    --organization-conformance-pack-name Threat-Informed-Security-Best-Practices-Fundamental \
    --template-body file://Threat-Informed-Security-Best-Practices-Fundamental.yaml \
    --region $REGION
done
```

- To skip specific accounts (for example, where AWS Config is not enabled), add
  `--excluded-accounts <ACCOUNT_IDS>` to the command.

---

#### Step 3: In each member account (primary Region)

> **Before you begin, confirm Step 2 finished.** The base pack deploys asynchronously.
> From the delegated administrator (or management) account, verify that every
> account reports `CREATE_SUCCESSFUL` before proceeding:
>
> ```
> PRIMARY_REGION=<PRIMARY_REGION>
> aws configservice get-organization-conformance-pack-detailed-status \
>   --organization-conformance-pack-name Threat-Informed-Security-Best-Practices-Fundamental \
>   --region "$PRIMARY_REGION"
> ```
>
> Every entry in the output must show `Status: CREATE_SUCCESSFUL`. If any account
> is still `CREATE_IN_PROGRESS`, wait and re-run the command. If any account is
> `CREATE_FAILED`, check its `ErrorMessage` (a common cause is AWS Config not
> being enabled in that account/Region) and resolve it before continuing.

Repeat this step in every member account that should run the complete pack, including the delegated administrator account. Log into the account and open AWS CloudShell in the primary Region (or use any authenticated AWS CLI session for that account).

The snippet below resolves that account's own Lambda ARNs by their fixed
function names and deploys the full conformance pack in one shot — no manual
ARN copying required. Set `PRIMARY_REGION` first, then paste the block:

```
PRIMARY_REGION=<PRIMARY_REGION>

ROOT_ARN=$(aws lambda get-function \
  --function-name sire-root-not-used-regularly \
  --query 'Configuration.FunctionArn' --output text \
  --region "$PRIMARY_REGION")

KEY_ARN=$(aws lambda get-function \
  --function-name sire-user-access-key-check \
  --query 'Configuration.FunctionArn' --output text \
  --region "$PRIMARY_REGION")

aws configservice put-conformance-pack \
  --conformance-pack-name Threat-Informed-Security-Best-Practices-Fundamental \
  --template-body file://Threat-Informed-Security-Best-Practices-Fundamental-Complete.yaml \
  --conformance-pack-input-parameters \
    ParameterName=RootNotUsedRegularlyLambdaArn,ParameterValue="$ROOT_ARN" \
    ParameterName=UserAccessKeyCheckLambdaArn,ParameterValue="$KEY_ARN" \
    ParameterName=RootUsageThresholdDays,ParameterValue=5 \
  --region "$PRIMARY_REGION"
```

Because each account resolves its own ARNs at deploy time, every account gets a full conformance pack wired to its own local Lambda functions.

`RootUsageThresholdDays` sets the look-back window (in days) for the `sire-ia-iam-iam-root-not-used-regularly` rule; adjust the value (default `5`) as needed. Set it consistently in every account where you deploy the full pack.


### Base-Only Deployment (Fallback)

If you only want the base managed rules without the IAM custom Lambda rules, you can deploy the base template in all regions without prerequisites:

```
aws configservice put-conformance-pack \
  --conformance-pack-name Threat-Informed-Security-Best-Practices-Fundamental \
  --template-body file://Threat-Informed-Security-Best-Practices-Fundamental.yaml \
  --region <REGION>
```

#### Base-Only Deployment alternative
The base template of the conformance pack is provided by the AWS Config service and is [documented in the AWS Config developer guide](https://docs.aws.amazon.com/config/latest/developerguide/threat-informed-security-best-practices-fundamental.html). You can deploy it directly from the AWS Config console:
  1. In the AWS Config console, go to **Conformance packs** and choose **Deploy conformance pack**.
  1. Under **Step 1: Specify template**, for **Conformance pack template** choose **Use sample template**.
  1. Under **Sample template**, open the **Select a sample template** dropdown and choose **Threat-Informed Security Best Practices (Fundamental)**.
  1. Choose **Next**, specify the conformance pack details, delete the parameters you don't use, then review and deploy.

This is the quickest way to deploy the conformance pack and makes a good first step to evaluate the pack before a wider rollout.

**Caveats:**
  - Deploys only to the **current account and Region** (the account and Region you are signed in to). It is not organization-wide and does not fan out to other Regions.
  - Deploys the **base** template only — the standard AWS Config managed rules. It does **not** include the IAM custom Lambda-based rules (`sire-ia-iam-iam-root-not-used-regularly`, `sire-ia-iam-iam-user-access-key-check`), which require the prerequisites and the extended version.
  - To get the custom rules, organization-wide coverage, or multi-Region deployment, use one of the deployment modes above.
