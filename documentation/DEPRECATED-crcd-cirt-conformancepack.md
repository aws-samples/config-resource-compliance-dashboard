# CRCD CIRT Conformance Pack - Rule Classification Reference

## Overview

This directory contains the rule classification reference data for the CRCD CIRT Conformance Pack. The classification system is based on the [Threat Technique Catalog for AWS](https://aws-samples.github.io/threat-technique-catalog-for-aws/), which maps AWS security controls to the MITRE ATT&CK® framework.

## Files

- **crcd-cirt-rule-classifications.yaml**: Complete reference data including taxonomy definitions, CIRT-recommended rules, naming conventions, and tag structure
- **ttc-mitre-rule-classifications.yaml**: Reference documentation only (not used in implementation)

## Classification System

### Two-Level Taxonomy

The classification system uses a two-level hierarchy:

1. **Level 1 (Tactics)**: High-level categories representing attacker objectives
2. **Level 2 (Techniques)**: Specific techniques or AWS service areas

### Level 1 Categories

| Category | Abbreviation | Description |
|----------|--------------|-------------|
| Initial Access | `ia` | Techniques used to gain initial access to AWS environments |
| Execution | `ex` | Techniques that result in adversary-controlled code running on AWS resources |
| Persistence | `p` | Techniques used to maintain access to AWS environments |
| Privilege Escalation | `pe` | Techniques used to gain higher-level permissions in AWS |
| Defense Evasion | `da` | Techniques used to avoid detection in AWS environments |
| Credential Access | `ca` | Techniques used to steal AWS credentials |
| Discovery | `d` | Techniques used to gain knowledge about AWS environments |
| Lateral Movement | `la` | Techniques used to move through AWS environments |
| Collection | `c` | Techniques used to gather data from AWS resources |
| Exfiltration | `e` | Techniques used to steal data from AWS environments |
| Impact | `i` | Techniques used to disrupt availability or compromise integrity |

### Level 2 Techniques

| Technique | Abbreviation | Description |
|-----------|--------------|-------------|
| S3 Protection | `s3` | Security controls for Amazon S3 buckets and objects |
| IAM Security | `iam` | Identity and Access Management security controls |
| EC2 Security | `ec2` | Elastic Compute Cloud security controls |
| VPC Security | `vpc` | Virtual Private Cloud network security controls |
| KMS Encryption | `kms` | Key Management Service encryption controls |
| RDS Security | `rds` | Relational Database Service security controls |
| Lambda Security | `lambda` | AWS Lambda function security controls |
| Valid Accounts | `va` | Account access and authentication controls |
| API Security | `api` | API Gateway and API access controls |
| CloudTrail Logging | `ct` | CloudTrail audit logging controls |
| Config Monitoring | `cfg` | AWS Config monitoring and compliance controls |
| EBS Security | `ebs` | Elastic Block Store security controls |
| Secrets Management | `sm` | Secrets Manager and credential protection controls |

## Naming Convention

All Config rules in the CRCD CIRT Conformance Pack follow a standardized naming pattern:

```
crcd-cirt-<lv1>-<lv2>-<rule-name>
```

### Components

- **crcd-cirt**: Fixed prefix identifying CRCD CIRT conformance pack rules
- **lv1**: Level 1 classification abbreviation (e.g., `ia`, `p`, `pe`)
- **lv2**: Level 2 classification abbreviation (e.g., `s3`, `iam`, `vpc`)
- **rule-name**: Descriptive rule name in kebab-case

### Examples

- `crcd-cirt-ia-s3-s3-bucket-public-read-prohibited`
  - Level 1: Initial Access (`ia`)
  - Level 2: S3 Protection (`s3`)
  - Rule: s3-bucket-public-read-prohibited

- `crcd-cirt-p-va-iam-root-access-key-check`
  - Level 1: Persistence (`p`)
  - Level 2: Valid Accounts (`va`)
  - Rule: iam-root-access-key-check

- `crcd-cirt-pe-iam-iam-policy-no-statements-with-admin-access`
  - Level 1: Privilege Escalation (`pe`)
  - Level 2: IAM Security (`iam`)
  - Rule: iam-policy-no-statements-with-admin-access

## Tag Structure

Each Config rule is tagged with classification information to enable filtering and querying:

### Tags

1. **crcd-cirt-lv1**: Level 1 classification abbreviation
   - Values: `ia`, `ex`, `p`, `pe`, `da`, `ca`, `d`, `la`, `c`, `e`, `i`
   - Purpose: Filter rules by Level 1 category (tactic)

2. **crcd-cirt-lv2**: Level 2 classification abbreviation
   - Values: `s3`, `iam`, `ec2`, `vpc`, `kms`, `rds`, `lambda`, `va`, `api`, `ct`, `cfg`, `ebs`, `sm`
   - Purpose: Filter rules by Level 2 technique (service area)

### Usage Examples

Query all Initial Access rules:
```
Tag filter: crcd-cirt-lv1=ia
```

Query all S3 protection rules:
```
Tag filter: crcd-cirt-lv2=s3
```

Query Initial Access rules for S3:
```
Tag filter: crcd-cirt-lv1=ia AND crcd-cirt-lv2=s3
```

## Rule Types

### Standard Rules

Standard rules use AWS-managed Config rules provided by AWS. These rules are maintained by AWS and require no custom Lambda functions.

Example:
```yaml
rule_name: "crcd-cirt-ia-s3-s3-bucket-public-read-prohibited"
rule_type: "STANDARD"
source_identifier: "S3_BUCKET_PUBLIC_READ_PROHIBITED"
```

### Custom Rules

Custom rules use Lambda functions to implement custom evaluation logic. These rules are backed by Python Lambda functions deployed as part of the conformance pack. These rules have a `source_details` block that specifies the triggering of the resource.
The field message_type acn be "ConfigurationItemChangeNotification" and "OversizedConfigurationItemChangeNotification" for change-triggered rules, OR use the following for periodic rules: "ScheduledNotification" and also specify maximum_execution_frequency to either: "One_Hour" # Options: One_Hour, Three_Hours, Six_Hours, Twelve_Hours, TwentyFour_Hours.


Example:
```yaml
rule_name: "crcd-cirt-da-cfg-config-enabled"
rule_type: "CUSTOM"
source_identifier: "LAMBDA_ARN_PLACEHOLDER"
source_details:
  - event_source: "aws.config"
    message_type: "ScheduledNotification"
    maximum_execution_frequency: "TwentyFour_Hours"
```

## CIRT Rationales

Each rule includes a rationale from the AWS Customer Incident Response Team (CIRT) explaining why the rule is recommended. These rationales are based on real-world security incidents and threat actor behaviors observed by CIRT.

Example rationale:
> "Publicly readable S3 buckets are a common attack vector for initial access and data exposure. CIRT frequently observes unauthorized access through misconfigured S3 bucket permissions."

## MITRE ATT&CK® Mapping

Each rule is mapped to one or more MITRE ATT&CK® technique IDs. This mapping helps security teams understand which threat techniques each rule helps detect or prevent.

Example mappings:
- **T1190**: Exploit Public-Facing Application
- **T1078**: Valid Accounts
- **T1078.004**: Cloud Accounts
- **T1562.008**: Impair Defenses: Disable Cloud Logs
- **T1552**: Unsecured Credentials
- **T1537**: Transfer Data to Cloud Account
- **T1486**: Data Encrypted for Impact
- **T1204**: User Execution
- **T1046**: Network Service Scanning
- **T1021**: Remote Services

## Using the Reference Data

### For CloudFormation Templates

The reference data is used to generate CloudFormation templates with proper metadata and tags:

```yaml
Resources:
  CIRTRule:
    Type: AWS::Config::ConfigRule
    Metadata:
      ThreatTechniqueCatalog:
        Level1: "Initial Access"
        Level1Abbrev: "ia"
        Level2: "S3 Protection"
        Level2Abbrev: "s3"
        MitreAttackId: "T1190"
        CIRTRationale: "Publicly readable S3 buckets are a common attack vector..."
    Properties:
      ConfigRuleName: crcd-cirt-ia-s3-s3-bucket-public-read-prohibited
      Tags:
        - Key: crcd-cirt-lv1
          Value: ia
        - Key: crcd-cirt-lv2
          Value: s3
```

### For Documentation

The reference data is used to generate comprehensive documentation tables showing all rules with their classifications, descriptions, and CIRT rationales.

### For Programmatic Access

The YAML format allows easy parsing and programmatic access for automation scripts, CI/CD pipelines, and custom tooling.

## Maintenance

When adding new rules:

1. Add the rule definition to `rule-classifications.yaml`
2. Ensure the rule name follows the naming convention
3. Include both Level 1 and Level 2 classifications
4. Add appropriate tags
5. Include MITRE ATT&CK® ID(s)
6. Provide CIRT rationale based on real-world threat intelligence
7. Update CloudFormation templates and documentation

## References

- [Threat Technique Catalog for AWS](https://aws-samples.github.io/threat-technique-catalog-for-aws/)
- [MITRE ATT&CK® Framework](https://attack.mitre.org/)
- [AWS Config Rules](https://docs.aws.amazon.com/config/latest/developerguide/managed-rules-by-aws-config.html)
- [AWS CIRT](https://aws.amazon.com/security/incident-response/)
