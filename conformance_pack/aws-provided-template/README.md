# Security Best Practices for Security Incident Response Engineering Team (Fundamental)

## Purpose

This conformance pack contains a focused set of AWS Config rules recommended by [AWS Security Incident Response](https://aws.amazon.com/security-incident-response/) security engineers. These rules target the most common misconfigurations that security engineers observe causing real security incidents in customer environments.

Unlike larger conformance packs that may contain 50+ rules mapped to a compliance framework, this pack is intentionally small and focused. It is designed for customers who are new to AWS Config and security monitoring and want to start with the highest-impact checks without the cost and complexity of deploying dozens of rules. Additionally, any customer can deploy this conformance pack to perform fundamental security posture checks on their AWS environment, regardless of their experience level. Each rule in this pack addresses a specific misconfiguration that is known to be actively exploited by threat actors.

The rules are organized using categories from the [Threat Technique Catalog for AWS](https://aws-samples.github.io/threat-technique-catalog-for-aws/), which is in turn based on [MITRE ATT&CK®](https://attack.mitre.org/). This grouping is intended to help you reason about *why* a misconfiguration matters in terms of attacker behavior — it is not a claim that the pack fully covers, maps to, or conforms to the catalog or MITRE ATT&CK.

### Why this pack

- **Curated by incident responders**: Rules are selected based on multi-year experience supporting AWS customers during active security incidents — not from a theoretical compliance checklist.
- **Low cost, high impact**: A small number of rules keeps AWS Config costs low while covering the misconfigurations most frequently exploited in real attacks.
- **Accessible to beginners**: Customers who are new to AWS security can deploy this pack to immediately gain visibility into their most critical exposures without needing deep security expertise.
- **Threat-informed**: Rules are organized by threat-oriented category rather than by AWS service, helping customers understand *why* a misconfiguration matters in terms of what an attacker would do with it.
- **Dashboard integration**: This conformance pack can optionally be visualized in the [AWS Config Resource Compliance Dashboard (CRCD)](https://docs.aws.amazon.com/guidance/latest/cloud-intelligence-dashboards/config-resource-compliance-dashboard.html), which provides a QuickSight-based view of compliance status classified by threat-technique categories.

**Note:** Resolving these misconfigurations significantly reduces your attack surface, but does not guarantee complete protection against security incidents. Additional security controls, monitoring, and practices are recommended as part of a comprehensive security strategy.


## Prerequisites

- **AWS Config** must be enabled in all accounts and Regions where you deploy this conformance pack. This template supports both single-account deployment (`put-conformance-pack`) and organization-wide deployment (`put-organization-conformance-pack`).
- **AWS Config recorder** must record the resource types evaluated by the rules in this pack. The base template requires: `AWS::S3::Bucket`, `AWS::S3::AccessPoint`, `AWS::EC2::Instance`, `AWS::EC2::SecurityGroup`, `AWS::EC2::LaunchTemplate`, `AWS::AutoScaling::LaunchConfiguration`. The extended template additionally requires `AWS::IAM::User` to be recorded (in at least one Region) for the IAM MFA rules (`IAM_USER_MFA_ENABLED`, `MFA_ENABLED_FOR_IAM_CONSOLE_ACCESS`) to produce per-user compliance results.
- **Extended version only**: Deploy the prerequisites CloudFormation template (`sire-conformance-pack-prerequisites.yaml`) first to create the required Lambda functions. See [Extended Version](#extended-version) below.


## Rules


### Naming Convention

All rules follow the format: `sire-<lv1>-<lv2>-<rule-name>`

| Component | Description | Examples |
|-----------|-------------|----------|
| `sire-` | Fixed prefix for the conformance pack rules, stands for "Security Incident Response Engineering" | - |
| `lv1` | Level 1 classification (threat-oriented category, related to the attack tactics) | `ia`, `p`, `pe` |
| `lv2` | Level 2 classification (protection domain) | `s3`, `iam`, `ec2` |
| `rule-name` | Descriptive rule name in kebab-case | `root-account-mfa-enabled` |

The level names below borrow terminology from MITRE ATT&CK and the Threat Technique Catalog for AWS to make the intent of each grouping recognizable. They are organizational labels for this pack, not a formal classification against those frameworks.

#### Level 1 Classification (Threat-Oriented Categories)

This version of the conformance pack is called Fundamental because it covers the Initial Access grouping only.

| Abbreviation | Name | Description |
|--------------|------|-------------|
| `ia` | Initial Access | Techniques used to gain initial access to AWS environments |
| `ex` | Execution | Techniques that result in adversary-controlled code running on AWS resources |
| `p` | Persistence | Techniques used to maintain access to AWS environments |
| `pe` | Privilege Escalation | Techniques used to gain higher-level permissions in AWS |
| `da` | Defense Evasion | Techniques used to avoid detection in AWS environments |
| `ca` | Credential Access | Techniques used to steal AWS credentials |
| `d` | Discovery | Techniques used to gain knowledge about AWS environments |
| `lm` | Lateral Movement | Techniques used to enter and control remote AWS accounts and services |
| `c` | Collection | Techniques used to gather data from AWS resources |
| `e` | Exfiltration | Techniques used to steal data from AWS environments |
| `i` | Impact | Techniques used to disrupt availability or compromise integrity |
| `rd` | Resource Development | Techniques used to develop new resources for AWS targeting |

#### Level 2 Classification (Protection Domains)

| Abbreviation | Name | Description |
|--------------|------|-------------|
| `s3` | S3 Protection | Security controls for Amazon S3 buckets and objects |
| `iam` | IAM Protection | Identity and Access Management security controls |
| `ec2` | EC2 Protection | Elastic Compute Cloud security controls |
| `ra` | Resource Access Protection | Security controls for VPC firewalls |
| `vpc` | VPC Security | Virtual Private Cloud network security controls |
| `kms` | KMS Encryption | Key Management Service encryption controls |
| `rds` | RDS Security | Relational Database Service security controls |
| `lambda` | Lambda Security | AWS Lambda function security controls |
| `va` | Valid Accounts | Account access and authentication controls |
| `api` | API Security | API Gateway and API access controls |
| `ct` | CloudTrail Logging | CloudTrail audit logging controls |
| `cfg` | Config Monitoring | AWS Config monitoring and compliance controls |
| `ebs` | EBS Security | Elastic Block Store security controls |
| `sm` | Secrets Management | Secrets Manager and credential protection controls |




### Rules: Initial Access — S3 Protection

These rules detect S3 misconfigurations that could allow unauthorized access to data.

| Rule Name | AWS Config Managed Rule | Description |
|-----------|------------------------|-------------|
| `sire-ia-s3-s3-bucket-public-read-prohibited` | [S3_BUCKET_PUBLIC_READ_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-public-read-prohibited.html) | Checks that S3 buckets do not allow public read access. Public read access can expose sensitive data to the internet. |
| `sire-ia-s3-s3-bucket-public-write-prohibited` | [S3_BUCKET_PUBLIC_WRITE_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-public-write-prohibited.html) | Checks that S3 buckets do not allow public write access. Public write access can allow attackers to modify or plant malicious content. |
| `sire-ia-s3-s3-access-point-in-vpc-only` | [S3_ACCESS_POINT_IN_VPC_ONLY](https://docs.aws.amazon.com/config/latest/developerguide/s3-access-point-in-vpc-only.html) | Checks whether S3 access points are configured to only allow access from within a VPC, preventing internet-based access. |
| `sire-ia-s3-s3-access-point-public-access-blocks` | [S3_ACCESS_POINT_PUBLIC_ACCESS_BLOCKS](https://docs.aws.amazon.com/config/latest/developerguide/s3-access-point-public-access-blocks.html) | Checks whether S3 access points have public access block settings enabled. |
| `sire-ia-s3-s3-account-level-public-access-blocks-periodic` | [S3_ACCOUNT_LEVEL_PUBLIC_ACCESS_BLOCKS_PERIODIC](https://docs.aws.amazon.com/config/latest/developerguide/s3-account-level-public-access-blocks-periodic.html) | Periodically checks whether S3 account-level public access block settings remain enabled. Account-level blocks provide a safety net against bucket-level misconfigurations. |
| `sire-ia-s3-s3-bucket-level-public-access-prohibited` | [S3_BUCKET_LEVEL_PUBLIC_ACCESS_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-level-public-access-prohibited.html) | Checks whether individual S3 buckets have public access blocked at the bucket level. |

### Rules: Initial Access — EC2 Security

These rules detect EC2 instances vulnerable to Server-Side Request Forgery (SSRF) attacks through the Instance Metadata Service.

| Rule Name | AWS Config Managed Rule | Description |
|-----------|------------------------|-------------|
| `sire-ia-ec2-autoscaling-launchconfig-requires-imdsv2` | [AUTOSCALING_LAUNCHCONFIG_REQUIRES_IMDSV2](https://docs.aws.amazon.com/config/latest/developerguide/autoscaling-launchconfig-requires-imdsv2.html) | Checks whether Auto Scaling launch configurations require IMDSv2. IMDSv1 is vulnerable to SSRF attacks that can steal instance credentials. |
| `sire-ia-ec2-ec2-imdsv2-check` | [EC2_IMDSV2_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/ec2-imdsv2-check.html) | Checks whether running EC2 instances are configured to require IMDSv2. |
| `sire-ia-ec2-ec2-launch-template-imdsv2-check` | [EC2_LAUNCH_TEMPLATE_IMDSV2_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/ec2-launch-template-imdsv2-check.html) | Checks whether EC2 launch templates are configured to require IMDSv2 for new instances. |

### Rules: Initial Access — Resource Access Protection

These rules detect overly permissive network configurations that could allow unauthorized network access.

| Rule Name | AWS Config Managed Rule | Description |
|-----------|------------------------|-------------|
| `sire-ia-ra-vpc-sg-port-restriction-check` | [VPC_SG_PORT_RESTRICTION_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/vpc-sg-port-restriction-check.html) | Checks whether security groups allow unrestricted inbound traffic on specified ports. Open SSH (22) and RDP (3389) ports are commonly exploited for unauthorized access. |


### Rules: Extended Version (Initial Access — IAM Protection)
The extended version includes all rules from the base template and adds IAM protection rules that detect identity-based misconfigurations commonly exploited for initial access.

| Rule Name | AWS Config Managed Rule | Description |
|-----------|------------------------|-------------|
| `sire-ia-iam-root-account-mfa-enabled` | [ROOT_ACCOUNT_MFA_ENABLED](https://docs.aws.amazon.com/config/latest/developerguide/root-account-mfa-enabled.html) | Checks if the root user has MFA enabled for console sign-in. A root account without MFA is a critical exposure. |
| `sire-ia-iam-iam-root-access-key-check` | [IAM_ROOT_ACCESS_KEY_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/iam-root-access-key-check.html) | Checks whether root user access keys exist. Root access keys provide unrestricted access and should be deleted. |
| `sire-ia-iam-iam-user-mfa-enabled` | [IAM_USER_MFA_ENABLED](https://docs.aws.amazon.com/config/latest/developerguide/iam-user-mfa-enabled.html) | Checks if IAM users have MFA enabled. Users without MFA are vulnerable to credential theft. |
| `sire-ia-iam-mfa-enabled-for-iam-console-access` | [MFA_ENABLED_FOR_IAM_CONSOLE_ACCESS](https://docs.aws.amazon.com/config/latest/developerguide/mfa-enabled-for-iam-console-access.html) | Checks if MFA is enabled for all IAM users with console passwords. |

### Rules: Extended Version Custom Lambda Rules (Initial Access — IAM Protection)

| Rule Name | Description |
|-----------|-------------|
| `sire-ia-iam-iam-root-not-used-regularly` | Checks whether the root user has been used within a configurable threshold (default: 5 days). Root usage is a strong indicator of either compromise or poor operational practice. |
| `sire-ia-iam-iam-user-access-key-check` | Checks whether IAM users have active access keys. Access keys are long-lived credentials that are high-value targets for attackers. |


## Input Parameters

All parameters are optional unless marked otherwise. Default values are provided for a security-first posture.

**Note on data types:** In the CloudFormation templates every parameter is declared as `Type: String`, so all values — including booleans and integers — must be supplied as strings (for example `true`, not the unquoted boolean, and `5`, not the unquoted number). The **Type** column below describes the *logical* type and accepted format.

### S3 Protection Parameters

| Parameter | Type | Default | Example | Description |
|-----------|------|---------|---------|-------------|
| `S3BucketLevelPublicAccessProhibitedExcludedPublicBuckets` | Comma-separated list of bucket names | _(empty)_ | `my-public-site,shared-logs-bucket` | Known allowed public S3 bucket names to exclude from evaluation. |
| `S3AccessPointPublicAccessBlocksExcludedAccessPoints` | Comma-separated list of access point names | _(empty)_ | `my-access-point,vpc-access-point` | S3 access point names to exclude from public access evaluation. |
| `S3AccountLevelPublicAccessIgnorePublicAcls` | Boolean (`true` / `false`) | `true` | `false` | Whether to enforce the `IgnorePublicAcls` setting at the account level. |
| `S3AccountLevelPublicAccessBlockPublicPolicy` | Boolean (`true` / `false`) | `true` | `false` | Whether to enforce the `BlockPublicPolicy` setting at the account level. |
| `S3AccountLevelPublicAccessBlockPublicAcls` | Boolean (`true` / `false`) | `true` | `false` | Whether to enforce the `BlockPublicAcls` setting at the account level. |
| `S3AccountLevelPublicAccessRestrictPublicBuckets` | Boolean (`true` / `false`) | `true` | `false` | Whether to enforce the `RestrictPublicBuckets` setting at the account level. |

### Resource Access Protection Parameters

| Parameter | Type | Default | Example | Description |
|-----------|------|---------|---------|-------------|
| `VPCSecurityGroupPortRestrictionRestrictedPorts` | Comma-separated list of port numbers | `22,3389` | `22,3389,23` | Ports that should not be open to unrestricted inbound traffic (0.0.0.0/0 or ::/0). |
| `VPCSecurityGroupPortRestrictionProtocolType` | Enum: `TCP` \| `UDP` \| `ALL` | `ALL` | `TCP` | Protocol type to evaluate. |
| `VPCSecurityGroupPortRestrictionExcludeExternalSecurityGroups` | Boolean (`true` / `false`) | `true` | `false` | Whether to exclude external security groups from evaluation. |
| `VPCSecurityGroupPortRestrictionIpType` | Enum: `IPv4` \| `IPv6` \| `ALL` | `ALL` | `IPv4` | IP version to evaluate. |

### Extended Version Parameters

In addition to the base parameters, the extended version requires:

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| `RootNotUsedRegularlyLambdaArn` | Lambda function ARN | Yes | `arn:aws:lambda:us-east-1:111122223333:function:sire-root-not-used-regularly` | ARN of the Lambda function for the root usage check. Obtained from the prerequisites template output. |
| `UserAccessKeyCheckLambdaArn` | Lambda function ARN | Yes | `arn:aws:lambda:us-east-1:111122223333:function:sire-user-access-key-check` | ARN of the Lambda function for the access key check. Obtained from the prerequisites template output. |
| `RootUsageThresholdDays` | Integer (as string) | No (default: `5`) | `7` | Number of days to look back for root account usage. If root was used within this threshold, the account is marked NON_COMPLIANT. |

### Rule-to-Parameter Mapping

Only the rules listed below consume input parameters; all other rules in the pack take no parameters.

| Rule | Parameters consumed |
|------|---------------------|
| `sire-ia-s3-s3-bucket-level-public-access-prohibited` | `S3BucketLevelPublicAccessProhibitedExcludedPublicBuckets` |
| `sire-ia-s3-s3-access-point-public-access-blocks` | `S3AccessPointPublicAccessBlocksExcludedAccessPoints` |
| `sire-ia-s3-s3-account-level-public-access-blocks-periodic` | `S3AccountLevelPublicAccessIgnorePublicAcls`, `S3AccountLevelPublicAccessBlockPublicPolicy`, `S3AccountLevelPublicAccessBlockPublicAcls`, `S3AccountLevelPublicAccessRestrictPublicBuckets` |
| `sire-ia-ra-vpc-sg-port-restriction-check` | `VPCSecurityGroupPortRestrictionRestrictedPorts`, `VPCSecurityGroupPortRestrictionProtocolType`, `VPCSecurityGroupPortRestrictionExcludeExternalSecurityGroups`, `VPCSecurityGroupPortRestrictionIpType` |
| `sire-ia-iam-iam-root-not-used-regularly` (extended) | `RootNotUsedRegularlyLambdaArn`, `RootUsageThresholdDays` |
| `sire-ia-iam-iam-user-access-key-check` (extended) | `UserAccessKeyCheckLambdaArn` |


## Remediation

**This conformance pack is detection-only.** It ships no `RemediationConfiguration` blocks — the rules evaluate resources and report compliance, but they do not modify any resource. Nothing in this pack changes your environment automatically.

You have two ways to fix a resource that a rule reports as `NON_COMPLIANT`:

1. **Manual remediation** — make the corrective configuration change yourself (steps per rule below).
2. **Automatic remediation (optional, self-configured)** — for the subset of rules that have an AWS-provided [Systems Manager Automation remediation runbook](https://docs.aws.amazon.com/config/latest/developerguide/remediation.html), you can attach a `RemediationConfiguration` to the deployed rule (via the AWS Config console or `put-remediation-configurations`) to remediate manually or automatically. These runbooks are **not** included or pre-wired by this pack; you opt in and take on the associated IAM permissions and operational risk. See [Remediating Noncompliant Resources](https://docs.aws.amazon.com/config/latest/developerguide/remediation.html).

The table below lists the manual fix for each rule and, where one exists, the AWS-provided remediation runbook you could attach.

### S3 Protection

| Rule | Manual remediation | AWS remediation runbook |
|------|--------------------|-------------------------|
| `sire-ia-s3-s3-bucket-public-read-prohibited` | Remove public read grants from the bucket ACL and policy, and enable S3 Block Public Access on the bucket. | `AWS-DisableS3BucketPublicReadWrite` |
| `sire-ia-s3-s3-bucket-public-write-prohibited` | Remove public write grants from the bucket ACL and policy, and enable S3 Block Public Access on the bucket. | `AWS-DisableS3BucketPublicReadWrite` |
| `sire-ia-s3-s3-bucket-level-public-access-prohibited` | Enable all four Block Public Access settings on the bucket. | `AWSConfigRemediation-ConfigureS3BucketPublicAccessBlock` |
| `sire-ia-s3-s3-account-level-public-access-blocks-periodic` | Enable the account-level Block Public Access settings for the account. | `AWSConfigRemediation-ConfigureS3PublicAccessBlock` |
| `sire-ia-s3-s3-access-point-in-vpc-only` | Recreate the access point with a VPC network origin, or restrict it to a VPC. Access point network origin is immutable, so the access point must be replaced. | _None — manual only_ |
| `sire-ia-s3-s3-access-point-public-access-blocks` | Enable Block Public Access settings on the access point. | _None — manual only_ |

### EC2 Security (IMDSv2)

| Rule | Manual remediation | AWS remediation runbook |
|------|--------------------|-------------------------|
| `sire-ia-ec2-ec2-imdsv2-check` | Set the instance metadata options to require IMDSv2 (`HttpTokens=required`) using `modify-instance-metadata-options`. | `AWSConfigRemediation-EnforceEC2InstanceIMDSv2` |
| `sire-ia-ec2-ec2-launch-template-imdsv2-check` | Create a new launch template version with `MetadataOptions.HttpTokens=required` and set it as the default version. | _None — manual only_ |
| `sire-ia-ec2-autoscaling-launchconfig-requires-imdsv2` | Launch configurations are immutable. Create a replacement launch configuration (or migrate to a launch template) with `HttpTokens=required`, then update the Auto Scaling group to use it. | _None — manual only_ |

### Resource Access Protection (Security Groups)

| Rule | Manual remediation | AWS remediation runbook |
|------|--------------------|-------------------------|
| `sire-ia-ra-vpc-sg-port-restriction-check` | Edit the security group to remove or narrow the offending inbound rule so the restricted ports (default `22`, `3389`) are not open to `0.0.0.0/0` or `::/0`. Scope the source to specific CIDRs or security groups. | _None designated for this rule — manual only_ |

### IAM Protection (extended template)

| Rule | Manual remediation | AWS remediation runbook |
|------|--------------------|-------------------------|
| `sire-ia-iam-root-account-mfa-enabled` | Sign in as the root user and enable an MFA device for the root account. | _None — manual only_ |
| `sire-ia-iam-iam-root-access-key-check` | Sign in as the root user and delete the root access key(s). Root should not have access keys. | _None — manual only_ |
| `sire-ia-iam-iam-user-mfa-enabled` | Assign an MFA device to each IAM user flagged. | _None — manual only_ |
| `sire-ia-iam-mfa-enabled-for-iam-console-access` | Assign an MFA device to each IAM user that has a console password. | _None — manual only_ |
| `sire-ia-iam-iam-root-not-used-regularly` (custom) | Investigate why the root user was used within the threshold window. If the usage was not expected, treat it as a potential compromise and follow your incident response process (rotate root credentials, review CloudTrail). If it was legitimate, migrate the task to an IAM principal so root is not used routinely. | _None — manual only_ |
| `sire-ia-iam-iam-user-access-key-check` (custom) | Review each flagged IAM user's active access keys. Remove keys that are unnecessary, and for keys that are required, rotate them and prefer short-lived credentials (IAM roles) where possible. | _None — manual only_ |


## Regional Availability

Some AWS Config managed rules are not available in all AWS Regions. Before deploying this conformance pack, verify that the rules are supported in your target Region by consulting the [AWS Config Managed Rules by Region Availability](https://docs.aws.amazon.com/config/latest/developerguide/managing-rules-by-region-availability.html) page.

If you deploy this conformance pack in a Region where a rule is not available, the deployment will fail. Remove unsupported rules from the template before deploying in those Regions.


## Deployment

This conformance pack is provided as two templates: a base template and an extended template. The recommended deployment strategy for multi-region environments is to deploy the **extended template in a single primary region** and the **base template in all other regions**. This is because IAM resources are global — deploying the custom Lambda rules and IAM managed rules in every region would produce redundant evaluations at unnecessary cost. Regional resources (S3 buckets, EC2 instances, security groups) are checked by the base template in each region where they exist.

### Single Account Deployment

#### Step 1: Deploy prerequisites in the primary region

Deploy the prerequisites CloudFormation template to create the Lambda functions and IAM roles needed by the extended template:

```
aws cloudformation deploy \
  --template-file sire-conformance-pack-prerequisites.yaml \
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

#### Step 2: Deploy the extended template in the primary region

Deploy the extended conformance pack (all rules including IAM + custom Lambda) in the primary region:

```
aws configservice put-conformance-pack \
  --conformance-pack-name Security-Best-Practices-for-Incident-Response-Fundamental \
  --template-body file://sire-conformance-pack-template-extended.yaml \
  --conformance-pack-input-parameters \
    ParameterName=RootNotUsedRegularlyLambdaArn,ParameterValue=<ARN_FROM_STEP_1> \
    ParameterName=UserAccessKeyCheckLambdaArn,ParameterValue=<ARN_FROM_STEP_1> \
  --region <PRIMARY_REGION>
```

#### Step 3: Deploy the base template in all other regions

Deploy the base conformance pack (managed rules only, no Lambda prerequisites) in every other region where AWS Config is enabled:

```
REGIONS="us-east-2 us-west-2 eu-west-1 eu-central-1 ap-southeast-1 ap-northeast-1"

for REGION in $REGIONS; do
  echo "Deploying base conformance pack in $REGION..."
  aws configservice put-conformance-pack \
    --conformance-pack-name Security-Best-Practices-for-Incident-Response-Fundamental \
    --template-body file://sire-conformance-pack-template.yaml \
    --region $REGION
done
```

Alternatively, the base template can be deployed from the AWS Config console by selecting it from the conformance pack dropdown in each region.

### Organization-Wide Deployment

This section describes how to deploy the conformance pack across all accounts in an AWS Organization.

The deployment is split into three steps:

- **Step 1 — Delegated administrator account (once):** deploy the prerequisite
  Lambda functions to every member account (primary Region only) using a
  service-managed CloudFormation StackSet.
- **Step 2 — Delegated administrator account (once):** deploy the **base** conformance
  pack to all non-primary Regions organization-wide.
- **Step 3 — Each member account (repeat):** deploy the **extended** conformance
  pack in the primary Region of each account, pointing it at that account's own
  prerequisite Lambda functions.

> **Why the extended pack is deployed per account.** The extended pack's two
> custom rules invoke account-local Lambda functions. Each function's ARN
> contains its own account ID, and the functions only allow invocation from the
> account they live in (`SourceAccount: !Ref AWS::AccountId` in the prerequisites
> template). A single organization-level `put-organization-conformance-pack`
> call can only pass one Lambda ARN to every account, so it cannot work for the
> extended pack. The base pack has no Lambda dependency and *is* deployed
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
  --template-body file://sire-conformance-pack-prerequisites.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --permission-model SERVICE_MANAGED \
  --auto-deployment Enabled=true,RetainStacksOnAccountRemoval=false \
  --parameters ParameterKey=RootUsageThresholdDays,ParameterValue=5 \
  --call-as DELEGATED_ADMIN \
  --region "$PRIMARY_REGION"
```


- **Root usage threshold**: to change the default (`5` days) for the `sire-ia-iam-iam-root-not-used-regularly` rule, edit the `--parameters` argument to the command above.
- `--call-as DELEGATED_ADMIN` - Use it if you run the command run from
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
extended pack in Step 3):

```
OTHER_REGIONS="us-east-2 us-west-2 eu-west-1 eu-central-1 ap-southeast-1 ap-northeast-1"

for REGION in $OTHER_REGIONS; do
  echo "Deploying base conformance pack in $REGION..."
  aws configservice put-organization-conformance-pack \
    --organization-conformance-pack-name Security-Best-Practices-for-Incident-Response-Fundamental \
    --template-body file://sire-conformance-pack-template.yaml \
    --region $REGION
done
```

- To skip specific accounts (for example, where AWS Config is not enabled), add
  `--excluded-accounts <ACCOUNT_IDS>` to the command.

---

#### Step 3: In each member account (primary Region)

> **Before you begin, confirm Step 2 finished.** The base pack deploys
> asynchronously — the ARNs returned in Step 2 mean "accepted", not "complete".
> From the delegated administrator (or management) account, verify that every
> account reports `CREATE_SUCCESSFUL` before proceeding:
>
> ```
> PRIMARY_REGION=<PRIMARY_REGION>
> aws configservice get-organization-conformance-pack-detailed-status \
>   --organization-conformance-pack-name Security-Best-Practices-for-Incident-Response-Fundamental \
>   --region "$PRIMARY_REGION"
> ```
>
> Every entry in the output must show `Status: CREATE_SUCCESSFUL`. If any account
> is still `CREATE_IN_PROGRESS`, wait and re-run the command. If any account is
> `CREATE_FAILED`, check its `ErrorMessage` (a common cause is AWS Config not
> being enabled in that account/Region) and resolve it before continuing.

Repeat this step in every member account that should run the extended pack, including the delegated administrator account. Log into the account and open AWS CloudShell in the primary Region (or use any authenticated AWS CLI session for that account).

The snippet below resolves that account's own Lambda ARNs by their fixed
function names and deploys the extended conformance pack in one shot — no manual
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
  --conformance-pack-name Security-Best-Practices-for-Incident-Response-Fundamental \
  --template-body file://sire-conformance-pack-template-extended.yaml \
  --conformance-pack-input-parameters \
    ParameterName=RootNotUsedRegularlyLambdaArn,ParameterValue="$ROOT_ARN" \
    ParameterName=UserAccessKeyCheckLambdaArn,ParameterValue="$KEY_ARN" \
  --region "$PRIMARY_REGION"
```

Because each account resolves its own ARNs at deploy time, every account gets an
extended pack wired to its own local Lambda functions.


### Base-Only Deployment (Fallback)

If you only want the base managed rules without the IAM custom Lambda rules, you can deploy the base template in all regions without prerequisites:

```
aws configservice put-conformance-pack \
  --conformance-pack-name Security-Best-Practices-for-Incident-Response-Fundamental \
  --template-body file://sire-conformance-pack-template.yaml \
  --region <REGION>
```

The base template can also be deployed from the AWS Config console by selecting it from the conformance pack dropdown.


## FAQ

**Q: What is the difference between the base and extended versions?**

The base template (`sire-conformance-pack-template.yaml`) contains only AWS Config managed rules and can be deployed directly from the AWS Config console dropdown with no prerequisites. The extended template (`sire-conformance-pack-template-extended.yaml`) adds IAM protection rules — including two custom Lambda-based rules — and requires deploying the prerequisites template first.

| Version | File | Rules | Prerequisites | Console Dropdown |
|---------|------|-------|---------------|-----------------|
| Base | `sire-conformance-pack-template.yaml` | 10 managed rules | None | Yes |
| Extended | `sire-conformance-pack-template-extended.yaml` | 14 managed + 2 custom rules | Lambda functions via `sire-conformance-pack-prerequisites.yaml` | No (download only) |

The recommended multi-region deployment uses both templates together: deploy the extended template in a single primary region (for full IAM coverage including custom Lambda rules), and the base template in all other regions (for regional resource checks). This avoids running IAM evaluations redundantly in every region, since IAM resources are global.

| Region | Template | What it covers |
|--------|----------|----------------|
| Primary (e.g., us-east-1) | Extended | S3, EC2, Security Groups + IAM managed rules + custom Lambda rules |
| All other regions | Base | S3, EC2, Security Groups |

In a multi-account setup (AWS Organizations), this recommendation applies to every account: deploy the extended template in one primary region per account, and the base template in all other regions of that account.

**Q: How is this pack different from other published conformance packs?**

Other conformance packs are organized by compliance framework (NIST, PCI, CIS) or AWS service (S3, EC2). They are comprehensive — often containing 50 to 100+ rules — and are designed for customers who need to demonstrate compliance with a specific standard. This pack takes a different approach: it is curated by AWS Security Incident Response engineers based on the misconfigurations they see most frequently exploited in real attacks. It is intentionally small, making it cost-effective and accessible to customers who are beginning their security journey on AWS. Rather than covering every possible check, it focuses on the specific vulnerabilities that threat actors target most often to gain initial access.

**Q: I already have other conformance packs deployed. Should I still use this one?**

If you already have a comprehensive conformance pack (e.g., CIS, NIST), the rules in this pack are likely already covered. This pack is most valuable for customers who have no conformance packs deployed and want a low-cost starting point with the highest security impact.

**Q: Why do rule names have the `sire-` prefix?**

The rule naming convention (`sire-ia-{category}-{rule}`) encodes a threat-oriented category, which enables grouping and visualization on security dashboards. The prefix `sire` stands for **S**ecurity **I**ncident **R**esponse **E**ngineering. `ia` corresponds to "Initial Access" from MITRE ATT&CK; it indicates the intent behind the grouping rather than a formal mapping to the ATT&CK framework.

**Q: Can I deploy this pack alongside other conformance packs?**

Yes. Conformance packs are independent and can coexist. A resource may be evaluated by rules in multiple conformance packs simultaneously.

**Q: What happens if a rule in this pack evaluates the same resource as a rule I already have?**

Both evaluations will appear in AWS Config. The conformance pack rules are immutable — they cannot be modified outside the conformance pack API — so there is no conflict with existing rules.


## References

- [Threat Technique Catalog for AWS](https://aws-samples.github.io/threat-technique-catalog-for-aws/)
- [MITRE ATT&CK® Framework](https://attack.mitre.org/)
- [AWS Security Incident Response](https://aws.amazon.com/security-incident-response/)
- [AWS Config Managed Rules](https://docs.aws.amazon.com/config/latest/developerguide/managed-rules-by-aws-config.html)
- [AWS Config Conformance Packs](https://docs.aws.amazon.com/config/latest/developerguide/conformance-packs.html)
- [AWS Config Managed Rules by Region Availability](https://docs.aws.amazon.com/config/latest/developerguide/managing-rules-by-region-availability.html)
