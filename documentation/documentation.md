# Additional Information

## Amazon S3 prefixes for AWS Config files

The dashboard uses these sources to get the inventory of resources and their compliance with AWS Config Rules and Conformance Packs: AWS Config configuration history and configuration snapshot files. Check this [blog post](https://aws.amazon.com/blogs/mt/configuration-history-configuration-snapshot-files-aws-config/) for more on the difference between AWS Config configuration history and configuration snapshot files.


The solution supports the following ways of activating AWS Config:
1. Manual setup on standalone AWS accounts.
1. Deployment by AWS Control Tower on AWS Organizations.

These options have different ways of structuring the prefixes of the AWS Config files on Amazon S3. They are defined below, and the Lambda Partitioner function supports all of them.

**Verify that your setup is compatible with these Amazon S3 prefixes.** If not, the Lambda Partitioner function will not be able to recognize objects as valid AWS Config files and will discard them. As a consequence, your Athena table will be empty.


### Supported AWS Config prefixes on Amazon S3

#### Manual AWS Config setup 
`AWSLogs/ACCOUNT-ID/Config/REGION/YYYY/MM/DD/ConfigSnapshot/ACCOUNT-ID_Config_REGION_ConfigSnapshot_TIMESTAMP_RANDOM.json.gz`

`AWSLogs/ACCOUNT-ID/Config/REGION/YYYY/MM/DD/ConfigHistory/ACCOUNT-ID_Config_REGION_ConfigHistory_RESOURCE-ID_TIMESTAMP_RANDOM.json.gz`

#### AWS Control Tower deployment
`AWS-ORGANIZATION-ID/AWSLogs/ACCOUNT-ID/Config/REGION/YYYY/MM/DD/ConfigSnapshot/ACCOUNT-ID_Config_REGION_ConfigSnapshot_TIMESTAMP_RANDOM.json.gz`

`AWS-ORGANIZATION-ID/AWSLogs/ACCOUNT-ID/Config/REGION/YYYY/MM/DD/ConfigHistory/ACCOUNT-ID_Config_REGION_ConfigHistory_RESOURCE-ID_TIMESTAMP.json.gz`

Where:
* `AWS-ORGANIZATION-ID` is the identifier of your AWS Organization.
* `ACCOUNT-ID` is the 12-digit AWS Account number, e.g. 123412341234.
* `REGION` identifies an AWS region, e.g. us-east-1.
* `YYYY/MM/DD` represents a date, e.g. 2024/04/18.
* `TIMESTAMP` is a full timestamp, e.g. 20240418T054711Z.
* `RESOURCE-ID` identifies the resource affected by the ConfigHistory record, e.g. AWS::Lambda::Function.
* `RANDOM` is a sequence of random character, e.g. a970aeff-cb3d-4c4e-806b-88fa14702hdb.

