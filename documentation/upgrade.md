# Upgrade Instructions
With the exception of the cases reported here, you should remove the dashboard completely and re-deploy the new version.

## Upgrade to v4.0.2

### Upgrade to v4.0.2 from v4.0.1
This version has a new `config_compliance` view.

1. Open AWS CloudShell on the Log Archive account, in the region where you deployed the dashboard.
1. Execute the following command:

```
 cid-cmd update \
   --recursive \
   --resources 'https://raw.githubusercontent.com/aws-samples/config-resource-compliance-dashboard/refs/heads/main/dashboard_template/cid-crcd.yaml' \
   --dashboard-id 'cid-crcd' \
   --athena-database 'cid_crcd_database' \
   --athena-workgroup 'crcd-dashboard'
```

3. The `cid-cmd` tool will ask you to confirm the values of parameters `tag1`, `tag2`, `tag3` and `tag4`. Their current value will be displayed.
4. The `cid-cmd` tool will then analyze each Athena view and identify an updated version of `config_compliance`.
     - **If `cid-cmd` does not analyze the views, make sure you used the option `--recursive` in the CLI command**
     - The changes will be highlighted in color, expect to see `configrulelist` being replaced by `configRuleList` within the first lines of the view definition.
     ```
      -    CROSS JOIN UNNEST(CAST(json_extract(configurationItem.configuration, '$.configrulelist') AS array(json))) u (rule))
      +    CROSS JOIN UNNEST(CAST(json_extract(configurationItem.configuration, '$.configRuleList') AS array(json))) u (rule))
     ```
5. Select `proceed and override`.
1. When prompted `[timezone] Please select timezone for datasets scheduled refresh.:` select the time zone for dataset scheduled refresh in your Region (it is already preselected). The tool will not find other updates for the Athena views. 
1. When prompted `Select taxonomy fields to add as dashboard filters and group by fields` select `Looks good` without adding taxonomy items. Taxonomy is not supported by the dashboard.
1. The tool will update the dashboard definition and terminate.

## Upgrade to v4.0.2 from earlier versions
You have to destroy the resources of the current versions and redeploy.

## Upgrade to v4.0.1
You have to destroy the resources of the current versions and redeploy.

## Upgrade to v4.0.0
You have to destroy the resources of the current versions and redeploy.

## Upgrade to v3.0.1
There are no functional changes over v3.0.0. The new version allows CRCD to be easier to install together with other CID dashboards, if you are already running v3.0.0 there is no reason to upgrade.

## Upgrade to v3.0.0

### Upgrade to v3.0.0 from v2.1.1 or v2.1.0
You only need to redeploy the frontend resources with the `cid-cmd` tool. You can keep the data pipeline resources that were installed by CloudFormation, as is.

#### Step 1: Enable AWS Config history files on the Lambda Partitioner function
1. Open the Lambda Console on the AWS account and region where you deployed the dashboard.
1. Select the Lambda Partitioner function, it's called `crcd-config-file-partitioner`.
1. Ensure the [environment variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html) `PARTITION_CONFIG_SNAPSHOT_RECORDS` and `PARTITION_CONFIG_HISTORY_RECORDS` are both set to `1`.

#### Step 2: Uninstall the dashboard frontend with the cid-cmd tool
1. On the same AWS account and region, open AWS CloudShell
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
Follow the installation steps to deploy the dashboard resources using the `cid-cmd` tool. This is either **Step 2** in case of Log Archive account deployment, or **Step 3** in case of Dashboard account deployment.

#### Step 4: Optionally change the retention period of the Lambda Partitioner CloudWatch logs
AWS Config Dashboard v2.2.1 and v2.1.0 did not configure a retention period for the CloudWatch logs of the Lambda Partitioner function. From version 3.0.0, logs are kept for 14 days. We recommend that you configure a retention period for your logs. Follow these steps:

1. Open the CloudWatch Console on the AWS account and region where you deployed the dashboard.
1. Click on `Logs/Log groups`.
1. Find the log group called `/aws/lambda/crcd-config-file-partitioner`.
1. Edit the log settings, change retention to 14 days, or the value that suits your needs.

### Upgrade to v3.0.0 from older versions
You have to destroy the resources of the current versions and redeploy. After you removed the old versions, and before deploying v3.0.0, make sure to delete the CloudWatch log group of the Lambda Partitioner:
1. Log onto the AWS Console on the account and region where you deploy the dashboard, open the CloudWatch console.
1. Click on `Logs/Log groups`.
1. Find the log group called `/aws/lambda/crcd-config-file-partitioner` and select it.
1. Click on the `Actions` button and select `Delete log group(s)`.

The AWS Config Dashboard v3.0.0 creates the CloudWatch log group as a CloudFormation resource with a retention period, the installation will fail if the log group already exists.