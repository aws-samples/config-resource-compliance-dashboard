import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import explode
from pyspark.sql.functions import col, lit, when
from pyspark.sql.functions import collect_list

import boto3
from datetime import datetime, timezone
import os
import json
import gzip
import io
import random
import string
import urllib.parse
from collections import Counter

# Define replacements dictionary as a constant outside the function
# amazonq-ignore-next-line
S3_NAME_REPLACEMENTS = {
    '/': '-', '\\': '-', ':': '-', '*': '-', '?': '-', '"': '-', '<': '-', '>': '-',
    '|': '-', ' ': '-', '=': '-', '@': '-', '#': '-', '$': '-', '&': '-', '{': '-',
    '}': '-', '[': '-', ']': '-', '`': '-', "'": '-', '!': '-', '+': '-', '^': '-', ',': '-'
}

# Get job parameters
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'tracking_table_name',
    'source_path',
    'destination_path',
    'CRCD_JOB_RUN_ID'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
logger = glueContext.get_logger()  # Get the Glue logger
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Configure Spark for better GZIP and large JSON processing
spark.conf.set("spark.sql.files.maxPartitionBytes", 134217728)  # 128MB
spark.conf.set("spark.sql.files.openCostInBytes", 134217728)  # 128MB
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.files.ignoreCorruptFiles", "true")


# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(args['tracking_table_name'])


