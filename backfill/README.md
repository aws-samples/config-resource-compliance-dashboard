# Config Resource Compliance Dashboard (CRCD) - Backfill Process

## Overview

The CRCD Backfill feature processes historical AWS Config data that already exists in your S3 bucket and creates the necessary Athena/Glue partitions for it. This is essential when you have existing AWS Config data that wasn't automatically partitioned when the dashboard was first deployed.

## Architecture
The solution uses a two-stage process:
1. **Producer Function**: Scans the dashboard S3 bucket to identify AWS Config prefixes
2. **Worker Function**: Creates Athena/Glue partitions for the identified files
3. **SQS Queue**: Coordinates the workflow between producer and worker functions


TODO: add image

The Producer Function scans your Amazon S3 dashboard bucket and finds all prefixes related to AWS Config. The prefix structure of an AWS Config file is as follows (for an AWS Config Snapshot): `ORG-ID/AWSLogs/ACCOUNT-NUMBER/Config/REGION/YYYY/MM/DD/ConfigSnapshot/objectname.json.gz`. For performance reasons, this function identifies all AWS Config prefixes down to REGION. These prefixes are sent to an SQS queue that will trigger the Worker Function to add them to the dashboard data.


The Backfill worker function is triggered by SQS. The SQS payload to the function is an AWS Config prefix until the region. This function will create full AWS Config prefixes adding the `YYYY/MM/DD/(ConfigSnapshot/ConfigHistory/)` part until a configurable time in the past. For each complete prefix, the function will check whether that prefix exists on the S3 Dashboard bucket, in which case the Athena partition will be created (if not existing).

The backfill process will generate partitions for these AWS Config prefixes:
1. All AWS Config history records
2. AWS Config snapshot records on all accounts an regions whose date is the last day of the month, from the last day of the month until 5 months ago
3. Config snapshot records on all accounts an regions whose date is within the last 5 days



## Prerequisites

- CRCD Dashboard must already be deployed
- AWS Config historical data exists in your S3 bucket
- Deploy this template in the same AWS account and region as your CRCD resources

## Deployment Instructions

TODO: refer to github

1. Navigate to the AWS CloudFormation console
2. Create a new stack using the `crcd-backfill-resources.yaml` template
3. Configure the following parameters:

### Required Parameters

| Parameter | Description | Example Value |
|-----------|-------------|---------------|
| **DashboardBucketName** | Name of the S3 bucket containing your AWS Config data | `my-config-dashboard-bucket` |
| **AthenaQueryResultBucketName** | S3 bucket for Athena query results (from CRCD stack outputs) | `crcd-athena-results-bucket-123456` |

### Optional Parameters

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| **AWSOrganizationID** | _(empty)_ | Your AWS Organization ID. Leave empty for standalone accounts |

4. Open the Worker function and confirm the parameters to the function

| Parameter | Default Value | Description |
|-----------|---------------|-------------|
| **PARTITION_CONFIG_SNAPSHOT_RECORDS** | `1` (i.e. enabled) | Pass `1` to create partitions for AWS Config snapshot files. Pass `0` to ignore them. |
| **PARTITION_CONFIG_HISTORY_RECORDS** | `1` (i.e. enabled) | Pass `1` to create partitions for AWS Config history files. Pass `0` to ignore them. |
| **CONFIG_HISTORY_TIME_LIMIT_MONTHS** | `12` | How long in the past (months) the function will go to generate partitions for AWS Config history records |
| **CONFIG_SNAPSHOT_TIME_LIMIT_MONTHS** | `6` | How long in the past (months) the function will go to generate partitions for AWS Config history records |

5. Open the Producer function and run it
   - The backfill process will start
   - Monitor CloudWatch logs for the Lambda functions
   - Check SQS queue metrics to track progress

6. Verify Results
   - Query your Athena tables to confirm historical data is accessible
   - Refresh your Quick Suite datasets dashboard to see historical data on the dashboard

## Important Notes

- This is a one-time operation for processing historical data
- The process may take several hours depending on the amount of historical data
- Resources can be deleted after successful backfill completion
- Ensure sufficient Lambda execution time and SQS message retention for large datasets