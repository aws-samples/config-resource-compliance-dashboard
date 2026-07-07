# Security Best Practices for Security Incident Response Engineering Team (Fundamental)

## Purpose

This conformance pack contains a focused set of AWS Config rules recommended by [AWS Security Incident Response](https://aws.amazon.com/security-incident-response/) security engineers. These rules target the most common misconfigurations that security engineers observe causing real security incidents in customer environments.

Unlike larger conformance packs that may contain 50+ rules mapped to a compliance framework, this pack is intentionally small and focused. It is designed for customers who are new to AWS Config and security monitoring and want to start with the highest-impact checks without the cost and complexity of deploying dozens of rules. Additionally, any customer can deploy this conformance pack to perform fundamental security posture checks on their AWS environment, regardless of their experience level. Each rule in this pack addresses a specific misconfiguration that is known to be actively exploited by threat actors.

The rules are classified according to the [Threat Technique Catalog for AWS](https://aws-samples.github.io/threat-technique-catalog-for-aws/), which is based on [MITRE ATT&CK®](https://attack.mitre.org/). The catalog identifies and categorizes threat actor behaviors observed by AWS.

### Why this pack

- **Curated by incident responders**: Rules are selected based on multi-year experience supporting AWS customers during active security incidents — not from a theoretical compliance checklist.
- **Low cost, high impact**: A small number of rules keeps AWS Config costs low while covering the misconfigurations most frequently exploited in real attacks.
- **Accessible to beginners**: Customers who are new to AWS security can deploy this pack to immediately gain visibility into their most critical exposures without needing deep security expertise.
- **Threat-informed**: Rules are organized by attack technique rather than AWS service, helping customers understand *why* a misconfiguration matters in terms of what an attacker would do with it.
- **Dashboard integration**: This conformance pack can optionally be visualized in the [AWS Config Resource Compliance Dashboard (CRCD)](https://docs.aws.amazon.com/guidance/latest/cloud-intelligence-dashboards/config-resource-compliance-dashboard.html), which provides a QuickSight-based view of compliance status classified by threat technique.

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
| `lv1` | Level 1 classification (attack tactic) | `ia`, `p`, `pe` |
| `lv2` | Level 2 classification (protection domain) | `s3`, `iam`, `ec2` |
| `rule-name` | Descriptive rule name in kebab-case | `root-account-mfa-enabled` |

#### Level 1 Classification (Attack Tactics)

This version of the conformance pack is called Fundamental because it covers Initial Access classification only.

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

All parameters are optional. Default values are provided for a security-first posture.

### S3 Protection Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `S3BucketLevelPublicAccessProhibitedExcludedPublicBuckets` | _(empty)_ | Comma-separated list of known allowed public S3 bucket names to exclude from evaluation. |
| `S3AccessPointPublicAccessBlocksExcludedAccessPoints` | _(empty)_ | Comma-separated list of S3 access point names to exclude from public access evaluation. |
| `S3AccountLevelPublicAccessIgnorePublicAcls` | `true` | Whether to enforce the `IgnorePublicAcls` setting at the account level. |
| `S3AccountLevelPublicAccessBlockPublicPolicy` | `true` | Whether to enforce the `BlockPublicPolicy` setting at the account level. |
| `S3AccountLevelPublicAccessBlockPublicAcls` | `true` | Whether to enforce the `BlockPublicAcls` setting at the account level. |
| `S3AccountLevelPublicAccessRestrictPublicBuckets` | `true` | Whether to enforce the `RestrictPublicBuckets` setting at the account level. |

### Resource Access Protection Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `VPCSecurityGroupPortRestrictionRestrictedPorts` | `22,3389` | Comma-separated list of ports that should not be open to unrestricted inbound traffic (0.0.0.0/0 or ::/0). |
| `VPCSecurityGroupPortRestrictionProtocolType` | `ALL` | Protocol type to evaluate. Valid values: `TCP`, `UDP`, `ALL`. |
| `VPCSecurityGroupPortRestrictionExcludeExternalSecurityGroups` | `true` | Whether to exclude external security groups from evaluation. |
| `VPCSecurityGroupPortRestrictionIpType` | `ALL` | IP version to evaluate. Valid values: `IPv4`, `IPv6`, `ALL`. |

### Extended Version Parameters

In addition to the base parameters, the extended version requires:

| Parameter | Required | Description |
|-----------|----------|-------------|
| `RootNotUsedRegularlyLambdaArn` | Yes | ARN of the Lambda function for the root usage check. Obtained from the prerequisites template output. |
| `UserAccessKeyCheckLambdaArn` | Yes | ARN of the Lambda function for the access key check. Obtained from the prerequisites template output. |
| `RootUsageThresholdDays` | No (default: `5`) | Number of days to look back for root account usage. If root was used within this threshold, the account is marked NON_COMPLIANT. |


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

#### Step 1: Deploy prerequisites in the primary region (all accounts)

Deploy the prerequisites CloudFormation template using StackSets to create the Lambda functions and IAM roles in every member account, but only in the primary region:

```
aws cloudformation deploy \
  --template-file sire-conformance-pack-prerequisites.yaml \
  --stack-name sire-conformance-pack-prerequisites \
  --capabilities CAPABILITY_NAMED_IAM \
  --region <PRIMARY_REGION>
```

Use CloudFormation StackSets to deploy the prerequisites across all member accounts in the primary region.

#### Step 2: Deploy the extended template in the primary region (all accounts)

Deploy the extended conformance pack across the organization in the primary region only:

```
aws configservice put-organization-conformance-pack \
  --organization-conformance-pack-name Security-Best-Practices-for-Incident-Response-Fundamental \
  --template-body file://sire-conformance-pack-template-extended.yaml \
  --conformance-pack-input-parameters \
    ParameterName=RootNotUsedRegularlyLambdaArn,ParameterValue=<ARN_FROM_STEP_1> \
    ParameterName=UserAccessKeyCheckLambdaArn,ParameterValue=<ARN_FROM_STEP_1>
```

Note: Organization conformance packs deploy to all accounts but you control the region by running the command from the primary region.

#### Step 3: Deploy the base template in all other regions (all accounts)

Deploy the base conformance pack across the organization in every other region where AWS Config is enabled:

```
REGIONS="us-east-2 us-west-2 eu-west-1 eu-central-1 ap-southeast-1 ap-northeast-1"

for REGION in $REGIONS; do
  echo "Deploying base conformance pack in $REGION..."
  aws configservice put-organization-conformance-pack \
    --organization-conformance-pack-name Security-Best-Practices-for-Incident-Response-Fundamental \
    --template-body file://sire-conformance-pack-template.yaml \
    --region $REGION
done
```

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

The rule naming convention (`sire-ia-{category}-{rule}`) encodes the threat tactic and category, enabling automated classification and visualization on security dashboards. The prefix `sire` stands for **S**ecurity **I**ncident **R**esponse **E**ngineering. `ia` refers to the MITRE ATT&CK tactic "Initial Access."

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
