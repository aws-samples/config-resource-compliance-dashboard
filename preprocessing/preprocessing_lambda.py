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

# Objects below this threshold can safely be transfered directly to the destination bucket
DEFAULT_CONFIG_OBJECT_SIZE_THRESHOLD = 300000

def lambda_handler(event, context):
    # Get the table name from environment variable
    table_name = os.environ["DYNAMODB_TRACKING_TABLE_NAME"]
    
    # Use the environment variable for the table name
    dynamodb = boto3.resource('dynamodb').Table(table_name)

    # Gets more environment variables
    dashboard_bucket_name = os.environ["DASHBOARD_BUCKET_NAME"]
    preprocessing_glue_job = os.environ["GLUE_JOB_NAME"]


    size_threshold = DEFAULT_CONFIG_OBJECT_SIZE_THRESHOLD
    size_threshold_parameter = os.environ.get("CONFIG_OBJECT_SIZE_THRESHOLD_BYTES", "")
    try:
        size_threshold = int(size_threshold_parameter) if size_threshold_parameter.strip() else DEFAULT_CONFIG_OBJECT_SIZE_THRESHOLD
    except ValueError:
        # Default value if conversion to int fails
        print(f"Warning: SIZE_THRESHOLD environment variable '{size_threshold_parameter}' is not a valid integer. Using default value of {DEFAULT_CONFIG_OBJECT_SIZE_THRESHOLD} bytes.")
        size_threshold = DEFAULT_CONFIG_OBJECT_SIZE_THRESHOLD

    
    records = event['Records']
    for record in records:
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        # process object key
        match  = re.match(PATTERN, key)
        if not match:
            print(f'SKIPPING: Cannot match {key} as AWS Config file, skipping.')
            continue

        # Extract the object size from the event
        object_size = record['s3']['object']['size']
        print(f"Object size: {object_size} bytes")


        # Extract the filename from the full path
        filename = os.path.basename(key)
        # Remove the .json.gz extension if present
        filename = filename.replace('.json.gz', '')

        # Split by underscore and take the last two parts
        parts = filename.split('_')
        if len(parts) >= 2:
            timestamp_and_random = f"{parts[-2]}_{parts[-1]}"
        else:
            # Fallback: use the entire filename without extensions
            timestamp_and_random = filename
        
        run_id = timestamp_and_random

        # Record job start in DynamoDB with object size
        preprocessing_job_record = {
            'source_file': key,
            'job_run_id': run_id,
            'status': 'STARTED',
            'start_time': datetime.now().isoformat(),
            'object_size': object_size,
            'ttl': int((datetime.now().timestamp()) + (90 * 24 * 60 * 60))  # 90 days TTL
        }


         # Check if the object size is smaller than the threshold
        if object_size < size_threshold:
            print(f"Object size {object_size} bytes is below threshold of {size_threshold} bytes. Moving directly to destination bucket.")
            
            s3_client = boto3.client('s3')

            try:
                # Copy the object to the destination bucket
                copy_source = {'Bucket': bucket, 'Key': key}
                destination_key = key  # Use the same key structure in the destination bucket
                
                s3_client.copy_object(
                    CopySource=copy_source,
                    Bucket=dashboard_bucket_name,
                    Key=destination_key
                )
                
                # Update DynamoDB record to reflect direct processing
                preprocessing_job_record['status'] = 'COMPLETED'
                preprocessing_job_record['end_time'] = datetime.now().isoformat()
                preprocessing_job_record['processing_method'] = 'DIRECT_COPY'
                
                dynamodb.put_item(Item=preprocessing_job_record)
                
                print(f"Successfully copied {key} to {dashboard_bucket_name}/{destination_key}")
                
            except Exception as e:
                print(f"Error copying object {key} to destination bucket: {str(e)}")
                preprocessing_job_record['status'] = 'FAILED'
                preprocessing_job_record['error_message'] = str(e)
                dynamodb.put_item(Item=preprocessing_job_record)
                raise

        else:
            glue_client = boto3.client('glue')

            # Record job start in DynamoDB
            dynamodb.put_item(Item=preprocessing_job_record)
            
            # Start Glue job
            # TODO pass object size?
            # '--object_size': f"{object_size}"
            try:
                response = glue_client.start_job_run(
                    JobName=preprocessing_glue_job,
                    Arguments={
                        '--tracking_table_name': f"{table_name}",
                        '--source_path': f"s3://{bucket}/{key}",
                        '--destination_path': f"s3://{dashboard_bucket_name}/",
                        '--CRCD_JOB_RUN_ID': run_id
                    }
                )
                
                print(f"Started Glue job for bucket {bucket} on object {key} with run ID: {response['JobRunId']}")
            
            except Exception as e:
                print(f"Error starting Glue job for {key}: {str(e)}")
                # Update DynamoDB record to reflect failure
                dynamodb.update_item(
                    Key={'source_file': key, 'job_run_id': run_id},
                    UpdateExpression="set #status = :s, #error = :e",
                    ExpressionAttributeNames={
                        '#status': 'status',
                        '#error': 'error_message'
                    },
                    ExpressionAttributeValues={
                        ':s': 'FAILED',
                        ':e': str(e)
                    }
                )
                raise
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed S3 event')
    }