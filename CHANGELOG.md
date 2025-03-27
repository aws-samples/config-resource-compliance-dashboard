

see work log for more



# [3] - 2025-03-27
## Added
- **Compliance** tab, added compliance score visuals for resources, AWS Config rules and conformance packs.
- **Configuration Item Events** tab, added **AWS Config Coverage** visuals, reorganized visuals in the tab.
- Fully automated S3 replication in case of KMS encrypted buckets, no more manual configuration needed.

## Changed
- Deployment instructions moved to the [Cloud Intelligence Dashboards Well Architected Labs](https://catalog.workshops.aws/awscid/en-US/dashboards/additional/config-resource-compliance-dashboard).
- **Configuration Items** tab, reviewed fields displayed on **RDS Inventory**, which now include Resource ID and DB Instance.
- **About** tab: added our new email address `aws-config-dashboard@amazon.com`.
- CloudWatch Logs retention period for the Lambda functions set to 14 days.

## Fixed
- **Compliance** tab, control **Current number of compliant AWS Config rules** and **Current number of non-compliant AWS Config rules**: adjusted aggregation parameter so that they report correct data.
- **Compliance** tab, visuals that compare trends of current month vs. the previous one are now color-formatted appropriately. E.g. trends of non compliant resources going up is bad, hence the dashboard will use red in case of positive number here. 
- **Tag Compliance** tab: fixed a typo on the description at the top.
- **Configuration Item Events** correctly captures all resource events in up to the previous six months.
- **Configuration Item Events** tab, **All AWS Config Events** table filtered by account ID and region selectors at the top
- Redesigned all the Athena views for accuracy and performance.


Upgrading to v3 from an older version? Read [this](./documentation/upgrade.md) first.

# [2.1.1] - 2025-01-06
## Fixed
- Typo on CloudFormation template file name.
- Typo on dashboard template.

# [2.1.0] - 2024-12-16
## Added
- About page.
- Configuration Items Event page.
- Added the following controls to Configuration Items page:
  - EBS Volume inventory.
  - AWS Config Inventory Dashboard visuals. 
  - Support for technical lifecycle management by listing current version of resources (RDS Engine, Lambda runtime) that can be deprecated or enter extended support.
- Standard installation process completely based on CloudFormation, without the needs for manual activities.
- Support for KMS-encrypted Amazon S3 Dashboard bucket.

## Changed
- Interface improvements.
- Updated installation instructions.
- Clarified that the dashboard supports both AWS Config history and snapshot files.
- Partitioning strategy of AWS Config data now considers both AWS Config snapshot and history files.
- By default, partitionig is done on AWS Config snapshot files.

## Fixed
- Resources that were deleted or not recently changed are accurately considered.
- Removed reserved concurrency limitation on Lambda function.


# [2.0.0] - 2024-05-01
## Added
- CloudFormation scripts.
- Inventory and Tag Compliance tags on the dashboard.
- Support AWS Config setups from AWS ControlTower (compatible with AWS Organizations) and manual (compatible with standalone AWS Accounts).
- Rewritten `README.md` with new architecture and installation instructions.

## Changed
- Removed dependency on CloudTrail data.
- Removed Terraform scripts.

## Fixed
N/A

# [1.0.0] - 2023-09-14
Initial version.