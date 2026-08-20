# using IJSON library

import sys
import boto3
import ijson
import json
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext

# Define replacements dictionary as a constant outside the function
# amazonq-ignore-next-line
S3_NAME_REPLACEMENTS = {
    '/': '-', '\\': '-', ':': '-', '*': '-', '?': '-', '"': '-', '<': '-', '>': '-',
    '|': '-', ' ': '-', '=': '-', '@': '-', '#': '-', '$': '-', '&': '-', '{': '-',
    '}': '-', '[': '-', ']': '-', '`': '-', "'": '-', '!': '-', '+': '-', '^': '-', ',': '-'
}

# Initialize Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
logger = glueContext.get_logger()  # Get the Glue logger

def main():
    # Get job parameters
    # args = getResolvedOptions(sys.argv, ['source_s3_path', 'dest_bucket'])
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'tracking_table_name',
        'source_path',
        'destination_path',
        'CRCD_JOB_RUN_ID'
    ])

    # if %3A is on the file name, glue does not find it
    # TODO test source_path = decode_s3_key_external(args['source_path'])

    source_s3_path = args['source_path']
    dest_bucket = args['dest_bucket']
    
    # Parse S3 path
    source_bucket = source_s3_path.split('/')[2]
    source_key = '/'.join(source_s3_path.split('/')[3:])
    
    s3_client = boto3.client('s3')
    
    # Stream the file from S3
    response = s3_client.get_object(Bucket=source_bucket, Key=source_key)
    
    # Extract metadata
    file_version = None
    config_snapshot_id = None
    
    # First pass to get metadata
    parser = ijson.parse(response['Body'])
    for prefix, event, value in parser:
        if prefix == 'fileVersion':
            file_version = value
        elif prefix == 'configSnapshotId':
            config_snapshot_id = value
        elif prefix == 'configurationItems':
            break
    
    # Second pass to process configurationItems
    response = s3_client.get_object(Bucket=source_bucket, Key=source_key)
    items = ijson.items(response['Body'], 'configurationItems.item')
    
    batch = []
    batch_num = 0
    
    for item in items:
        batch.append(item)
        
        if len(batch) == 100:
            # Create output file
            output_data = {
                "fileVersion": file_version,
                "configurationItems": batch
            }
            
            if config_snapshot_id:
                output_data["configSnapshotId"] = config_snapshot_id
            
            # Generate output key
            base_name = source_key.split('/')[-1].replace('.json', '')
            output_key = f"split/{base_name}_batch_{batch_num:04d}.json"
            
            # Upload to S3
            s3_client.put_object(
                Bucket=dest_bucket,
                Key=output_key,
                Body=json.dumps(output_data),
                ContentType='application/json'
            )
            
            batch = []
            batch_num += 1
    
    # Handle remaining items
    if batch:
        output_data = {
            "fileVersion": file_version,
            "configurationItems": batch
        }
        
        if config_snapshot_id:
            output_data["configSnapshotId"] = config_snapshot_id
        
        base_name = source_key.split('/')[-1].replace('.json', '')
        output_key = f"split/{base_name}_batch_{batch_num:04d}.json"
        
        s3_client.put_object(
            Bucket=dest_bucket,
            Key=output_key,
            Body=json.dumps(output_data),
            ContentType='application/json'
        )

if __name__ == "__main__":
    main()