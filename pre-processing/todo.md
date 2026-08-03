# TODO

## 1. Add configurable name parameters for all support Lambda functions

Every support Lambda function must have a CloudFormation parameter for its name (under "Technical Parameters (DO NOT CHANGE)"), just like `LambdaSupportJobTriggerConfigurationName` does for the S3 notification Lambda. Currently missing for:
- `crcd-support-upload-preprocessing-script` (ScriptUploaderLambda)
- `crcd-support-ensure-ecs-service-role` (ECSServiceLinkedRoleLambda)

Each should have a parameter with a default value matching the current hardcoded name, a ParameterLabel, and the Lambda's `FunctionName` should reference the parameter.

## 2. Create a private VPC with VPC Endpoints for Fargate tasks

The Fargate task currently requires a public subnet with `assignPublicIp: ENABLED` to reach S3 and DynamoDB. This should be replaced with a fully private VPC created within the CloudFormation template, eliminating the need for user-provided networking parameters and removing public internet exposure.

Requirements:
- Private subnets only (no internet gateway, no NAT gateway, no public IPs)
- S3 Gateway Endpoint (free, for streaming Config files and writing output)
- DynamoDB Gateway Endpoint (free, for job tracking table updates)
- ECR VPC Interface Endpoints (for pulling container images): `ecr.api`, `ecr.dkr`, `com.amazonaws.region.s3` (needed by ECR for image layers)
- CloudWatch Logs Interface Endpoint (for container log delivery)
- Security group allowing only outbound HTTPS (443) to the VPC endpoints
- Remove `FargateSubnetIds`, `FargateSecurityGroupIds` parameters from the template (no longer user-provided)
- Change `assignPublicIp` to `DISABLED` in the Producer Lambda's `run_task()` call

## 3. Review CloudWatch Logs retention configuration

CloudWatch log groups must not grow indefinitely. Verify that all log groups in the template have an appropriate `RetentionInDays` setting. Current log groups to check:
- `/aws/lambda/crcd-support-configure-s3-notification-preprocessing-job` (14 days)
- `/aws/lambda/${PreProcessingLambdaProducerName}` (14 days)
- `/ecs/crcd-preprocessing-task` (14 days)
- `/aws/lambda/crcd-support-upload-preprocessing-script` (14 days)
- `/aws/lambda/crcd-support-ensure-ecs-service-role` (14 days)

Consider whether 14 days is sufficient for debugging production issues, or if some log groups (e.g. the Fargate task logs) should retain longer for audit/troubleshooting. The support Lambdas run only once at deploy time, so short retention is fine for those.

## 4. Lambda Producer should copy small files directly instead of launching Fargate

If the source AWS Config file is below a size threshold, the Producer Lambda should copy/move the S3 object directly to the destination bucket without launching a Fargate task. This avoids the ~30 second Fargate startup overhead for files that don't need splitting.

Requirements:
- Determine the size threshold (e.g. files under 32MB uncompressed don't need splitting — they already fit within Athena's limit)
- Use the S3 object size from the event record or a HeadObject call to decide
- If below threshold: copy the object directly to the destination bucket (same directory structure)
- If above threshold: launch the Fargate task as currently implemented
- Additional IAM permissions for the Producer Lambda role will be needed (s3:GetObject on Log Archive, s3:PutObject on Dashboard bucket) — evaluate when implementing

## 5. Find a better name for `config_stream_splitter.py`

The script name should clearly communicate what it does in the context of the CRCD project. Consider names that reflect its purpose (preprocessing AWS Config files for Athena compatibility) rather than the implementation detail (streaming/splitting).

## 6. TODO comments from crcd-config-preprocessing.yaml

- `ParameterGroups / LogArchiveBucketName`: TODO ask for the LogArchive account id and validate it is THE CURRENT account - LogArchiveAccountId
- `ParameterGroups / LogArchiveBucketName`: TODO support KMS encrypted log archive bucket, see if additional permissions are needed at all - LogArchiveBucketKmsKeyArn
- `ParameterGroups / Pre-processing job configuration`: TODO remove default: "Dashboard bucket - destination bucket of the pre-processing job and source of data for the dashboard"
- `DashboardBucketNamePrefix`: TODO if customer installs on Log Archive account, this will be the Dashboard bucket. If the customer installs on a dedicated Dashboard account, this will be confusing. Think about a better name.
- `DashboardBucketNamePrefix / AllowedPattern`: TODO remove length of region and 12 digit account number
- `DashboardBucket / BucketEncryption`: TODO bucket encryption must be KMS if the original Log Archive bucked is KMS encrypted
- `DashboardBucket / Metadata`: TODO see if you need this (cfn_nag rules_to_suppress for W35 and W51)

```
#cfn_nag:
      #  rules_to_suppress:
      #    - id: W35
      #      reason: "We accept Athena query result bucket has no access logging"
      #    - id: W51
      #      reason: "We accept Athena query result bucket has no bucket policy"
```
