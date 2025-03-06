# [2.1.2] - 2025-01-20
## Added
- Cloud Formation template capable of setting S3 replication in case of KMS encrypted buckets

## Changed
- Deployment instructions moved to the [Cloud Intelligence Dashboards Well Architected Labs](https://catalog.workshops.aws/awscid/en-US/dashboards/additional/config-resource-compliance-dashboard)
- **About** tab: added our new email address aws-config-dashboard@amazon.com

## Fixed
- **Compliance** tab, control **Current number of compliant AWS Config rules** and **Current number of non-compliant AWS Config rules**: adjusted aggregation parameter so that they report correct data.
- **Tag Compliance** tab: fixed a typo on the description at the top
- Redesigned all the views for accuracy and performance

# [2.1.1] - 2025-01-06
## Fixed
- Typo on CloudFormation template file name
- Typo on dashboard template

# [2.1.0] - 2024-12-16
## Added
- About page
- Configuration Items Event page
- Added the following controls to Configuration Items page:
  - EBS Volume inventory 
  - AWS Config Inventory Dashboard visuals 
  - Support for technical lifecycle management by listing current version of resources (RDS Engine, Lambda runtime) that can be deprecated or enter extended support
- Standard installation process completely based on CloudFormation, without the needs for manual activities
- Support for KMS-encrypted Amazon S3 Dashboard bucket

## Changed
- Interface improvements
- Updated installation instructions
- Clarified that the dashboard supports both AWS Config history and snapshot files
- Partitioning strategy of AWS Config data now considers both AWS Config snapshot and history files
- By default, partitionig is done on AWS Config snapshot files

## Fixed
- Resources that were deleted or not recently changed are accurately considered
- Removed reserved concurrency limitation on Lambda function


# [2.0.0] - 2024-05-01
## Added
- CloudFormation scripts
- Inventory and Tag Compliance tags on the dashboard
- Support AWS Config setups from AWS ControlTower (compatible with AWS Organizations) and manual (compatible with standalone AWS Accounts)
- Rewritten `README.md` with new architecture and installation instructions

## Changed
- Removed dependency on CloudTrail data
- Removed Terraform scripts

## Fixed
N/A

# [1.0.0] - 2023-09-14
Initial version