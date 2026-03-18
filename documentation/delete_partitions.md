# Delete AWS Glue/Athena partitions belonging to an AWS account

Use this guide after the deployment of the AWS Config Resource Compliance Dashboard if you do not want AWS Config files for a specific account to be indexed and displayed on the dashboard.


## Step 1: Stop creating partitions for AWS Config files belonging to an AWS account
First, you have to modify the partitioning logic to exclude the AWS account(s) that you do not want to be displayed on the dashboard.

### Modify the Lambda Partitioner to exclude the account
1. Open the CRCD Lambda Partitioner function in the AWS Lambda console (same AWS account and Region where you deployed the dashboard resources).
1. Go to **Configuration**, **Environment variables**, click **Edit**.
1. Add a new environment variable:
   - **Key**: `EXCLUDED_ACCOUNTS`
   - **Value**: a comma-separated list of the account IDs you want to exclude, e.g. `111111111111,222222222222`
1. Go to the **Code** tab to add the exclusion logic.
   1. Find this part of the code:
      ```
      accountid = match.groupdict()['account_id']
      region = match.groupdict()['region']
      date = '{year}-{month}-{day}'.format(**match.groupdict())
      table = CRCD_TABLE_NAME # Athena table for Config History and Snapshot records
      ```
   1. Add this code **under** the line: `accountid = match.groupdict()['account_id']`:
      ```
      # Account exclusion logic
      if accountid in os.environ['EXCLUDED_ACCOUNTS']:
        logger.info(f'SKIPPING: Account {accountid} is in the excluded list.')
        return {
            'statusCode': 200,
            'body': 'Account is in the excluded list.'
        }
      ```
1. Save and deploy the Lambda function.
1. You can verify the account is excluded by checking the CloudWatch logs of the function for a log message like this (where `111111111111` is the excluded account): "SKIPPING: Account 111111111111 is in the excluded list."

## Step 2: Delete all AWS Glue partitions belonging to an AWS account
Now you can remove the AWS Glue partitions that were created in the meantime. You have to repeat this part of the procedure for each AWS account.

If you want to retrieve all partitions for an account, run this AWS CLI command on the AWS account and Region where you deployed the dashboard resources. Replace `XXXXXX` with your account number.
   ```
   aws glue get-partitions \
   --database-name cid_crcd_database \
   --table-name cid_crcd_config \
   --expression "accountid='XXXXXX'" \
   --query "Partitions[*].Values" \
   --output table
   ```

### Remove partitions belonging to an account
1. Save the **Deletion CLI script** below to a local file called `crcd_delete_account_partitions.sh`.
1. Edit the file's **Configuration** section to specify the AWS account number whose partitions must be deleted, and the Region where the AWS Glue table is located.
1. Open the AWS CloudShell on the AWS account and Region where you deployed the dashboard resouces.
1. Upload `crcd_delete_account_partitions.sh` to CloudShell.
1. Make the script file executable:
   ```
   chmod +x crcd_delete_account_partitions.sh
   ```
1. Run the script (will show a preview and ask for confirmation before deleting):

   ```
   ./crcd_delete_account_partitions.sh
   ```


## Deletion CLI script

This is a complete script that loads the AWS Glue partitions belonging to an account and deletes them in batches of 25.