def process_file():    
    try:
        logger.info(f"====CRCD==== Original source path: {args['source_path']}")
        logger.info(f"====CRCD==== DDB Table name: {args['tracking_table_name']}")

        # if %3A is on the file name, glue does not find it
        source_path = decode_s3_key(args['source_path'])
        logger.info(f"====CRCD==== Decoded source path: {source_path}")

        try:
            # Read data using Glue's native S3 capabilities
            dynamic_frame = glueContext.create_dynamic_frame.from_options(
                connection_type="s3",
                connection_options={
                    "paths": [source_path],
                    "recurse": False,
                    "compressionType": "gzip"
                },
                format="json"
            )
            
            # Convert to DataFrame for processing
            df = dynamic_frame.toDF()
            dataframe_count = df.count()
            logger.info(f"====CRCD==== dataframe.count = {dataframe_count}")
            
            if dataframe_count == 0:
                error_message = "Failed to read any data from the source file"
                logger.error(error_message)
                update_job_status('FAILED', 0, error_message)
                raise ValueError(error_message)
            
        except Exception as e:
            error_message = f"Error reading with Glue dynamic frame: {str(e)}"
            logger.error(error_message)
            update_job_status('FAILED', 0, error_message)
            raise ValueError(error_message)
        
        # Extract metadata - broadcast these values to all workers
        # These fields may be missing
        file_version_value = df.select("fileVersion").first()[0] if "fileVersion" in df.columns else "1.0"
        snapshot_id_value = df.select("configSnapshotId").first()[0] if "configSnapshotId" in df.columns else ""
        
        # Create broadcast variables for metadata
        file_version_bc = sc.broadcast(file_version_value)
        snapshot_id_bc = sc.broadcast(snapshot_id_value)
        destination_path_bc = sc.broadcast(args['destination_path'])
        source_path_bc = sc.broadcast(args['source_path'])
        job_run_id_bc = sc.broadcast(args['CRCD_JOB_RUN_ID'])
        
        logger.info(f"====CRCD==== file_version = {file_version_value}")
        logger.info(f"====CRCD==== snapshot_id = {snapshot_id_value}")

        # Create a DataFrame with exploded configuration items
        # TODO moved at the top from pyspark.sql.functions import explode, col, lit, when
        items_df = df.select(explode("configurationItems").alias("item"))
        logger.info(f"====CRCD==== EXPLODED items_df.count = {items_df.count()}")

        # Add resourceType as a separate column
        items_with_type_df = items_df.withColumn(
            "resourceType", 
            when(col("item.resourceType").isNotNull(), col("item.resourceType")).otherwise(lit("unknown"))
        )
        
        # Create an accumulator to count processed items
        processed_count_acc = sc.accumulator(0)
        
        # Define function to process each partition
        def process_partition(partition_iterator):
            import boto3
            import io
            import gzip
            import json
            import string
            import random
            import os
            import urllib.parse
            
            # Group items by resource type within this partition
            partition_items = list(partition_iterator)
            if not partition_items:
                return
                
            resource_groups = {}
            for row in partition_items:
                resource_type = row["resourceType"]
                item = row["item"]
                
                if resource_type not in resource_groups:
                    resource_groups[resource_type] = []
                    
                # Convert to dict if it's a Row object
                if hasattr(item, "asDict"):
                    item_dict = item.asDict()
                else:
                    item_dict = item
                    
                resource_groups[resource_type].append(item_dict)
            
            # Create S3 client for this partition
            s3_client = boto3.client('s3')
            batch_size = 200
            
            # Access broadcast variables
            file_version = file_version_bc.value
            snapshot_id = snapshot_id_bc.value
            destination_path = destination_path_bc.value
            source_path = source_path_bc.value
            run_id = job_run_id_bc.value
            
            # Helper functions needed within this partition
            def sanitize_s3_name(name):
                # Implementation of sanitize_s3_name function
                # Generate random string of 10 alphanumeric characters
                default_name = 'unknownResourceId' + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                if not name:
                    return default_name
                    
                # Use the global replacements dictionary
                for char, replacement in S3_NAME_REPLACEMENTS.items():
                    name = name.replace(char, replacement)
                
                # Replace multiple consecutive dashes with a single dash
                while '--' in name:
                    name = name.replace('--', '-')
                
                # Remove leading and trailing dashes
                name = name.strip('-')
                
                # If after all replacements name is empty, generate random string
                if not name:
                    return default_name
                
                return name
                
            def truncate_s3_key(key, max_length=1024):
                # Implementation of truncate_s3_key function
                if len(key.encode('utf-8')) <= max_length:
                    return key
                
                # Split the key into parts
                base, extension = os.path.splitext(key)
                if extension == '.gz':  # handle double extension .json.gz
                    base, json_ext = os.path.splitext(base)
                    extension = json_ext + extension
                
                # Calculate how many bytes we need to remove
                current_length = len(key.encode('utf-8'))
                excess_bytes = current_length - max_length
                
                # Truncate the base name, preserving the extension
                truncated_base = base.encode('utf-8')[:-excess_bytes-1].decode('utf-8', errors='ignore')
                return truncated_base + extension
                
                # TODO proposed code to check
                #if len(key) <= max_length:
                #    return key
                #extension = key.split('.')[-1] if '.' in key else ''
                #base_name = key[:max_length-(len(extension)+1)] if extension else key[:max_length]
                #return f"{base_name}.{extension}" if extension else base_name
                
            def get_destination_path(source_path, destination_base, filename):
                # Implementation of get_destination_path function
                """Generate destination path maintaining the source directory structure"""
                relative_path = get_relative_path(source_path)
                dir_path = os.path.dirname(relative_path)
                
                # Ensure the destination base is properly decoded
                decoded_destination_base = decode_s3_key(destination_base)
                
                if dir_path:
                    return f"{decoded_destination_base.rstrip('/')}/{dir_path}/{filename}"
                return f"{decoded_destination_base.rstrip('/')}/{filename}"
            
            def get_relative_path(source_path):
                # Implementation of get_destination_path function
                """Extract the relative path from the full S3 path"""
                decoded_path = decode_s3_key(source_path)
                parts = decoded_path.replace('s3://', '').split('/', 1)
                if len(parts) > 1:
                    return parts[1]
                return ''
            
            def decode_s3_key(s3_path):
                """Decode only the key part of the S3 path"""
                if not s3_path.startswith('s3://'):
                    return s3_path
                
                # Split the S3 path into bucket and key
                parts = s3_path[5:].split('/', 1)
                if len(parts) < 2:
                    return s3_path
                
                bucket = parts[0]
                key = parts[1]
                
                # Decode only the key part
                decoded_key = urllib.parse.unquote(key)
                
                return f"s3://{bucket}/{decoded_key}"

            # Process each resource group
            for resource_type, items in resource_groups.items():
                # Process items in batches
                for i in range(0, len(items), batch_size):
                    batch = items[i:i + batch_size]
                    
                    # Create batch output
                    output_json = {
                        "fileVersion": file_version,
                        "configSnapshotId": snapshot_id,
                        "configurationItems": batch
                    }
                    
                    # Generate batch filename
                    sanitized_type = sanitize_s3_name(str(resource_type).replace('::', '-'))
                    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                    
                    filename = truncate_s3_key(
                        f"{sanitized_type}_batch_{random_part}_{run_id}.json.gz"
                    )
                    
                    # Get destination path
                    destination = get_destination_path(
                        source_path,
                        destination_path,
                        filename
                    )
                    
                    dest_parts = destination.replace('s3://', '').split('/', 1)
                    dest_bucket = dest_parts[0]
                    dest_key = dest_parts[1]
                    
                    # Compress and write batch
                    with io.BytesIO() as gzip_buffer:
                        with gzip.GzipFile(mode='wb', fileobj=gzip_buffer) as gz:
                            gz.write(json.dumps(output_json).encode('utf-8'))
                        gzip_buffer.seek(0)
                        
                        s3_client.put_object(
                            Bucket=dest_bucket,
                            Key=dest_key,
                            Body=gzip_buffer.getvalue(),
                            ContentType='application/json',
                            ContentEncoding='gzip'
                        )
                    
                    # Update the accumulator with the number of items processed
                    processed_count_acc.add(len(batch))
        
        # Apply the partition processing function to each partition
        items_with_type_df.foreachPartition(process_partition)
        
        # Get the total processed count from the accumulator
        total_processed = processed_count_acc.value
        
        logger.info(f"====CRCD==== Processing Summary:")
        logger.info(f"====CRCD==== Total items processed: {total_processed}")
        
        update_job_status('COMPLETED', total_processed)
        return total_processed

    except ValueError as ve:
        # Handle specific validation errors
        error_message = str(ve)
        print(f"Validation error: {error_message}")
        update_job_status('FAILED', 0, error_message)
        raise
    except Exception as e:
        # Handle other unexpected errors
        error_message = f"Unexpected error: {str(e)}"
        print(error_message)
        update_job_status('FAILED', 0, error_message)
        raise


