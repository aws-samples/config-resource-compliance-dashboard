# Cloud Intelligence Dashboards - AWS Config Resource Compliance Dashboard (CRCD) v3

## Description

AWS Config is a fully managed service that provides you with resource inventory, configuration history, and configuration change notifications for security and governance.

The Amazon Web Services (AWS) Config Resource Compliance Dashboard (CRCD) shows the inventory of your AWS resources, along with their compliance status, across multiple AWS accounts and regions by leveraging your AWS Config data.

![CRCD](images/compliance-1.png "AWS Config Dashboard, Compliance tab")
![CRCD](images/compliance-2.png "AWS Config Dashboard, Compliance tab")


### Advantages
The AWS Config Resource Compliance Dashboard addresses significant challenges of AWS customers in maintaining their compliance and security posture and establishing effective resource configuration management practices at scale.

Through this unified platform, organizations can bridge the gap between security oversight and operational execution, creating a more efficient and secure cloud infrastructure management and compliance process. 

Key benefits include:

#### A simplified Configuration Management Database (CMDB) experience in AWS
Avoid investment in a dedicated external CMDB system or third-party tools. Access the inventory of resources in a single pane of glass, without accessing the AWS Management Console on each account and region. Filter resources by account, region, and fields that are specific to the resource such as IP address. If you tag consistently your resources - for example to map them to the application, owning team and environment - specify those tags to the dashboard and they will be displayed alongside the other resource-specific information, and used for filtering your configuration items. Manage and plan the upgrade of Amazon RDS DB engines and AWS Lambda runtimes.

#### Empower security and compliance practice
Track compliance of your AWS Config rules and conformance packs per service, region, account, resource. Identify resources that require compliance remediation and establish a process for continuous compliance review. Verify that your tagging strategy is consistently applied across accounts and regions.

#### Democratize compliance visibility
The AWS Config Dashboard helps security teams establish a compliance practice and offers visibility over security compliance to field teams, without them accessing AWS Config service or dedicated security tooling accounts. This creates a short feedback loop from security to field teams, keeps non-compliant resources to a minimum, and helps organizations establish a continuous compliance review process.


### Dashboard features

#### AWS Config compliance
- At-a-glance status of compliant and non-compliant resources and AWS Config rules.
- Month-by-month compliance trend for resources and AWS Config rules.
- Compliance breakdown by service, account, and region.
- Compliance tracking for AWS Config rules and conformance packs.
- Compliance score for AWS Config rules and conformance packs, and AWS resources.

#### Inventory management

![CRCD](images/ec2-inventory.png "AWS Config Dashboard, Configuration Items")

Inventory of Amazon EC2, Amazon EBS, Amazon S3, Amazon Relational Database Service (RDS) and AWS Lambda resources with filtering on account, region and resource-specific fields (e.g. IP addresses for EC2). Option to filter resources by the custom tags that you use to categorize workloads, such as Application, Owner and Environment. The name of the tags will be provided by you during installation.

#### AWS Config Aggregator Dashboard
Graphs from the AWS Config [Aggregator Dashboard](https://docs.aws.amazon.com/config/latest/developerguide/viewing-the-aggregate-dashboard.html#aggregate-compliance-dashboard) are added here, so that you can share it without managing read-only access to the AWS Config Console.

#### Tag compliance
Visualize the results of AWS Config Managed Rule [required-tags](https://docs.aws.amazon.com/config/latest/developerguide/required-tags.html). You can deploy this rule to find resources in your accounts that were not launched with your desired tag configurations by specifying which resource types should have tags and the expected value for each tag. The rule can be deployed multiple times in AWS Config. To display data on the dashboard, the rules must have a name that starts with `required-tags`.

![CRCD](images/tag-compliance-summary.png "AWS Config Dashboard, Tag Compliance")

## Architecture
The AWS Config Resource Compliance Dashboard (CRCD) solution can be deployed in standalone AWS accounts or AWS accounts that are members of an AWS Organization. In both cases, AWS Config is configured to deliver configuration files to a centralized Amazon S3 bucket in a dedicated Log Archive account.

There are two possible ways to deploy the AWS Config Dashboard on AWS Organizations. 

### Deploy in the Log Archive Account

You can deploy the dashboard resources in the same Log Archive account where your AWS Config configuration files are delivered. The architecture would look like this:


![CRCD](images/architecture-log-archive-account.png "AWS Config Dashboard: deployment on AWS Organization, Log Archive account")

### Deploy in a separate Dashboard Account
Alternatively, you can create a separate Dashboard account to deploy the dashboard resources. In this case, objects from the Log Archive bucket in the Log Archive account are replicated to another bucket in the Dashboard account.


![CRCD](images/architecture-dashboard-account.png "AWS Config Dashboard: deployment on AWS Organization, dedicated Dashboard account")

### Deploy on a standalone account
You can also deploy the dashboard in a standalone account with AWS Config enabled. This option may be useful for proof of concept or testing purposes. In this case, all resources are deployed within the same AWS account.


### Architecture details
An Amazon Athena table is used to extract data from the AWS Config configuration files delivered to Amazon S3. Whenever a new object is added to the bucket, the Lambda Partitioner function is triggered. This function checks if the object is an AWS Config configuration snapshot or configuration history file. If it is, the function adds a new partition to the corresponding Athena table with the new data. If the object is neither a configuration snapshot nor configuration history file, the function ignores it.

The solution provides Athena views, which are SQL queries that extract data from Amazon S3 using the schema defined in the Athena table. Finally, you can visualize the data in a QuickSight dashboard that uses these views through Amazon QuickSight datasets.

## Deployment
Deployment guide available at the [Cloud Intelligence Dashboards Framework workshops](https://catalog.workshops.aws/awscid/en-US/dashboards/additional/config-resource-compliance-dashboard).

## Upgrade
Upgrading from an older version? Read [this](./documentation/upgrade.md) first.

## Additional info
Other documentation is available [here](./documentation/README.md).

# Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

# License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.