```
#!/bin/bash
# ============================================================
# crcd_delete_account_partitions.sh
# Deletes all Glue partitions matching a given accountid
# Partition key order: accountid, dt, region, datasource
# ============================================================

set -euo pipefail

# ── Configuration ─ Edit the fields below ────────────────────
DATABASE_NAME="cid_crcd_database"
TABLE_NAME="cid_crcd_config"
ACCOUNT_FILTER="XXXXXX"  # Set your AWS account id
AWS_REGION="eu-west-1"   # Set your Glue catalog region
BATCH_SIZE=25
# ─────────────────────────────────────────────────────────────

echo "🔍 Fetching all partitions for accountid='${ACCOUNT_FILTER}'..."

ALL_PARTITIONS="[]"
NEXT_TOKEN=""

# ── Paginate through all results ─────────────────────────────
while true; do
  if [ -z "$NEXT_TOKEN" ]; then
    RESPONSE=$(aws glue get-partitions \
      --region "$AWS_REGION" \
      --database-name "$DATABASE_NAME" \
      --table-name "$TABLE_NAME" \
      --expression "accountid='${ACCOUNT_FILTER}'" \
      --output json)
  else
    RESPONSE=$(aws glue get-partitions \
      --region "$AWS_REGION" \
      --database-name "$DATABASE_NAME" \
      --table-name "$TABLE_NAME" \
      --expression "accountid='${ACCOUNT_FILTER}'" \
      --next-token "$NEXT_TOKEN" \
      --output json)
  fi

  # Accumulate partition values
  PAGE_PARTITIONS=$(echo "$RESPONSE" | jq '[.Partitions[].Values]')
  ALL_PARTITIONS=$(jq -n --argjson a "$ALL_PARTITIONS" --argjson b "$PAGE_PARTITIONS" '$a + $b')

  # Check for next page
  NEXT_TOKEN=$(echo "$RESPONSE" | jq -r '.NextToken // empty')
  [ -z "$NEXT_TOKEN" ] && break

  echo "  ↳ Paginating... fetched $(echo "$ALL_PARTITIONS" | jq 'length') partitions so far"
done

TOTAL=$(echo "$ALL_PARTITIONS" | jq 'length')
echo "✅ Found ${TOTAL} partitions to delete."

if [ "$TOTAL" -eq 0 ]; then
  echo "Nothing to delete. Exiting."
  exit 0
fi

# ── Dry-run preview ──────────────────────────────────────────
echo ""
echo "📋 Partitions to be deleted (accountid | dt | region | datasource):"
echo "$ALL_PARTITIONS" | jq -r '.[] | @tsv' | column -t -s $'\t'
echo ""

# ── Confirmation prompt ──────────────────────────────────────
read -r -p "⚠️  Are you sure you want to delete all ${TOTAL} partitions? [yes/N]: " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Aborted. No partitions were deleted."
  exit 0
fi

# ── Batch delete in groups of 25 ─────────────────────────────
echo ""
echo "🗑️  Starting batch deletion..."

DELETED=0
INDEX=0

while [ "$INDEX" -lt "$TOTAL" ]; do
  # Slice a batch of up to 25
  BATCH=$(echo "$ALL_PARTITIONS" | jq --argjson start "$INDEX" --argjson size "$BATCH_SIZE" \
    '.[$start:$start+$size] | [.[] | {"Values": .}]')

  BATCH_COUNT=$(echo "$BATCH" | jq 'length')

  RESULT=$(aws glue batch-delete-partition \
    --region "$AWS_REGION" \
    --database-name "$DATABASE_NAME" \
    --table-name "$TABLE_NAME" \
    --partitions-to-delete "$BATCH" \
    --output json)

  # Check for errors returned per-partition
  ERRORS=$(echo "$RESULT" | jq '.Errors | length')
  if [ "$ERRORS" -gt 0 ]; then
    echo "  ⚠️  ${ERRORS} error(s) in this batch:"
    echo "$RESULT" | jq '.Errors[] | "  ✗ \(.PartitionValues | join("/")): \(.ErrorDetail.ErrorMessage)"' -r
  fi

  DELETED=$((DELETED + BATCH_COUNT - ERRORS))
  INDEX=$((INDEX + BATCH_SIZE))

  echo "  ✓ Processed batch: $((INDEX < TOTAL ? INDEX : TOTAL))/${TOTAL} partitions"
done

echo ""
echo "🎉 Done! Successfully deleted ${DELETED}/${TOTAL} partitions from '${TABLE_NAME}'."
```