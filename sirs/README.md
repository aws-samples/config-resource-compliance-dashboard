# AWS Config Resource Compliance Dashboard (CRCD) Security Incident Response Service (SIRS) Conformance Pack

This folder contains templates for deploying AWS Config rules recommended by AWS Security Incident Response Service (SIRS) security engineers.

## Overview

The AWS Config Resource Compliance Dashboard (CRCD) Security Incident Response Service (SIRS) Conformance Pack is a comprehensive compliance monitoring solution that deploys AWS Config rules recommended by SIRS security engineers. This conformance pack helps customers maintain security and compliance best practices across their AWS environments.

## Features
- **Recommended Rules**: Includes both standard AWS Config managed rules and custom Lambda-backed rules recommended by AWS SIRS security engineers.
- **Threat Technique Catalog Classification**: Each rule is classified according to the Threat Technique Catalog for AWS (based on MITRE ATT&CK®).
- **Flexible Deployment**: Supports both AWS Organizations (organization-wide deployment) and standalone AWS accounts.
- **Multi-Region Support**: Deploys across all AWS regions where AWS Config is enabled.
- **Automatic Updates**: New accounts in AWS Organizations automatically receive the conformance pack.

## Architecture

### Deployment Modes

#### Organization-Wide Deployment
- Uses CloudFormation StackSets with automatic deployment enabled.
- Deploys to all accounts and regions automatically.
- New accounts receive the conformance pack automatically via StackSet configuration.
- Management account or delegated administrator hosts the StackSet.

#### Standalone Account Deployment
- Uses the same template as above, tailored to deploy the conformance pack in a single account.
- Single account receives all resources, deploys in all regions of the account.
- Can be deployed in any account.

### Conformance Packs
The solution deploys two conformance packs:
- **CRCD-SIRS-Security-Recommendations** containing all standard AWS Config rules deployed in all regions and all accounts of your organization.
- **CRCD-SIRS-Security-Recommendations-IA-IAM** containing all rules that apply to IAM resources, including the custom rules. Since IAM resources are global, these rules can be deployed on one region to avoid redundancy.

The conformance packs support all parameters to their AWS Config rules and manages automatically regional availability of rules - i.e. you can deploy the conformance pack in all Regions where AWS Config is enabled, and if a rule is not available in a region, it will be automatically skipped.

## Files

### `crcd-sirs-conformance-pack-specification.yaml`
Contains the specification of all AWS Config and custom rules that will be deployed as part of the conformance pack.

### `crcd-sirs-conformance-pack.yaml`
Cloud Formation template to deploy the conformance pack and the related AWS resources. 

### `README.md`
Documentation and installation instructions.

## Prerequisites

### Any deployment mode:
- **AWS Config**: Must be enabled in target accounts/regions.

