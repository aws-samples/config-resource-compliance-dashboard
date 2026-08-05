# AWS Config Resource Compliance Dashboard - Preprocessing

## Problem

AWS Config generates snapshot files that contain all tracked resource configurations for an AWS account and region in a single line of a JSON file. In large environments, these files can contain tens or hundreds of thousands of Configuration Items (CI) and result in a file that is several MB in size.

AWS Athena has a hard limit of 32 MB per row of data. When a Config file exceeds this limit, every Athena query that touches that file will fail. Even a single oversized file makes the entire dataset unreliable for querying.

## Solution

This preprocessing pipeline automatically splits large AWS Config files into smaller files that stay well within Athena's 32 MB limit. It runs as a serverless Fargate task triggered by S3 events whenever a new Config file is delivered to the Log Archive bucket.

Key design decisions:
- **Streaming processing** - Uses `ijson` to parse files incrementally, holding only one batch in memory at a time. Memory usage stays constant regardless of input file size.
- **Batched output** - Each output file contains up to 500 configuration items, maintaining the same JSON structure as the original file (`fileVersion`, `configSnapshotId`, `configurationItems`).
- **Filename correlation** - Output files preserve the account ID, region, type, and timestamp from the source file, making it easy to trace output back to input.
- **Zero data loss** - Items are processed sequentially and written atomically to S3. The job tracks progress in DynamoDB.
- **Fully automated deployment** - A single CloudFormation template creates all resources. No Docker builds, no manual steps.

## Architecture


![CRCD Preprocessing Architecture](../images/pre-processing-architecture.png "AWS Config Dashboard, Preprocessing Architecture")

The flow of data is as follows:
1. **New Config record** lands in the source S3 bucket, the AWS Config Logs bucket.
2. **S3 event notification** triggers the Preprocessing Producer Lambda.
3. **Producer Lambda** checks the compressed file size:
   - **Below threshold** (< 300 KB): copies the file directly to the Dashboard Bucket.
   - **Above threshold** (>= 300 KB): launches a Fargate task.
4. **Fargate task** streams the large file, splits it into files of 500 `configurationItems` each, and writes them to the Dashboard Bucket.
5. **DynamoDB** tracks job status (STARTED → COMPLETED/FAILED) for both paths.

---

# AWS Config Snapshot File Structure

This section describes the structure of the AWS Config snapshot JSON files that serve as input for the pre-processing pipeline.

## File Naming Convention

```
<AccountId>_Config_<Region>_ConfigSnapshot_<Timestamp>_<SnapshotId>.json
```

Example: `730335424115_Config_eu-central-1_ConfigSnapshot_20260717T083010Z_6292fd47-f519-4323-9b79-6c3cbebe1b2e.json`

## Top-Level Fields

| Field | Description |
|-------|-------------|
| `fileVersion` | Schema version (e.g. `"1.0"`) |
| `configSnapshotId` | Unique ID for this snapshot delivery |
| `configurationItems` | Array of all tracked resource configurations |

## Configuration Item Structure

Each item in the `configurationItems` array contains:

| Field | Description |
|-------|-------------|
| `relatedEvents` | Associated AWS events (usually empty) |
| `relationships` | Relationships to other resources |
| `configuration` | The actual resource configuration (varies per resource type) |
| `supplementaryConfiguration` | Extra config data beyond the primary configuration |
| `tags` | Resource tags as key-value pairs |
| `configurationItemVersion` | Item schema version (e.g. `"1.3"`) |
| `configurationItemCaptureTime` | ISO timestamp when the config was captured |
| `configurationStateId` | Numeric state identifier |
| `awsAccountId` | The owning AWS account |
| `configurationItemStatus` | Status like `OK`, `ResourceDiscovered` |
| `resourceType` | AWS resource type (e.g. `AWS::Cassandra::Keyspace`, `AWS::CodeDeploy::DeploymentConfig`) |
| `resourceId` | Resource identifier |
| `resourceName` | Human-readable resource name |
| `ARN` | Full ARN of the resource |
| `awsRegion` | Region (e.g. `eu-central-1`) |
| `availabilityZone` | AZ or `Regional` / `Not Applicable` |
| `configurationStateMd5Hash` | MD5 hash of the configuration state |
| `resourceCreationTime` | (optional) When the resource was created |

When AWS Config generates a snapshot file, it creates one single YAML row containing all the resources and their compliance status in the AWS account/Region where it runs. This means the `configurationItems` array can contain potentially contain millions of items and the YAML file can have a size of several MBytes.


## Notes

- The file is a single-line JSON (no pretty-printing), which is typical for Config snapshot deliveries to S3.
- The `configuration` field is polymorphic — its shape depends entirely on the `resourceType`. It will contain every `resourceType` supported by AWS Config that is also a real resource on the AWS account and region where the snapshot is generated.
- Resource types found in the sample file include:
  - `AWS::Cassandra::Keyspace`
  - `AWS::AppConfig::DeploymentStrategy`
  - `AWS::AppConfig::Extension`
  - `AWS::CodeDeploy::DeploymentConfig`
  - `AWS::Athena::WorkGroup`
  - `AWS::CloudFormation::Stack` (PCI-DSS conformance pack with many Config rules)

# AWS Athena Limit
AWS Athena has a **hard limit of 32 MB** for each row of data it can process. Because AWS Config can produce snapshot files where a single configuration item exceeds Athena's 32 MB per-row hard limit, Athena queries will fail.

Even if an account has a single history file exceeding the limit, Athena queries will fail every time the query has to read that file, making it unpredictable to utilize the data generated by AWS Config.

# The Need of Pre-Processing
Data must be pre-processed to split or reduce oversized rows. The idea is to ingest a large file and create multiple output files that have the same structure as the original file:


```
{
  "fileVersion": "1.0",
  "configSnapshotId": "6292fd47-f519-4323-9b79-6c3cbebe1b2e",
  "configurationItems": []
}
```

But where the array `configurationItems` contains a subset of the items, making sure each processed file is within the hard limit of 32MB.

For example, if the original file contains 10000 items and is above the 32MB limit, the pre-processing function will generate 20 files each with 500 items. More sophisticated ways os splitting the original file may exist.