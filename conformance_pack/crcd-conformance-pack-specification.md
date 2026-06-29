# Conformance Pack Specification

_**Please note:** The AWS Config conformance pack that will bundle these rules into a single deployable unit is under development. However, the dashboard's Threat-Informed Security Compliance tab already tracks compliance for the standard AWS Config managed rules listed below — whether you deploy them individually, through another conformance pack, or through any other mechanism. These rules are recommended by AWS Security Incident Response security engineers regardless of how they are deployed._


This document describes the AWS Config rules included in the AWS Config Resource Compliance Dashboard (CRCD) Conformance Pack, built in collaboration with Security Incident Response security engineers. The rules are based on the [Threat Technique Catalog for AWS](https://aws-samples.github.io/threat-technique-catalog-for-aws/) (MITRE ATT&CK® framework).

## Naming Convention

All rules follow the format: `crcd-<lv1>-<lv2>-<rule-name>`

| Component | Description | Examples |
|-----------|-------------|----------|
| `crcd-` | Fixed prefix for CRCD conformance pack rules | - |
| `lv1` | Level 1 classification (attack tactic) | `ia`, `p`, `pe` |
| `lv2` | Level 2 classification (protection domain) | `s3`, `iam`, `ec2` |
| `rule-name` | Descriptive rule name in kebab-case | `root-account-mfa-enabled` |

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
| crcd-ia-iam-root-account-mfa-enabled | Checks if the root user requires MFA for console sign-in | STANDARD | [ROOT_ACCOUNT_MFA_ENABLED](https://docs.aws.amazon.com/config/latest/developerguide/root-account-mfa-enabled.html) | Initial Access / IAM Protection | Account-level |
| crcd-ia-iam-iam-root-access-key-check | Checks whether the root user access key exists | STANDARD | [IAM_ROOT_ACCESS_KEY_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/iam-root-access-key-check.html) | Initial Access / IAM Protection | Account-level |
| crcd-ia-iam-iam-root-not-used-regularly | Checks whether the root user is not used regularly | CUSTOM | Lambda | Initial Access / IAM Protection | Account-level |
| crcd-ia-iam-iam-user-access-key-check | Checks whether an IAM user access key exists | CUSTOM | Lambda | Initial Access / IAM Protection | AWS::IAM::User |
| crcd-ia-iam-iam-user-mfa-enabled | Checks if IAM users have MFA enabled | STANDARD | [IAM_USER_MFA_ENABLED](https://docs.aws.amazon.com/config/latest/developerguide/iam-user-mfa-enabled.html) | Initial Access / IAM Protection | AWS::IAM::User |
| crcd-ia-iam-mfa-enabled-for-iam-console-access | Checks if MFA is enabled for IAM users with console passwords | STANDARD | [MFA_ENABLED_FOR_IAM_CONSOLE_ACCESS](https://docs.aws.amazon.com/config/latest/developerguide/mfa-enabled-for-iam-console-access.html) | Initial Access / IAM Protection | AWS::IAM::User |
| crcd-ia-s3-s3-bucket-public-read-prohibited | Checks that S3 buckets do not allow public read access | STANDARD | [S3_BUCKET_PUBLIC_READ_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-public-read-prohibited.html) | Initial Access / S3 Protection | AWS::S3::Bucket |
| crcd-ia-s3-s3-bucket-public-write-prohibited | Checks that S3 buckets do not allow public write access | STANDARD | [S3_BUCKET_PUBLIC_WRITE_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-public-write-prohibited.html) | Initial Access / S3 Protection | AWS::S3::Bucket |
| crcd-ia-ec2-autoscaling-launchconfig-requires-imdsv2 | Checks if Auto Scaling launch configurations require IMDSv2 | STANDARD | [AUTOSCALING_LAUNCHCONFIG_REQUIRES_IMDSV2](https://docs.aws.amazon.com/config/latest/developerguide/autoscaling-launchconfig-requires-imdsv2.html) | Initial Access / EC2 Protection | AWS::AutoScaling::LaunchConfiguration |
| crcd-ia-ec2-ec2-imdsv2-check | Checks if EC2 instances require IMDSv2 | STANDARD | [EC2_IMDSV2_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/ec2-imdsv2-check.html) | Initial Access / EC2 Protection | AWS::EC2::Instance |
| crcd-ia-ec2-ec2-launch-template-imdsv2-check | Checks if EC2 launch templates require IMDSv2 | STANDARD | [EC2_LAUNCH_TEMPLATE_IMDSV2_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/ec2-launch-template-imdsv2-check.html) | Initial Access / EC2 Protection | AWS::EC2::LaunchTemplate |
| crcd-ia-s3-s3-access-point-in-vpc-only | Checks if S3 access points only allow VPC access | STANDARD | [S3_ACCESS_POINT_IN_VPC_ONLY](https://docs.aws.amazon.com/config/latest/developerguide/s3-access-point-in-vpc-only.html) | Initial Access / S3 Protection | AWS::S3::AccessPoint |
| crcd-ia-s3-s3-access-point-public-access-blocks | Checks if S3 access points have public access blocks enabled | STANDARD | [S3_ACCESS_POINT_PUBLIC_ACCESS_BLOCKS](https://docs.aws.amazon.com/config/latest/developerguide/s3-access-point-public-access-blocks.html) | Initial Access / S3 Protection | AWS::S3::AccessPoint |
| crcd-ia-s3-s3-account-level-public-access-blocks-periodic | Periodically checks if account-level S3 public access blocks are enabled | STANDARD | [S3_ACCOUNT_LEVEL_PUBLIC_ACCESS_BLOCKS_PERIODIC](https://docs.aws.amazon.com/config/latest/developerguide/s3-account-level-public-access-blocks-periodic.html) | Initial Access / S3 Protection | Account-level |
| crcd-ia-s3-s3-bucket-level-public-access-prohibited | Checks if S3 buckets are publicly accessible | STANDARD | [S3_BUCKET_LEVEL_PUBLIC_ACCESS_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-level-public-access-prohibited.html) | Initial Access / S3 Protection | AWS::S3::Bucket |
| crcd-ia-ra-vpc-sg-port-restriction-check | Checks if security groups allow unrestricted inbound ports | STANDARD | [VPC_SG_PORT_RESTRICTION_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/vpc-sg-port-restriction-check.html) | Initial Access / Resource Access Protection | AWS::EC2::SecurityGroup |

## Rule Details
For STANDARD rules, all parameters are supported and will not be repeated in this file. Rule parameters are specified for custom rules.

### Initial Access rules

#### IAM Protection Rules

##### crcd-ia-iam-root-account-mfa-enabled
The AWS account root user has unrestricted access to all resources within that account, its usage must be protected by Multi-Factor Authentication (MFA).

##### crcd-ia-iam-iam-root-access-key-check
Root access keys provide unrestricted access to all AWS resources and are high-value targets for attackers. Recommendation: do not create root access keys and delete any that exist.

##### crcd-ia-iam-iam-root-not-used-regularly (CUSTOM)
Root users have unrestricted access to all AWS resources and are high-value targets for attackers. Recommendation: use this user as little as possible.

###### Parameters

| Parameter Name | Description | Default value |
|----------------|-------------|---------------|
| RootUsageThresholdDays | Number of days to look back for root account usage. If root was used within this threshold, the account is marked NON_COMPLIANT | 5 |



##### crcd-ia-iam-iam-user-access-key-check (CUSTOM)
Access keys provide unrestricted access to all AWS resources and are high-value targets for attackers. Recommendation: do not create access keys and delete any that exist.

##### crcd-ia-iam-iam-user-mfa-enabled / crcd-ia-iam-mfa-enabled-for-iam-console-access
Multi-factor authentication provides an additional layer of security against compromised credentials. Enabling MFA significantly reduces the risk of unauthorized access even when passwords are compromised.

#### S3 Protection Rules

##### crcd-ia-s3-s3-bucket-public-read-prohibited
Publicly readable S3 buckets are a common attack vector for initial access and data exposure.

##### crcd-ia-s3-s3-bucket-public-write-prohibited
Publicly writable S3 buckets can be exploited for data injection, malware distribution, and resource abuse.

##### crcd-ia-s3-s3-access-point-in-vpc-only
S3 access points that allow public internet access increase the attack surface for data exfiltration and unauthorized access. Restricting to VPC-only access ensures data can only be accessed through controlled network paths.

##### crcd-ia-s3-s3-access-point-public-access-blocks
Public access block settings on S3 access points provide defense-in-depth protection against accidental public exposure of data.

##### crcd-ia-s3-s3-account-level-public-access-blocks-periodic
Continuous monitoring of account-level public access block settings ensures they remain enabled and have not been inadvertently disabled.

##### crcd-ia-s3-s3-bucket-level-public-access-prohibited
Bucket-level public access blocks provide defense-in-depth protection against accidental exposure.

#### EC2 Protection Rules

##### crcd-ia-ec2-autoscaling-launchconfig-requires-imdsv2 / crcd-ia-ec2-ec2-imdsv2-check / crcd-ia-ec2-ec2-launch-template-imdsv2-check
IMDSv2 provides enhanced security for instance metadata by requiring session-oriented requests, which prevents Server-Side Request Forgery (SSRF) attacks. Enforcing IMDSv2 significantly reduces the risk of credential theft through metadata service exploitation.

#### Resource Access Protection Rules

##### crcd-ia-ra-vpc-sg-port-restriction-check
Unrestricted inbound ports enable lateral movement within AWS environments.
