# Local Testing Guide

This guide walks you through testing the CRCD preprocessing script locally against your real AWS Config files.

## Prerequisites

- Python 3.12+
- `pip` package manager
- AWS CLI configured (to download files from S3)
- Enough disk space for the input file and output files

## Download these files

Download the following files from this folder and save them to a local directory called `crcd-local-test-pre-processing`:

| File | Description |
|------|-------------|
| [`test_local.py`](./test_local.py) | The preprocessing script you will run locally |
| [`requirements.txt`](./requirements.txt) | Python dependencies needed by the script |




## Step 1: Install dependencies

```bash
cd crcd-local-test-pre-processing
pip install -r requirements.txt
```

## Step 2: Download a Config file from your S3 bucket

Pick a large ConfigHistory file from your Log Archive bucket. These are typically found at:

**Standalone account:**
```
s3://<log-archive-bucket>/AWSLogs/<account-id>/Config/<region>/<year>/<month>/<day>/ConfigHistory/
```

**AWS Organization:**
```
s3://<log-archive-bucket>/<org-id>/AWSLogs/<account-id>/Config/<region>/<year>/<month>/<day>/ConfigHistory/
```

To find the largest files in your bucket, replace:
- `<YOUR-CONFIG-BUCKET>` with the name of your S3 bucket where AWS Config records are delivered.
- `<YOUR-S3-PREFIX>` with the S3 prefix where you know large Config files exist. Be as narrow as possible — the more specific the prefix, the faster the query returns. A broad prefix (e.g. `AWSLogs/`) will scan every object under it and can take a very long time on buckets with millions of objects. Examples:
  - Standalone, specific region and day: `AWSLogs/123456789012/Config/eu-central-1/2026/8/2/ConfigHistory/`
  - Organization, specific account and region: `o-abc123def4/AWSLogs/123456789012/Config/eu-central-1/`
  - Organization, specific account (all regions): `o-abc123def4/AWSLogs/123456789012/Config/`
- `<YYYY-MM-DD>` with a recent date. Yesterday should be enough and return files quickly. You can always use an earlier date if you don't find files, but don't go too far in the past or the command will take a long time.
- `<SIZE-IN-BYTES>` with the minimum compressed file size to filter on. The `Size` field in S3 is the **gzip-compressed** size — the uncompressed JSON will be much larger. As a reference, a compressed file of just 500 KB can expand to over 45 MB uncompressed, which already exceeds Athena's 32 MB limit. Adjust this value based on your needs:
  - Use a low threshold (e.g. `300000` = ~300 KB) to find files that are just barely over the Athena limit.
  - Use a higher threshold (e.g. `5000000` = ~5 MB) if you want to test with the largest files in your bucket.

```bash
aws s3api list-objects-v2 \
  --bucket <YOUR-CONFIG-BUCKET> \
  --prefix "<YOUR-S3-PREFIX>" \
  --query 'Contents[?LastModified>=`<YYYY-MM-DD>` && Size>`<SIZE-IN-BYTES>`].[Key,Size,LastModified]' \
  --output table
```

Create a folder under `crcd-local-test-pre-processing` to store your source files:

**macOS/Linux:**
```bash
mkdir -p ./source-files
```

**Windows (PowerShell):**
```powershell
mkdir source-files
```

Download one to your local machine:

```bash
aws s3 cp s3://<log-archive-bucket>/AWSLogs/<account-id>/Config/<region>/<YYYY>/<MM>/<DD>/ConfigSnapshot/<filename>.json.gz ./source-files/
```

Choose the largest file you can find — ideally one that has caused Athena query failures in the past.

## Step 3: Run the preprocessing script

```bash
python test_local.py ./source-files/<filename>.json.gz ./output-files
```

The script will print progress as it processes:

```
Input: ./source-files/058264555211_Config_eu-central-1_ConfigSnapshot_20260801T083010Z_6292fd47-f519-4323-9b79-6c3cbebe1b2e.json.gz
Output dir: ./output-files
Input size: 45.2 MB (compressed)
Batch size: 500 items per file
Source: account=058264555211, region=eu-central-1, timestamp=20260801T083010Z
Progress: 5000 items read, 10 files written
Progress: 10000 items read, 20 files written
...

Done:
  Items processed: 50000
  Files written: 100
  Items with errors: 0
  Output dir: ./output-files
```

## Step 4: Check the results

Verify the output:

**macOS/Linux:**
```bash
# Count output files
ls ./output-files/*.json.gz | wc -l

# Check the size of output files (should all be well under 32MB uncompressed)
ls -lh ./output-files/

# Inspect one file to verify it has the correct structure
gunzip -c ./output-files/<any-file>.json.gz | python -m json.tool | head -20
```

**Windows (PowerShell):**
```powershell
# Count output files
(Get-ChildItem ./output-files/*.json.gz).Count

# Check the size of output files (should all be well under 32MB uncompressed)
Get-ChildItem ./output-files/ | Format-Table Name, Length

# Inspect one file to verify it has the correct structure
python -c "import gzip, json, sys; data=json.loads(gzip.open(sys.argv[1],'rt').read()); print(json.dumps(data, indent=4)[:2000])" ./output-files/<any-file>.json.gz
```

Each output file should have this structure:

```json
{
    "fileVersion": "1.0",
    "configSnapshotId": "...",
    "configurationItems": [...]
}
```

The `configurationItems` array should contain up to 500 items per file.

## Step 5: (Optional) Verify no data was lost

Compare the total number of items in the original file against the sum of items across all output files:

