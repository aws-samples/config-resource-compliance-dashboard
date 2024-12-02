# [2.1.0] - 2024-10-18
## Added
- About page
- Configuration Items Event page
- Added to Configuration Items page:
  - EBS Volume inventory 
  - AWS Config Inventory Dashboard visuals 
  - Support for technical lifecycle management by listing current version of resources (RDS Engine, Lambda runtime) that can be deprecated or enter extended support
- Installation process completely based on CloudFormation, no more manual activities are needed 
- Documentation and support for KMS-encrypted Amazon S3 buckets or AWS Config delivery channels

## Changed
- Interface improvements
- Updated installation instructions
- Clarified that the dashboard supports both AWS Config history and snapshot files
- Partitioning strategy of AWS Config data now considers both ConfigSnapshot and ConfigHistory records


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