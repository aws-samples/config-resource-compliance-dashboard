# Operational Best Practices for AWS Security Incident Response

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
- **Extended version only**: Deploy the prerequisites CloudFormation template (`crcd-conformance-pack-prerequisites.yaml`) first to create the required Lambda functions. See [Extended Version](#extended-version) below.


## Deployment (Base Version)

### Single Account Deployment

```
aws configservice put-conformance-pack \
  --conformance-pack-name Operational-Best-Practices-for-AWS-Security-Incident-Response \
  --template-body file://crcd-conformance-pack-template.yaml \
  --region <REGION>
```

### Organization-Wide Deployment

```
aws configservice put-organization-conformance-pack \
  --organization-conformance-pack-name Operational-Best-Practices-for-AWS-Security-Incident-Response \
  --template-body file://crcd-conformance-pack-template.yaml
```

Alternatively, the base template can be deployed directly from the AWS Config console by selecting it from the conformance pack dropdown.


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


## Rules

### Initial Access — S3 Protection

These rules detect S3 misconfigurations that could allow unauthorized access to data.

| Rule Name | AWS Config Managed Rule | Description |
|-----------|------------------------|-------------|
| `crcd-ia-s3-s3-bucket-public-read-prohibited` | [S3_BUCKET_PUBLIC_READ_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-public-read-prohibited.html) | Checks that S3 buckets do not allow public read access. Public read access can expose sensitive data to the internet. |
| `crcd-ia-s3-s3-bucket-public-write-prohibited` | [S3_BUCKET_PUBLIC_WRITE_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-public-write-prohibited.html) | Checks that S3 buckets do not allow public write access. Public write access can allow attackers to modify or plant malicious content. |
| `crcd-ia-s3-s3-access-point-in-vpc-only` | [S3_ACCESS_POINT_IN_VPC_ONLY](https://docs.aws.amazon.com/config/latest/developerguide/s3-access-point-in-vpc-only.html) | Checks whether S3 access points are configured to only allow access from within a VPC, preventing internet-based access. |
| `crcd-ia-s3-s3-access-point-public-access-blocks` | [S3_ACCESS_POINT_PUBLIC_ACCESS_BLOCKS](https://docs.aws.amazon.com/config/latest/developerguide/s3-access-point-public-access-blocks.html) | Checks whether S3 access points have public access block settings enabled. |
| `crcd-ia-s3-s3-account-level-public-access-blocks-periodic` | [S3_ACCOUNT_LEVEL_PUBLIC_ACCESS_BLOCKS_PERIODIC](https://docs.aws.amazon.com/config/latest/developerguide/s3-account-level-public-access-blocks-periodic.html) | Periodically checks whether S3 account-level public access block settings remain enabled. Account-level blocks provide a safety net against bucket-level misconfigurations. |
| `crcd-ia-s3-s3-bucket-level-public-access-prohibited` | [S3_BUCKET_LEVEL_PUBLIC_ACCESS_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-level-public-access-prohibited.html) | Checks whether individual S3 buckets have public access blocked at the bucket level. |

### Initial Access — EC2 Security (IMDSv2)

These rules detect EC2 instances vulnerable to Server-Side Request Forgery (SSRF) attacks through the Instance Metadata Service.

| Rule Name | AWS Config Managed Rule | Description |
|-----------|------------------------|-------------|
| `crcd-ia-ec2-autoscaling-launchconfig-requires-imdsv2` | [AUTOSCALING_LAUNCHCONFIG_REQUIRES_IMDSV2](https://docs.aws.amazon.com/config/latest/developerguide/autoscaling-launchconfig-requires-imdsv2.html) | Checks whether Auto Scaling launch configurations require IMDSv2. IMDSv1 is vulnerable to SSRF attacks that can steal instance credentials. |
| `crcd-ia-ec2-ec2-imdsv2-check` | [EC2_IMDSV2_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/ec2-imdsv2-check.html) | Checks whether running EC2 instances are configured to require IMDSv2. |
| `crcd-ia-ec2-ec2-launch-template-imdsv2-check` | [EC2_LAUNCH_TEMPLATE_IMDSV2_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/ec2-launch-template-imdsv2-check.html) | Checks whether EC2 launch templates are configured to require IMDSv2 for new instances. |

### Initial Access — Resource Access Protection

These rules detect overly permissive network configurations that could allow unauthorized network access.

| Rule Name | AWS Config Managed Rule | Description |
|-----------|------------------------|-------------|
| `crcd-ia-ra-vpc-sg-port-restriction-check` | [VPC_SG_PORT_RESTRICTION_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/vpc-sg-port-restriction-check.html) | Checks whether security groups allow unrestricted inbound traffic on specified ports. Open SSH (22) and RDP (3389) ports are commonly exploited for unauthorized access. |


## Remediation Guidance

If a resource is evaluated as NON_COMPLIANT, follow the remediation steps below:

| Category | Remediation |
|----------|-------------|
| **S3 public access** | Enable S3 Block Public Access at the account and/or bucket level. Review and remove any bucket policies or ACLs that grant public access. |
| **S3 access points** | Configure access points to use VPC-only network origin. Enable public access blocks on all access points. |
| **EC2 IMDSv2** | Update instance metadata options to set `HttpTokens` to `required`. Update launch configurations and launch templates to enforce IMDSv2. |
| **Security group ports** | Remove inbound rules that allow unrestricted access (0.0.0.0/0 or ::/0) on ports 22 and 3389. Restrict access to known IP ranges or use AWS Systems Manager Session Manager as an alternative to SSH/RDP. |


## Regional Availability

Some AWS Config managed rules are not available in all AWS Regions. Before deploying this conformance pack, verify that the rules are supported in your target Region by consulting the [AWS Config Managed Rules by Region Availability](https://docs.aws.amazon.com/config/latest/developerguide/managing-rules-by-region-availability.html) page.

Rules with known regional limitations:
- `AUTOSCALING_LAUNCHCONFIG_REQUIRES_IMDSV2` — Not available in ap-southeast-5, ap-southeast-7, mx-central-1, ap-east-1, ca-west-1.
- `S3_ACCESS_POINT_IN_VPC_ONLY` — Not available in ap-southeast-5, ap-southeast-7, mx-central-1, ap-east-1, ca-west-1.
- `S3_ACCESS_POINT_PUBLIC_ACCESS_BLOCKS` — Not available in ap-southeast-5, ap-southeast-7, mx-central-1, ap-east-1, ca-west-1.
- `EC2_LAUNCH_TEMPLATE_IMDSV2_CHECK` — Not available in ap-southeast-5, ap-southeast-7, mx-central-1, ap-east-1, ca-west-1, me-central-1, ap-south-2, ap-southeast-4, il-central-1, eu-south-2, eu-central-2.
- `VPC_SG_PORT_RESTRICTION_CHECK` — Not available in ap-southeast-5, ap-southeast-7, mx-central-1, ap-east-1, ca-west-1, cn-north-1.

If you deploy this conformance pack in a Region where a rule is not available, the deployment will fail. Remove unsupported rules from the template before deploying in those Regions.


## Extended Version

The extended version adds IAM protection rules that detect identity-based misconfigurations commonly exploited for initial access. It includes all rules from the base template plus:

### Additional Managed Rules (Initial Access — IAM Protection)

| Rule Name | AWS Config Managed Rule | Description |
|-----------|------------------------|-------------|
| `crcd-ia-iam-root-account-mfa-enabled` | [ROOT_ACCOUNT_MFA_ENABLED](https://docs.aws.amazon.com/config/latest/developerguide/root-account-mfa-enabled.html) | Checks if the root user has MFA enabled for console sign-in. A root account without MFA is a critical exposure. |
| `crcd-ia-iam-iam-root-access-key-check` | [IAM_ROOT_ACCESS_KEY_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/iam-root-access-key-check.html) | Checks whether root user access keys exist. Root access keys provide unrestricted access and should be deleted. |
| `crcd-ia-iam-iam-user-mfa-enabled` | [IAM_USER_MFA_ENABLED](https://docs.aws.amazon.com/config/latest/developerguide/iam-user-mfa-enabled.html) | Checks if IAM users have MFA enabled. Users without MFA are vulnerable to credential theft. |
| `crcd-ia-iam-mfa-enabled-for-iam-console-access` | [MFA_ENABLED_FOR_IAM_CONSOLE_ACCESS](https://docs.aws.amazon.com/config/latest/developerguide/mfa-enabled-for-iam-console-access.html) | Checks if MFA is enabled for all IAM users with console passwords. |

### Custom Lambda Rules (Initial Access — IAM Protection)

| Rule Name | Description |
|-----------|-------------|
| `crcd-ia-iam-iam-root-not-used-regularly` | Checks whether the root user has been used within a configurable threshold (default: 5 days). Root usage is a strong indicator of either compromise or poor operational practice. |
| `crcd-ia-iam-iam-user-access-key-check` | Checks whether IAM users have active access keys. Access keys are long-lived credentials that are high-value targets for attackers. |

### Extended Version Parameters

In addition to the base parameters, the extended version requires:

| Parameter | Required | Description |
|-----------|----------|-------------|
| `RootNotUsedRegularlyLambdaArn` | Yes | ARN of the Lambda function for the root usage check. Obtained from the prerequisites template output. |
| `UserAccessKeyCheckLambdaArn` | Yes | ARN of the Lambda function for the access key check. Obtained from the prerequisites template output. |
| `RootUsageThresholdDays` | No (default: `5`) | Number of days to look back for root account usage. If root was used within this threshold, the account is marked NON_COMPLIANT. |

### Deployment Steps (Extended Version)

#### Single Account Deployment

1. Deploy the prerequisites template:
   ```
   aws cloudformation deploy \
     --template-file crcd-conformance-pack-prerequisites.yaml \
     --stack-name crcd-conformance-pack-prerequisites \
     --capabilities CAPABILITY_NAMED_IAM
   ```

2. Get the Lambda ARNs from the stack outputs:
   ```
   aws cloudformation describe-stacks \
     --stack-name crcd-conformance-pack-prerequisites \
     --query 'Stacks[0].Outputs'
   ```

3. Deploy the extended conformance pack using the ARNs from step 2:
   ```
   aws configservice put-conformance-pack \
     --conformance-pack-name Operational-Best-Practices-for-AWS-Security-Incident-Response \
     --template-body file://crcd-conformance-pack-template-extended.yaml \
     --conformance-pack-input-parameters \
       ParameterName=RootNotUsedRegularlyLambdaArn,ParameterValue=<ARN_FROM_STEP_2> \
       ParameterName=UserAccessKeyCheckLambdaArn,ParameterValue=<ARN_FROM_STEP_2>
   ```

#### Organization-Wide Deployment

1. Deploy the prerequisites template in the delegated administrator or management account:
   ```
   aws cloudformation deploy \
     --template-file crcd-conformance-pack-prerequisites.yaml \
     --stack-name crcd-conformance-pack-prerequisites \
     --capabilities CAPABILITY_NAMED_IAM
   ```

   For organization-wide deployment, the prerequisite Lambda functions must also be deployed in each member account. Use CloudFormation StackSets to deploy the prerequisites across the organization.

2. Get the Lambda ARNs from the stack outputs:
   ```
   aws cloudformation describe-stacks \
     --stack-name crcd-conformance-pack-prerequisites \
     --query 'Stacks[0].Outputs'
   ```

3. Deploy the extended conformance pack across the organization:
   ```
   aws configservice put-organization-conformance-pack \
     --organization-conformance-pack-name Operational-Best-Practices-for-AWS-Security-Incident-Response \
     --template-body file://crcd-conformance-pack-template-extended.yaml \
     --conformance-pack-input-parameters \
       ParameterName=RootNotUsedRegularlyLambdaArn,ParameterValue=<ARN_FROM_STEP_2> \
       ParameterName=UserAccessKeyCheckLambdaArn,ParameterValue=<ARN_FROM_STEP_2>
   ```

### Extended Version Remediation

| Category | Remediation |
|----------|-------------|
| **Root MFA** | Enable MFA on the root user via the IAM console under Security Credentials. Use a hardware MFA device for maximum protection. |
| **Root access keys** | Delete root user access keys immediately. Use IAM roles or IAM Identity Center for programmatic access instead. |
| **User MFA** | Enable MFA for all IAM users, especially those with console access. Consider enforcing MFA via IAM policies. |
| **Root usage** | Investigate any recent root account activity. Root should only be used for tasks that specifically require it (e.g., closing the account, changing support plans). |
| **User access keys** | Delete active access keys from IAM users. Migrate workloads to IAM roles. For human users, use IAM Identity Center with temporary credentials. |


## FAQ

**Q: What is the difference between the base and extended versions?**

The base template (`crcd-conformance-pack-template.yaml`) contains only AWS Config managed rules and can be deployed directly from the AWS Config console dropdown with no prerequisites. The extended template (`crcd-conformance-pack-template-extended.yaml`) adds IAM protection rules — including two custom Lambda-based rules — and requires deploying the prerequisites template first.

| Version | File | Rules | Prerequisites | Console Dropdown |
|---------|------|-------|---------------|-----------------|
| Base | `crcd-conformance-pack-template.yaml` | 10 managed rules | None | Yes |
| Extended | `crcd-conformance-pack-template-extended.yaml` | 14 managed + 2 custom rules | Lambda functions via `crcd-conformance-pack-prerequisites.yaml` | No (download only) |

**Q: How is this pack different from other published conformance packs?**

Other conformance packs are organized by compliance framework (NIST, PCI, CIS) or AWS service (S3, EC2). They are comprehensive — often containing 50 to 100+ rules — and are designed for customers who need to demonstrate compliance with a specific standard. This pack takes a different approach: it is curated by AWS Security Incident Response engineers based on the misconfigurations they see most frequently exploited in real attacks. It is intentionally small, making it cost-effective and accessible to customers who are beginning their security journey on AWS. Rather than covering every possible check, it focuses on the specific vulnerabilities that threat actors target most often to gain initial access.

**Q: I already have other conformance packs deployed. Should I still use this one?**

If you already have a comprehensive conformance pack (e.g., CIS, NIST), the rules in this pack are likely already covered. This pack is most valuable for customers who have no conformance packs deployed and want a low-cost starting point with the highest security impact.

**Q: Why do rule names have the `crcd-` prefix?**

The rule naming convention (`crcd-ia-{category}-{rule}`) encodes the threat tactic and category, enabling automated classification and visualization on security dashboards. The prefix `crcd` stands for Config Resource Compliance Dashboard. `ia` refers to the MITRE ATT&CK tactic "Initial Access."

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


## Multi-Region Deployment

Since IAM resources are global, the custom Lambda-based IAM rules only need to run in a single region. For multi-region coverage, combine the extended template in one region with the base template in all other regions.

### Strategy

| Region | Template | What it covers |
|--------|----------|----------------|
| Primary region (e.g., us-east-1) | Extended template | S3, EC2, Security Groups + IAM custom rules (root usage, access keys, MFA) |
| All other regions | Base template | S3, EC2, Security Groups |

### Steps

1. **Choose a primary region** for your IAM rules (any region where AWS Config is enabled).

2. **Deploy the extended template in the primary region** 
Open CloudShell or the CLI in your main region and follow the Extended Version steps above for the single account deployment.

3. **Deploy the base template in all other regions:**
Make sure your default region is not on the list below.

   ```
   REGIONS="us-east-1 us-east-2 us-west-2 eu-central-1 eu-north-1 ap-southeast-1 ap-northeast-1"

   for REGION in $REGIONS; do
     echo "Deploying base conformance pack in $REGION..."
     aws configservice put-conformance-pack \
       --conformance-pack-name Operational-Best-Practices-for-AWS-Security-Incident-Response \
       --template-body file://crcd-conformance-pack-template.yaml \
       --region $REGION
   done
   ```

This gives you full coverage: regional resource checks (S3, EC2, security groups) in every region, plus the global IAM checks running once in your primary region.

