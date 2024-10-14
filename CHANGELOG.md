# [2.1.0] - 2024-09-10
## Added
- About page
- Lambda Inventory to Configuration Items
- EBS Volumes to Configuration Items
- Inventory Dashboard visuals to Configuration Items
- Support for technical lifecycle management by listing current version of resources (RDS Engine, Lambda runtime) that can be deprecated or enter extended support

## Changed
- Interface improvements on Compliance
  - Reorganized the order and clarified the titles of the visuals
  - Sorting of horizontal bars
  - Removed filter on date at the top
  - Evolution visuals filtered to include only the last 6 months
  - New Conformance pack graphs
  - For the tables at the bottom: added filters, sorting and use of icons on Compliance Type columns, Account ID and Region consistently the first two columns
- Interface improvements on Configuration Items
  - Account ID and Region consistently the first two columns of the inventory tables in Configuration Items
- Interface improvements on Tag Compliance
- Updated installation instructions
- Clarified that the dashboard supports both configuration history and configuration snapshot files of AWS Config
- Partitioning strategy of AWS Config data now considers both ConfigSnapshot and ConfigHistory records


## Fixed
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