# Recommended AWS Config Rules For Threat-Informed Security Compliance

_**Please note:** An AWS Config conformance pack that will bundle these rules into a single deployable unit is under development. However, the dashboard's Threat-Informed Security Compliance tab already tracks compliance for the standard AWS Config managed rules listed below — whether you deploy them individually, through another conformance pack, or through any other mechanism. These rules are recommended by AWS Security Incident Response security engineers regardless of how they are deployed._


This document describes the AWS Config rules identified in collaboration with Security Incident Response security engineers. The rules are based on the [Threat Technique Catalog for AWS](https://aws-samples.github.io/threat-technique-catalog-for-aws/) (MITRE ATT&CK® framework).


## AWS Config Rules

### Initial Access rules

| Rule Name | Description | Type | Source Identifier | Classification | Resource Types |
|-----------|-------------|------|-------------------|----------------|----------------|
| root-account-mfa-enabled | Checks if the root user requires MFA for console sign-in | STANDARD | [ROOT_ACCOUNT_MFA_ENABLED](https://docs.aws.amazon.com/config/latest/developerguide/root-account-mfa-enabled.html) | Initial Access / IAM Protection | Account-level |
| iam-root-access-key-check | Checks whether the root user access key exists | STANDARD | [IAM_ROOT_ACCESS_KEY_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/iam-root-access-key-check.html) | Initial Access / IAM Protection | Account-level |
| iam-user-mfa-enabled | Checks if IAM users have MFA enabled | STANDARD | [IAM_USER_MFA_ENABLED](https://docs.aws.amazon.com/config/latest/developerguide/iam-user-mfa-enabled.html) | Initial Access / IAM Protection | AWS::IAM::User |
| mfa-enabled-for-iam-console-access | Checks if MFA is enabled for IAM users with console passwords | STANDARD | [MFA_ENABLED_FOR_IAM_CONSOLE_ACCESS](https://docs.aws.amazon.com/config/latest/developerguide/mfa-enabled-for-iam-console-access.html) | Initial Access / IAM Protection | AWS::IAM::User |
| s3-bucket-public-read-prohibited | Checks that S3 buckets do not allow public read access | STANDARD | [S3_BUCKET_PUBLIC_READ_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-public-read-prohibited.html) | Initial Access / S3 Protection | AWS::S3::Bucket |
| s3-bucket-public-write-prohibited | Checks that S3 buckets do not allow public write access | STANDARD | [S3_BUCKET_PUBLIC_WRITE_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-public-write-prohibited.html) | Initial Access / S3 Protection | AWS::S3::Bucket |
| autoscaling-launchconfig-requires-imdsv2 | Checks if Auto Scaling launch configurations require IMDSv2 | STANDARD | [AUTOSCALING_LAUNCHCONFIG_REQUIRES_IMDSV2](https://docs.aws.amazon.com/config/latest/developerguide/autoscaling-launchconfig-requires-imdsv2.html) | Initial Access / EC2 Protection | AWS::AutoScaling::LaunchConfiguration |
| ec2-imdsv2-check | Checks if EC2 instances require IMDSv2 | STANDARD | [EC2_IMDSV2_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/ec2-imdsv2-check.html) | Initial Access / EC2 Protection | AWS::EC2::Instance |
| ec2-launch-template-imdsv2-check | Checks if EC2 launch templates require IMDSv2 | STANDARD | [EC2_LAUNCH_TEMPLATE_IMDSV2_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/ec2-launch-template-imdsv2-check.html) | Initial Access / EC2 Protection | AWS::EC2::LaunchTemplate |
| s3-access-point-in-vpc-only | Checks if S3 access points only allow VPC access | STANDARD | [S3_ACCESS_POINT_IN_VPC_ONLY](https://docs.aws.amazon.com/config/latest/developerguide/s3-access-point-in-vpc-only.html) | Initial Access / S3 Protection | AWS::S3::AccessPoint |
| s3-access-point-public-access-blocks | Checks if S3 access points have public access blocks enabled | STANDARD | [S3_ACCESS_POINT_PUBLIC_ACCESS_BLOCKS](https://docs.aws.amazon.com/config/latest/developerguide/s3-access-point-public-access-blocks.html) | Initial Access / S3 Protection | AWS::S3::AccessPoint |
| s3-account-level-public-access-blocks-periodic | Periodically checks if account-level S3 public access blocks are enabled | STANDARD | [S3_ACCOUNT_LEVEL_PUBLIC_ACCESS_BLOCKS_PERIODIC](https://docs.aws.amazon.com/config/latest/developerguide/s3-account-level-public-access-blocks-periodic.html) | Initial Access / S3 Protection | Account-level |
| s3-bucket-level-public-access-prohibited | Checks if S3 buckets are publicly accessible | STANDARD | [S3_BUCKET_LEVEL_PUBLIC_ACCESS_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-level-public-access-prohibited.html) | Initial Access / S3 Protection | AWS::S3::Bucket |
| vpc-sg-port-restriction-check | Checks if security groups allow unrestricted inbound ports | STANDARD | [VPC_SG_PORT_RESTRICTION_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/vpc-sg-port-restriction-check.html) | Initial Access / Resource Access Protection | AWS::EC2::SecurityGroup |

## Rule Parameters
All rules parameters are supported .