**macOS/Linux:**
```bash
# Count items in original file (this may take a while for large files)
gunzip -c ./source-files/<filename>.json.gz | python -c "
import json, sys
data = json.load(sys.stdin)
print(f'Original items: {len(data[\"configurationItems\"])}')"

# Count items across all output files
for f in ./output-files/*.json.gz; do
  gunzip -c "$f"
done | python -c "
import json, sys
total = 0
for line in sys.stdin:
    try:
        data = json.loads(line)
        total += len(data['configurationItems'])
    except: pass
print(f'Output items: {total}')"
```

**Windows (PowerShell):**
```powershell
# Count items in original file (this may take a while for large files)
python -c "import gzip, json; data=json.loads(gzip.open('./source-files/<filename>.json.gz','rt').read()); print(f'Original items: {len(data[\"configurationItems\"])}')"

# Count items across all output files
python -c "import gzip, json, glob; total=sum(len(json.loads(gzip.open(f,'rt').read())['configurationItems']) for f in glob.glob('./output-files/*.json.gz')); print(f'Output items: {total}')"
```

Both numbers must match exactly.

## Expected file naming

Output files follow this naming convention:

```
<account-id>_Config_<region>_<type>_<timestamp>_<sequence>_<random>.json.gz
```

For example:
```
058264555211_Config_eu-central-1_ConfigSnapshot_20260801T083010Z_00001_a3f8b2c1d4e5.json.gz
058264555211_Config_eu-central-1_ConfigSnapshot_20260801T083010Z_00002_7b9e1f3a2c8d.json.gz
```

The account ID, region, type, and timestamp are preserved from the source file so you can correlate input and output.

## Supported input file formats

The script handles both AWS Config file types:

| Type | Filename pattern |
|------|-----------------|
| ConfigSnapshot | `<AccountId>_Config_<Region>_ConfigSnapshot_<Timestamp>_<UUID>.json.gz` |
| ConfigHistory | `<AccountId>_Config_<Region>_ConfigHistory_<ResourceType>_<StartTime>_<EndTime>_<Sequence>.json.gz` |

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Input filename does not match expected pattern" | The file was renamed or doesn't follow AWS Config naming | Use the original filename as delivered by AWS Config |
| "Items with errors" > 0 | Individual items failed to serialize | Check the error messages in the output for details |
| Script uses too much memory | Should not happen — the script streams the file | Report this as a bug with the file size and item count |

## Step 6: Upload output files to S3 and verify with Athena

Upload the output files to the S3 bucket where your CRCD dashboard reads AWS Config data. Preferably use a test environment where you have the CRCD dashboard deployed. If you do not have a test environment for the dashboard, use a made-up account ID in `<YOUR-CONFIG-BUCKET>`, for example `111222333444`, in the command below. The files will be indexed under that account ID and you can easily remove the entire folder afterwards.

S3 creates intermediate folders automatically — you don't need to create the prefix path beforehand.

```bash
aws s3 cp ./output-files/ s3://<YOUR-CONFIG-BUCKET>/AWSLogs/<account-id>/Config/<region>/<YYYY>/<MM>/<DD>/ConfigHistory/ --recursive
```

Once the files are uploaded, run an Athena query against the CRCD table to verify the data is readable and no longer triggers the 32 MB row limit error:

```sql
SELECT
  configurationItem.resourceId,
  configurationItem.resourceType,
  configurationItem.awsRegion,
  configurationItem.configurationItemStatus
FROM cid_crcd_config
CROSS JOIN UNNEST(configurationitems) t (configurationItem)
WHERE configurationItem.resourceType = 'AWS::EC2::Instance'
  AND accountid = '<account-id>'
  AND region = '<region>'
  AND dt = '<YYYY-M-D>'
LIMIT 20;
```

You can also query for a specific resource type, for example Lambda functions:

```sql
SELECT
  configurationItem.resourceId,
  configurationItem.arn,
  json_extract_scalar(configurationItem.configuration, '$.functionName') AS FunctionName,
  json_extract_scalar(configurationItem.configuration, '$.runtime') AS Runtime,
  configurationItem.configurationItemStatus
FROM cid_crcd_config
CROSS JOIN UNNEST(configurationitems) t (configurationItem)
WHERE configurationItem.resourceType = 'AWS::Lambda::Function'
  AND accountid = '<account-id>'
  AND region = '<region>'
  AND dt = '<YYYY-M-D>'
LIMIT 20;
```

Or query all resource types at once:

```sql
SELECT
  accountid,
  region,
  configurationItem.resourceType,
  configurationItem.resourceId,
  configurationItem.arn,
  configurationItem.configurationItemStatus
FROM cid_crcd_config
CROSS JOIN UNNEST(configurationitems) t (configurationItem)
WHERE accountid = '<account-id>'
  AND region = '<region>'
  AND dt = '<YYYY-M-D>'
LIMIT 20;
```

If these queries return results without errors, the preprocessing worked correctly and Athena can read the split files.


## Step 7: Cleanup

If you uploaded the output files to a made-up account (e.g. `111222333444`):

Delete the prefix from the S3 bucket:

**Standalone account:**
```bash
aws s3 rm s3://<YOUR-CONFIG-BUCKET>/AWSLogs/111222333444/ --recursive
```

**AWS Organization:**
```bash
aws s3 rm s3://<YOUR-CONFIG-BUCKET>/<org-id>/AWSLogs/111222333444/ --recursive
```

Remove the corresponding Athena partition:

```sql
ALTER TABLE <your-athena-table>
DROP IF EXISTS PARTITION (accountid='111222333444', region='<region>', dt='<YYYY-MM-DD>');
```

Remember that MM and DD use a single digit if the day or month is below 10, e.g. `2026-8-2` for the 2nd of Agust 2026.
