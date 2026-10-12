# Conformance Pack Specification

This document describes the AWS Config rules included in the Threat-Informed Security Best Practices (Fundamental) conformance pack, built in collaboration with Security Incident Response security engineers. The rules are based on the [Threat Technique Catalog for AWS](https://aws-samples.github.io/threat-technique-catalog-for-aws/) (MITRE ATT&CK® framework).

## Naming Convention

All rules follow the format: `sire-<lv1>-<lv2>-<rule-name>`

| Component | Description | Examples |
|-----------|-------------|----------|
| `sire-` | Fixed prefix for the conformance pack rules, stands for "Security Incident Response Engineering" | - |
| `lv1` | Level 1 classification (attack tactic) | `ia`, `p`, `pe` |
| `lv2` | Level 2 classification (protection domain) | `s3`, `iam`, `ec2` |
| `rule-name` | Descriptive rule name in kebab-case | `root-account-mfa-enabled` |

The `sire-` prefix records that the rules come from the AWS Security Incident Response team. The level names `lv1` and `lv2` borrow terminology from MITRE ATT&CK and the Threat Technique Catalog for AWS to make the intent of each grouping recognizable. They are organizational labels for this pack, not a formal classification against those frameworks.

This version of the conformance pack is called Fundamental because it covers the Initial Access grouping only.

### Level 1 Classification (Attack Tactics)

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

### Level 2 Classification (Protection Domains)

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

## AWS Config Rules

### Initial Access rules

| Rule Name | Description | Type | Source Identifier | Classification | Resource Types |
|-----------|-------------|------|-------------------|----------------|----------------|
| sire-ia-iam-root-account-mfa-enabled | Checks if the root user has MFA enabled for console sign-in. A root account without MFA is a critical exposure. | STANDARD | [ROOT_ACCOUNT_MFA_ENABLED](https://docs.aws.amazon.com/config/latest/developerguide/root-account-mfa-enabled.html) | Initial Access / IAM Protection | Account-level |
| sire-ia-iam-iam-root-access-key-check | Checks whether root user access keys exist. Root access keys provide unrestricted access and should be deleted. | STANDARD | [IAM_ROOT_ACCESS_KEY_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/iam-root-access-key-check.html) | Initial Access / IAM Protection | Account-level |
| sire-ia-iam-iam-root-not-used-regularly | Checks whether the root user has been used within a configurable threshold (default: 5 days). Root usage is a strong indicator of either compromise or poor operational practice. | CUSTOM | Lambda | Initial Access / IAM Protection | Account-level |
| sire-ia-iam-iam-user-access-key-check | Checks whether IAM users have active access keys. Access keys are long-lived credentials that are high-value targets for attackers. | CUSTOM | Lambda | Initial Access / IAM Protection | AWS::IAM::User |
| sire-ia-iam-iam-user-mfa-enabled | Checks if IAM users have MFA enabled. Users without MFA are vulnerable to credential theft. | STANDARD | [IAM_USER_MFA_ENABLED](https://docs.aws.amazon.com/config/latest/developerguide/iam-user-mfa-enabled.html) | Initial Access / IAM Protection | AWS::IAM::User |
| sire-ia-iam-mfa-enabled-for-iam-console-access | Checks if MFA is enabled for all IAM users with console passwords. | STANDARD | [MFA_ENABLED_FOR_IAM_CONSOLE_ACCESS](https://docs.aws.amazon.com/config/latest/developerguide/mfa-enabled-for-iam-console-access.html) | Initial Access / IAM Protection | AWS::IAM::User |
| sire-ia-s3-s3-bucket-public-read-prohibited | Checks that S3 buckets do not allow public read access. Public read access can expose sensitive data to the internet. | STANDARD | [S3_BUCKET_PUBLIC_READ_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-public-read-prohibited.html) | Initial Access / S3 Protection | AWS::S3::Bucket |
| sire-ia-s3-s3-bucket-public-write-prohibited | Checks that S3 buckets do not allow public write access. Public write access can allow attackers to modify or plant malicious content. | STANDARD | [S3_BUCKET_PUBLIC_WRITE_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-public-write-prohibited.html) | Initial Access / S3 Protection | AWS::S3::Bucket |
| sire-ia-ec2-autoscaling-launchconfig-requires-imdsv2 | Checks whether Auto Scaling launch configurations require IMDSv2. IMDSv1 is vulnerable to SSRF attacks that can steal instance credentials. | STANDARD | [AUTOSCALING_LAUNCHCONFIG_REQUIRES_IMDSV2](https://docs.aws.amazon.com/config/latest/developerguide/autoscaling-launchconfig-requires-imdsv2.html) | Initial Access / EC2 Protection | AWS::AutoScaling::LaunchConfiguration |
| sire-ia-ec2-ec2-imdsv2-check | Checks whether running EC2 instances are configured to require IMDSv2. | STANDARD | [EC2_IMDSV2_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/ec2-imdsv2-check.html) | Initial Access / EC2 Protection | AWS::EC2::Instance |
| sire-ia-ec2-ec2-launch-template-imdsv2-check | Checks whether EC2 launch templates are configured to require IMDSv2 for new instances. | STANDARD | [EC2_LAUNCH_TEMPLATE_IMDSV2_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/ec2-launch-template-imdsv2-check.html) | Initial Access / EC2 Protection | AWS::EC2::LaunchTemplate |
| sire-ia-s3-s3-access-point-in-vpc-only | Checks whether S3 access points are configured to only allow access from within a VPC, preventing internet-based access. | STANDARD | [S3_ACCESS_POINT_IN_VPC_ONLY](https://docs.aws.amazon.com/config/latest/developerguide/s3-access-point-in-vpc-only.html) | Initial Access / S3 Protection | AWS::S3::AccessPoint |
| sire-ia-s3-s3-access-point-public-access-blocks | Checks whether S3 access points have public access block settings enabled. | STANDARD | [S3_ACCESS_POINT_PUBLIC_ACCESS_BLOCKS](https://docs.aws.amazon.com/config/latest/developerguide/s3-access-point-public-access-blocks.html) | Initial Access / S3 Protection | AWS::S3::AccessPoint |
| sire-ia-s3-s3-account-level-public-access-blocks-periodic | Periodically checks whether S3 account-level public access block settings remain enabled. Account-level blocks provide a safety net against bucket-level misconfigurations. | STANDARD | [S3_ACCOUNT_LEVEL_PUBLIC_ACCESS_BLOCKS_PERIODIC](https://docs.aws.amazon.com/config/latest/developerguide/s3-account-level-public-access-blocks-periodic.html) | Initial Access / S3 Protection | Account-level |
| sire-ia-s3-s3-bucket-level-public-access-prohibited | Checks whether individual S3 buckets have public access blocked at the bucket level. | STANDARD | [S3_BUCKET_LEVEL_PUBLIC_ACCESS_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-level-public-access-prohibited.html) | Initial Access / S3 Protection | AWS::S3::Bucket |
| sire-ia-ra-vpc-sg-port-restriction-check | Checks whether security groups allow unrestricted inbound traffic on specified ports. Open SSH (22) and RDP (3389) ports are commonly exploited for unauthorized access. | STANDARD | [VPC_SG_PORT_RESTRICTION_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/vpc-sg-port-restriction-check.html) | Initial Access / Resource Access Protection | AWS::EC2::SecurityGroup |

## Input Parameters

All parameters are optional unless marked otherwise. Default values are provided for a security-first posture.

**Note on data types:** In the CloudFormation templates every parameter is declared as `Type: String`, so all values — including booleans and integers — must be supplied as strings (for example `true`, not the unquoted boolean, and `5`, not the unquoted number). The **Type** column below describes the logical type and accepted format.

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

### IAM Protection Parameters

In addition to the base parameters, the complete version requires:

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
| `sire-ia-iam-iam-root-not-used-regularly` | `RootNotUsedRegularlyLambdaArn`, `RootUsageThresholdDays` |
| `sire-ia-iam-iam-user-access-key-check` | `UserAccessKeyCheckLambdaArn` |


## Rule Details

### Initial Access rules

#### IAM Protection Rules
IAM protection rules detect identity-based misconfigurations commonly exploited for initial access.

##### sire-ia-iam-root-account-mfa-enabled
The AWS account root user has unrestricted access to all resources within that account, its usage must be protected by Multi-Factor Authentication (MFA).

##### sire-ia-iam-iam-root-access-key-check
Root access keys provide unrestricted access to all AWS resources and are high-value targets for attackers. Recommendation: do not create root access keys and delete any that exist.

##### sire-ia-iam-iam-root-not-used-regularly (CUSTOM)
Root users have unrestricted access to all AWS resources and are high-value targets for attackers. Recommendation: use this user as little as possible.

##### sire-ia-iam-iam-user-access-key-check (CUSTOM)
Access keys provide unrestricted access to all AWS resources and are high-value targets for attackers. Recommendation: do not create access keys and delete any that exist.

##### sire-ia-iam-iam-user-mfa-enabled / sire-ia-iam-mfa-enabled-for-iam-console-access
Multi-factor authentication provides an additional layer of security against compromised credentials. Enabling MFA significantly reduces the risk of unauthorized access even when passwords are compromised.

#### S3 Protection Rules
These rules detect S3 misconfigurations that could allow unauthorized access to data.

##### sire-ia-s3-s3-bucket-public-read-prohibited
Publicly readable S3 buckets are a common attack vector for initial access and data exposure.

##### sire-ia-s3-s3-bucket-public-write-prohibited
Publicly writable S3 buckets can be exploited for data injection, malware distribution, and resource abuse.

##### sire-ia-s3-s3-access-point-in-vpc-only
S3 access points that allow public internet access increase the attack surface for data exfiltration and unauthorized access. Restricting to VPC-only access ensures data can only be accessed through controlled network paths.

##### sire-ia-s3-s3-access-point-public-access-blocks
Public access block settings on S3 access points provide defense-in-depth protection against accidental public exposure of data.

##### sire-ia-s3-s3-account-level-public-access-blocks-periodic
Continuous monitoring of account-level public access block settings ensures they remain enabled and have not been inadvertently disabled.

##### sire-ia-s3-s3-bucket-level-public-access-prohibited
Bucket-level public access blocks provide defense-in-depth protection against accidental exposure.

#### EC2 Protection Rules
These rules detect EC2 instances vulnerable to Server-Side Request Forgery (SSRF) attacks through the Instance Metadata Service.

##### sire-ia-ec2-autoscaling-launchconfig-requires-imdsv2 / sire-ia-ec2-ec2-imdsv2-check / sire-ia-ec2-ec2-launch-template-imdsv2-check
IMDSv2 provides enhanced security for instance metadata by requiring session-oriented requests, which prevents Server-Side Request Forgery (SSRF) attacks. Enforcing IMDSv2 significantly reduces the risk of credential theft through metadata service exploitation.

#### Resource Access Protection Rules
These rules detect overly permissive network configurations that could allow unauthorized network access.

##### sire-ia-ra-vpc-sg-port-restriction-check
Unrestricted inbound ports enable lateral movement within AWS environments.

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

### IAM Protection

| Rule | Manual remediation | AWS remediation runbook |
|------|--------------------|-------------------------|
| `sire-ia-iam-root-account-mfa-enabled` | Sign in as the root user and enable an MFA device for the root account. | _None — manual only_ |
| `sire-ia-iam-iam-root-access-key-check` | Sign in as the root user and delete the root access key(s). Root should not have access keys. | _None — manual only_ |
| `sire-ia-iam-iam-user-mfa-enabled` | Assign an MFA device to each IAM user flagged. | _None — manual only_ |
| `sire-ia-iam-mfa-enabled-for-iam-console-access` | Assign an MFA device to each IAM user that has a console password. | _None — manual only_ |
| `sire-ia-iam-iam-root-not-used-regularly` (custom) | Investigate why the root user was used within the threshold window. If the usage was not expected, treat it as a potential compromise and follow your incident response process (rotate root credentials, review CloudTrail). If it was legitimate, migrate the task to an IAM principal so root is not used routinely. | _None — manual only_ |
| `sire-ia-iam-iam-user-access-key-check` (custom) | Review each flagged IAM user's active access keys. Remove keys that are unnecessary, and for keys that are required, rotate them and prefer short-lived credentials (IAM roles) where possible. | _None — manual only_ |
