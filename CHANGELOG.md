_Cloud Intelligence Dashboards - AWS Config Resource Compliance Dashboard (CRCD) changelog_

# [5.X.X] - TBC
## Added

## Changed
- Support data refresh more frequently than 24 hours.

# [5.0.0] - 2026-06-30
## Added

### Dashboard features
- New data source for account metadata: AWS Organization Data Collection Module of [CID Data Collection](https://docs.aws.amazon.com/guidance/latest/cloud-intelligence-dashboards/data-collection.html). This allows the data pipeline of the dashboard to dynamically extract metadata from your AWS Organization to be displayed on the dashboard.
- Support for CID taxonomy. Use your AWS Organization metadata as filters in every tab of the dashboard.
- **Threat-Informed Security Compliance**: new dashboard tab to identify preventable, common misconfigurations that are known to create vulnerabilities exploited in attacks against AWS environments. 
- **Compliance**: added visuals that display the compliance score for each conformance pack.
- **Resource Inventory**: added visuals to show EC2 instances managed by AWS Systems Manager (SSM).
- **Config Usage Insights** Added a diagram displaying the resource count by account and Region.
- **Configuration Item Events**: added a date filter to the heat map of resource change events recorded by AWS Config. Improved documentation of the visuals at the top.

### External features
- [Backfill](./backfill/README.md) feature to show your historical AWS Config records after deployment.
- [Amazon Quick chat agent](./chat_agent/README.md). This setup combines your AWS Config dashboard with Amazon Quick's generative AI capabilities to create a compliance chat agent that understands your environment and provides contextual insights.


## Changed
- [AWS Control Tower v4.0](https://docs.aws.amazon.com/controltower/latest/userguide/config-updates-v4.html) deploys Config logs and Cloud Trail logs into different AWS accounts. The term "Log Archive account" that on previous versions uniquely indicated the AWS account receiving all logs, is not valid anymore for customers using the most recent version of Control Tower. The documentation will utilize "AWS Config account" or "Config account" instead. For the same reason, the "Log Archive bucket" will be called "AWS Config Logs bucket" or "Config Logs bucket".

- **Tag Compliance**: added support for the several AWS Config [rules](https://docs.aws.amazon.com/config/latest/developerguide/managed-rules-by-aws-config.html) ending with `-tagged`.
- **Resource Inventory**: click on an EC2 instance on the EC2 inventory table to see its attached EBS volumes on the EBS volume inventory table.

## Fixed
- Dashboard data was empty the first day of the month.
- **Configuration Item Events**: improved accuracy of data.
- **Resource Inventory**: resource counters consider all filters applied to the resource type.

# [4.0.2] - 2026-01-20
- Bugfix release for view `config_compliance`. 

## Fixed
- View `config_compliance` was using a lowercase field and thus not assigning AWS Config rules to their conformance pack. 

# [4.0.1] - 2025-11-10
Bugfix release: adopting a case sensitive Athena table for the dashboard. 
The case insensitive table of v4.0.0 does not work if you apply the same tag, but with different capitalization to a resource, e.g. `Environment` and `environment`. In that case, any query to the Athena table will fail and no data will be displayed on the dashboard.

## Changed
- Removed support for AWS Organizations Data Collection Module of the [Data Collection Stack](https://docs.aws.amazon.com/guidance/latest/cloud-intelligence-dashboards/data-collection.html). The case insensitive table is the only way to support that source of account names.

## Fixed
- The Athena table is case sensitive

# [4.0.0] - 2025-10-30
## Added
- Account names
- **Cost Contributors** tab, to find the contributors to AWS Config cost, for example the most evaluated rules, or most changing resources.
- (**Configuration Items** tab renamed to **Resource Inventory**).
- **Resource Inventory** tab, count of total resources currently in the list (after filters at the top are applied).
- **Resource Inventory** tab, graphs showing the distribution of EC2 instances across Availability Zones.


## Changed
- Lambda partitioner function: optimized Amazon Athena API calls by checking if a partition exists already before creating it.
- **Resource Inventory** tab, removed **Last Modified** column from Lambda inventory. Resource event information is accessible from **Configuration Items Events** tab.
- **Resource Inventory** tab, added filters on Lambda (runtime) and RDS (engine, engine version, certificate authority).
- **Tag Compliance** tab, moved as second tab from the left. All visuals now include all AWS Config rules whose name starts with `required-tags`, `required-tag`, `requiredtags` or `requiredtag`. The filtering is also case insensitive.
- Athena table is now case-insensitive in the `case.insensitive` property in the SerDe (Serializer/Deserializer) configuration. This configuration specifically affects how field names in the JSON data are matched to column names in the Athena table. With this new configuration, case is ignored when matching JSON field names to the expected column names.
- When deploying AWS Config rules and conformance packs across an organization, you may notice that the names often have random postfixes added to them. This is actually by design and serves several important purposes within the AWS infrastructure. The dashboard removes that part on all visuals so that all rule and conformance pack names can be correlated. For example, `my-rule-[random-text]` is displayed as `my-rule`. When AWS Config rules and conformance packs are listed on tables, both the normalized and the original name are reported, so that you have a full reference to the rule or conformance pack if you download the data of the table.
- **About** tab, new version.
- Improved installation of the dashboard resources with `cid-cmd` tool: it is not necessary anymore to download the YAML template.

## Fixed
- Tooltip texts of visuals have meaningful field names.


# [3.0.1] - 2025-05-09
This is a technical update to allow the CRCD Dashboard to be easier to install together with other CID Dashboards.

## Added
- The CloudFormation template exports the Amazon QuickSight policy to access the CRCD resources. This will be used by the `cid-cmd` tool to manage permissions during the dashboard deployment in case other CID dashboards exist.

## Changed
- Clarified that `required-tags` is a case-sensitive filter

# [3.0.0] - 2025-03-27
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
- **Configuration Item Events** tab, **All AWS Config Events** table filtered by account ID and Region selectors at the top
- Redesigned all the Athena views for accuracy and performance.


Upgrading to v3.0.0 from an older version? Read [this](./documentation/upgrade.md) first.

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
- By default, partitioning is done on AWS Config snapshot files.

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