### Organization-Wide Deployment:
- **AWS Config** enabled organization-wide.
- **Service-Managed StackSets**: Enable trusted access for CloudFormation StackSets in Organizations.
- An account designated as AWS Config and AWS Cloudformation delegated administrator (recommended).
- Deploy from the deletaged administrator of both [AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/stacksets-orgs-delegated-admin.html) and [AWS Config](https://docs.aws.amazon.com/config/latest/developerguide/aggregated-register-delegated-administrator.html).

# Deployment

## Step 1
1. Log into the AWS Management Console for your account or delegated admin for AWS Config of your organization.
1. Select a region that will be the base region for your deployment and where you will deploy the IAM-related rules of your Conformance Pack
1. Follow the link to open the cloud formation [template](https://console.aws.amazon.com/cloudformation/home#/stacks/create/review?&templateURL=https://aws-managed-cost-intelligence-dashboards.s3.amazonaws.com/cfn/crcd-sirs-conformance-pack.yaml&stackName=crcd-sirs-conformance-pack-resources) in your CloudFormation console. 
1. Specify the following parameters:
   - `Deployment mode` Choose deployment mode: `AWS Organizations` for multi-account and multi-region deployment, or `Standalone` for single-account multi-region deployment.
   - `Deployment account type` Choose type of deployment account (the current account). Select `Delegated Admin` if this account is the AWS Config and AWS CloudFormation delegated admin, or `Management Account` if you run this template from the management account of your AWS Organization. This parameter is used only when deployment mode is AWS Organizations.
   - `Target Organization Root or Organizational Unit IDs` Enter the root OU ID (`r-xxxx`) to deploy to all accounts of your organization, or specify a comma-separated list of Organizational Unit IDs (`ou-xxxx-xxxxxxxx`) to deploy to. Leave empty in standalone mode.
   - `Accounts to exclude` A comma-separated list of accounts that will not receive the organization conformance pack (leave empty to deploy to all accounts). **Make sure you add here any account ID where AWS Config is not enabled, otherwise the entire stack will fail**. This parameter is used only when deployment mode is AWS Organizations.
   - `Deployment Regions` Enter a comma-separated list of regions where AWS Config is enabled and the conformance pack should be deployed. **Make sure you specify only regions where AWS Config is enabled in all accounts in scope, otherwise the entire stack will fail**.
5. Specify the parameters to the AWS Config rules in the following CloudFormation parameters:
   - `Root Account Not Used Regularly rule: root account usage threshold (days)` Custom rule `crcd-sirt-ia-iam-iam-root-not-used-regularly` checks that the root user is not used regularly by looking when root was used last. This parameter specifies the number of days to look back for root account usage. If root was used within this threshold, the rule is marked NON_COMPLIANT.
   - `S3 Bucket-Level Public Access Prohibited rule: excluded public buckets` Supports the parameter of rule [S3_BUCKET_LEVEL_PUBLIC_ACCESS_PROHIBITED](https://docs.aws.amazon.com/config/latest/developerguide/s3-bucket-level-public-access-prohibited.html). Open the link for documentation of what these parameters are.
   - `S3 Access Point Public Access Block rule: excluded access points` Supports the parameter of rule [S3_ACCESS_POINT_PUBLIC_ACCESS_BLOCKS](https://docs.aws.amazon.com/config/latest/developerguide/s3-access-point-public-access-blocks.html). Open the link for documentation of what these parameters are.
   - The next four: `S3 Account-Level Public Access Block rule: enforce option IgnorePublicAcls`,
   - `S3 Account-Level Public Access Block rule: enforce option BlockPublicPolicy`,
   - `S3 Account-Level Public Access Block rule: enforce option BlockPublicAcls`, and
   - `S3 Account-Level Public Access Block rule: enforce option RestrictPublicBuckets` support the parameters of rule [S3_ACCOUNT_LEVEL_PUBLIC_ACCESS_BLOCKS_PERIODIC](https://docs.aws.amazon.com/config/latest/developerguide/s3-account-level-public-access-blocks-periodic.html). Open the link for documentation of what these parameters are.
   - The next four: `VPC Security Group Port Restriction Check rule: restricted ports`, 
   - `VPC Security Group Port Restriction Check rule: protocol type`, 
   - `VPC Security Group Port Restriction Check rule: exclude external security groups`, and
   - `VPC Security Group Port Restriction Check rule: IP type` support the parameters of rule [VPC_SG_PORT_RESTRICTION_CHECK](https://docs.aws.amazon.com/config/latest/developerguide/vpc-sg-port-restriction-check.html). Open the link for documentation of what these parameters are.
6. Leave all other parameters at their default value.
1. Run the CloudFormation template.

# Updates

To update the parameters of the AWS Config rules of the template open the CloudFormation stack in the main region and update the stack. Changes propagate automatically to all accounts/regions


# References
- [Threat Technique Catalog for AWS](https://aws-samples.github.io/threat-technique-catalog-for-aws/)
- [MITRE ATT&CK® Framework](https://attack.mitre.org/)
- [AWS Config Rules](https://docs.aws.amazon.com/config/latest/developerguide/managed-rules-by-aws-config.html)
- [AWS SIRS](https://aws.amazon.com/security-incident-response/)