# This is used bith inside and outside the worker
def decode_s3_key(s3_path):
    """Decode only the key part of the S3 path"""
    if not s3_path.startswith('s3://'):
        return s3_path
    
    # Split the S3 path into bucket and key
    parts = s3_path[5:].split('/', 1)
    if len(parts) < 2:
        return s3_path
    
    bucket = parts[0]
    key = parts[1]
    
    # Decode only the key part
    decoded_key = urllib.parse.unquote(key)
    
    return f"s3://{bucket}/{decoded_key}"

# this code is used externally, another version of the method is internal to the worker
def get_relative_path_external(source_path):
    """Extract the relative path from the full S3 path"""
    decoded_path = decode_s3_key(source_path)
    parts = decoded_path.replace('s3://', '').split('/', 1)
    if len(parts) > 1:
        return parts[1]
    return ''

# DEPRECATED this code must be internal to the worker
def get_destination_path_deprecated(source_path, destination_base, filename):
    """Generate destination path maintaining the source directory structure"""
    # TODO using get_relative_path_external so that the code is not broken
    relative_path = get_relative_path_external(source_path)
    dir_path = os.path.dirname(relative_path)
    
    # Ensure the destination base is properly decoded
    decoded_destination_base = decode_s3_key(destination_base)
    
    if dir_path:
        return f"{decoded_destination_base.rstrip('/')}/{dir_path}/{filename}"
    return f"{decoded_destination_base.rstrip('/')}/{filename}"

def update_job_status(status, processed_items=0, error_message=None):
    try:
        update_expression = "SET #status = :status, end_time = :end_time, processed_items = :processed_items"
        expression_values = {
            ':status': status,
            ':end_time': datetime.now(timezone.utc).isoformat(),
            ':processed_items': processed_items
        }
        
        if error_message:
            update_expression += ", error_message = :error_message"
            expression_values[':error_message'] = error_message

        source_file = get_relative_path_external(args['source_path'])
        
        table.update_item(
            Key={
                'source_file': source_file,
                'job_run_id': args['CRCD_JOB_RUN_ID']
            },
            UpdateExpression=update_expression,
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues=expression_values
        )
    except Exception as e:
        logger.error(f"Error updating DynamoDB: {str(e)}")

# DEPRECATED - this must be internal to the worker
def sanitize_s3_name_deprecated(name):
    # Generate random string of 10 alphanumeric characters
    default_name = 'unknownResourceId' + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    if not name:
        return default_name
        
    # Use the global replacements dictionary
    for char, replacement in S3_NAME_REPLACEMENTS.items():
        name = name.replace(char, replacement)
    
    # Replace multiple consecutive dashes with a single dash
    while '--' in name:
        name = name.replace('--', '-')
    
    # Remove leading and trailing dashes
    name = name.strip('-')
    
    # If after all replacements name is empty, generate random string
    if not name:
        return default_name
    
    return name

# S3 has a limit on the name of objects
# DEPRECATED will be internal to the worker
def truncate_s3_key_deprecated(key, max_length=1000):  # leaving some room for safety
    if len(key.encode('utf-8')) <= max_length:
        return key
    
    # Split the key into parts
    base, extension = os.path.splitext(key)
    if extension == '.gz':  # handle double extension .json.gz
        base, json_ext = os.path.splitext(base)
        extension = json_ext + extension
    
    # Calculate how many bytes we need to remove
    current_length = len(key.encode('utf-8'))
    excess_bytes = current_length - max_length
    
    # Truncate the base name, preserving the extension
    truncated_base = base.encode('utf-8')[:-excess_bytes-1].decode('utf-8', errors='ignore')
    return truncated_base + extension


try:
    # Add more detailed logging
    logger.info("Starting processing file...")
    items_processed = process_file()
    logger.info(f"Successfully processed {items_processed} items")
    job.commit()
except Exception as e:
    logger.error(f"Error processing file: {str(e)}")
    raise
