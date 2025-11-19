# CRCD CIRT Config Rules Deployment

This folder contains templates for deploying AWS Config rules recommended by the AWS Customer Incident Response Team (CIRT) across your AWS Organization.

## Files

### `crcd-cirt-stackset-deployment.yaml`
**Main deployment template** - Deploy this from your management account to create a StackSet that deploys Config rules organization-wide.

### `crcd-cirt-config-rules-template.yaml`
Target template deployed by the StackSet to each account/region. Contains both AWS managed rules and custom Lambda-based rules.

## Deployment Options

### Option 1: StackSet Deployment
For organization-wide deployment including custom Lambda rules:

1. **Deploy from Management Account**:
   ```bash
   aws cloudformation create-stack \
     --stack-name crcd-cirt-deployment \
     --template-body file://crcd-cirt-stackset-deployment.yaml \
     --parameters ParameterKey=TargetRegions,ParameterValue="us-east-1,us-west-2,eu-west-1" \
     --capabilities CAPABILITY_IAM
   ```

2. **Parameters**:
   - `TargetRegions`: Regions to deploy to
   - `ExcludedAccounts`: Accounts to exclude (optional)
   - `PermissionModel`: SERVICE_MANAGED (default) or SELF_MANAGED


## What Gets Deployed

### AWS Managed Config Rules:
- Root account MFA enforcement
- IAM user MFA requirements
- EC2 IMDSv2 checks
- S3 public access prevention
- VPC security group restrictions

### Custom Lambda Rule:
- CloudTrail logging verification (daily check)
- Returns COMPLIANT/NON_COMPLIANT to Config service

## Prerequisites

### For StackSet Deployment:
- **Service-Managed StackSets**: Enable trusted access for CloudFormation StackSets in Organizations
- **Self-Managed StackSets**: Create required IAM roles in management and target accounts
- **AWS Config**: Must be enabled in target accounts/regions

### For Conformance Pack:
- AWS Config enabled organization-wide
- Config delegated administrator (optional)

## Monitoring

After deployment, monitor compliance through:
- AWS Config Console (Compliance Dashboard)
- AWS Config Aggregator (if configured)
- CloudWatch metrics and alarms
- CRCD Dashboard (if deployed)

## Updates

To update rules:
1. Modify the template
2. Update the StackSet through CloudFormation console or CLI
3. Changes propagate automatically to all accounts/regions