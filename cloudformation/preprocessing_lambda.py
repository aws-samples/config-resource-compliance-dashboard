import boto3
import json
from datetime import datetime
import os
import re


# This regular expressions pattern is compatible with how ControlTower Config logs AND also with how Config Logs are stored in S3 in standalone account
# Structure for Config Snapshots: ORG-ID/AWSLogs/ACCOUNT-NUMBER/Config/REGION/YYYY/MM/DD/ConfigSnapshot/objectname.json.gz
# Object name follows this pattern: ACCOUNT-NUMBER_Config_REGION_ConfigSnapshot_TIMESTAMP-YYYYMMDDHHMMSS_RANDOM-TEXT.json.gz
# For example: 123412341234_Config_eu-north-1_ConfigSnapshot_20240306T122755Z_09c5h4kc-3jc7-4897-830v-d7a858325638.json.gz
PATTERN = r'^(?P<org_id>[\w-]+)?/?AWSLogs/(?P<account_id>\d+)/Config/(?P<region>[\w-]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<type>ConfigSnapshot|ConfigHistory)/[^//]+$'


def lambda_handler(event, context):
    glue = boto3.client('glue')

    # Get the table name from environment variable
    table_name = os.environ.get('DYNAMODB_TRACKING_TABLE_NAME', 'CRCDPreprocessingJobTracking')
    
    # Use the environment variable for the table name
    dynamodb = boto3.resource('dynamodb').Table(table_name)

    # this will be dynamic, hard coding for now
    DashboardBucketName = 'crcd-dashboard-bucket-058264555211-eu-north-1'
    
    records = event['Records']
    for record in records:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        # process object key
        match  = re.match(PATTERN, key)
        if not match:
            print(f'SKIPPING: Cannot match {key} as AWS Config file, skipping.')
            continue

        # Extract the filename from the full path
        filename = os.path.basename(key)
        # Remove the .json.gz extension if present
        filename = filename.replace('.json.gz', '')
        
        #timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        # run_id = f"s3-trigger-{timestamp}"
        #run_id = f"{filename}-{timestamp}"

        # Split by underscore and take the last two parts
        parts = filename.split('_')
        if len(parts) >= 2:
            timestamp_and_random = f"{parts[-2]}_{parts[-1]}"
        else:
            # Fallback: use the entire filename without extensions
            timestamp_and_random = filename
        
        run_id = timestamp_and_random
        
        # Record job start in DynamoDB
        dynamodb.put_item(
            Item={
                'source_file': key,
                'job_run_id': run_id,
                'status': 'STARTED',
                'start_time': datetime.now().isoformat(),
                'ttl': int((datetime.now().timestamp()) + (90 * 24 * 60 * 60))  # 90 days TTL
            }
        )
        
        # Start Glue job
        try:
            response = glue.start_job_run(
                JobName='crcd-config-file-processing-job',
                Arguments={
                    '--source_path': f"s3://{bucket}/{key}",
                    '--destination_path': f"s3://{DashboardBucketName}/",
                    '--CRCD_JOB_RUN_ID': run_id
                }
            )
            
            print(f"Started Glue job for bucket {bucket} on object {key} with run ID: {response['JobRunId']}")
            
        except Exception as e:
            print(f"Error starting Glue job for {key}: {str(e)}")
            raise
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed S3 event')
    }
