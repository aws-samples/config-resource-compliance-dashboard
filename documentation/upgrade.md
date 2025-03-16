# Upgrade Instructions
With the expection of the cases reported here, you should remove the dashboard completely and re-deploy the new version.


## Upgrade to 2.1.2

### From 2.1.1
You can keep the data pipeline resources, these were installed by CloudFormation, at the current version. You only need to redeploy the frontend resources with the `cid-cmd` tool.

#### Step 1: Enable Config history files on the Lambda Partitioner function
1. Open the Lambda Console on the AWS account and region where you deployed the dashboard.
1. Select the Lambda Partitioner function, it's called `crcd-config-file-partitioner`
1. Ensure the environemnt variables `PARTITION_CONFIG_SNAPSHOT_RECORDS` and `PARTITION_CONFIG_HISTORY_RECORDS` are both set to `1`.

#### Step 2: Uninstall the dashboard frontend with cid-cmd tool
1. On  the same AWS account and region , open Amazon CloudShell
1. Execute the following command to delete the dashboard:

```
cid-cmd delete --resources cid-crcd.yaml
```

* `cid-crcd.yaml` is the template file for the dashboard resources. Upload it to CloudShell if needed.

3. When prompted:
   - Select the `[cid-crcd] AWS Config Resource Compliance Dashboard (CRCD)` dashboard.
   - For each QuickSight dataset, choose `yes` to delete the dataset.
   - Accept the default values for the S3 Path for the Athena table.
   - Accept the default values for the four tags.
   - For each Athena view, choose `yes` to delete the dataset.

#### Step 3: Deploy the dashboard frontend again
Follow the installation steps to deploy the dashboard resources using the 'cid-cmd' tool. This is **Step 2** in case of Log Archive account deployment, or **Step 3** iin case of Dashboard account deployment.

#### Step 4: Optionally change the retention period of the Lambda Partitioner CloudWatch logs
Version 1.2.1 did not configure a retention period for the CloudWatch logs of the Lambda Partitioner function. From version 1.2.1, logs are kept for 14 days.

1. Open the CloudWatch Console on the AWS account and region where you deployed the dashboard.
1. Select Log Groups and find `/aws/lambda/crcd-config-file-partitioner`
1. Edit the log settings, change retention to 14 days, or the value that suits your needs.

### From older versions
You have to destroy the resources of the current versions and redeploy. When you removed the old versions, and before deploying v2.1.2, make sure to delete the CloudWatch log group of the Lambda Partitioner:
1. Log onto the AWS Console on the account and region where you deploy the dashboard, open the CloudWatch console.
1. Click on `Logs/Log groups`.
1. Find the log group called `/aws/lambda/cid-crcd-config-file-partitioner` or `/aws/lambda/crcd-config-file-partitioner`, depending on your version, select it.
1. Click on the `Actions` button and select `Delete log Group(s)`

The AWS Config Dashboard v2.1.2 creates the CloudWatch log group as a CloudFormation resource with a retention period, and will fail if the log group already exists.