
import math
import time
import sys
from awsglue.transforms import *
from pyspark.sql.types import *
from pyspark.sql.functions import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

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

# Initialize Glue context
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

def process_file_DEPRECATED():
    """initial approach, but it's taking me far away in circles"""
    logger.info(f"====CRCD==== Original source path: {args['source_path']}")
    logger.info(f"====CRCD==== DDB Table name: {args['tracking_table_name']}")

    # if %3A is on the file name, glue does not find it
    source_path = decode_s3_key_external(args['source_path'])
    logger.info(f"====CRCD==== Decoded source path: {source_path}")

    destination_path = args['destination_path']
    logger.info(f"====CRCD==== Destination path: {destination_path}")

    try:
        # Read the large JSON file directly with Spark
        raw_data = sc.textFile(source_path)
        config_content = raw_data.collect()
        config_content = "".join(config_content)
        config_data = json.loads(config_content)

        logger.info(f"====CRCD==== JSON data loaded")

        # Extract the metadata
        file_version = config_data.get("fileVersion", "1.0")
        config_snapshot_id = config_data.get("configSnapshotId", "")
        config_items = config_data.get("configurationItems", [])

        # Calculate how many output files we'll need
        total_items = len(config_items)
        batch_size = 100
        num_batches = math.ceil(total_items / batch_size)

        logger.info(f"====CRCD==== Processing {total_items} items into {num_batches} output files")

        # Process in batches of 100 items
        for i in range(num_batches):
            start_idx = i * batch_size
            # The error you're encountering is unusual because in standard Python, the min() function should accept multiple arguments. 
            # However, it appears that in your AWS Glue environment, there might be a custom implementation or namespace conflict 
            # affecting the min() function.
            # end_idx = min((i + 1) * batch_size, total_items)

            if (i + 1) * batch_size < total_items:
                end_idx = (i + 1) * batch_size
            else:
                end_idx = total_items

            
            # Create a new config object with just this batch of items
            batch_config = {
                "fileVersion": file_version,
                "configSnapshotId": config_snapshot_id,
                "configurationItems": config_items[start_idx:end_idx]
            }
        
            # Convert to JSON string
            batch_json = json.dumps(batch_config)
            
            # Create an RDD with the batch data
            batch_rdd = sc.parallelize([batch_json])
            
            # Write the batch to S3
            output_path = f"{destination_path}/config_batch_{i+1:05d}.json"
            batch_rdd.saveAsTextFile(output_path)

    except Exception as e:
            error_message = f"Error reading with Glue dynamic frame: {str(e)}"
            logger.error(error_message)
            update_job_status('FAILED', 0, error_message)
            raise ValueError(error_message)
    

    # Get the total processed count from the accumulator
    total_processed = total_items
    
    logger.info(f"====CRCD==== Processing Summary:")
    logger.info(f"====CRCD==== Total items processed: {total_processed}")
    
    update_job_status('COMPLETED', total_processed)
    return total_processed

def process_file():
    
    logger.info(f"====CRCD==== Original source path: {args['source_path']}")
    logger.info(f"====CRCD==== DDB Table name: {args['tracking_table_name']}")

    # if %3A is on the file name, glue does not find it
    source_path = decode_s3_key_external(args['source_path'])
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
    
    try:
        # Convert DataFrame back to Python dict for processing
        start_time = time.time()
        logger.info(f"====CRCD==== starting load of JSON")
        
        # ====CRCD==== 
        json_content = json.loads(df.toJSON().collect()[0])
        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"====CRCD==== completed load 1 of JSON in {elapsed_time:.6f} seconds")

        # TODO loading the file TWICE to compare performance
        # This uses spark
        start_time = time.time()
        raw_data = sc.textFile(source_path)
        config_content = raw_data.collect()
        config_content = "".join(config_content)
        json_content = json.loads(config_content)

        end_time = time.time()
        elapsed_time = end_time - start_time
        logger.info(f"====CRCD==== completed load 2 of JSON in {elapsed_time:.6f} seconds")
        

        # Performance
        # config_history_payload_10000-items_20250406170827.json.gz - 500Kb zipped
        # ====CRCD==== completed load 1 of JSON in 10.112428 seconds
        # ====CRCD==== completed load 2 of JSON in 2.617950 seconds

        # config_history_payload_100000-items_20250406170856.json.gz - 5MB zipped
        # ====CRCD==== completed load 1 of JSON in 57.562911 seconds 
        # ====CRCD==== completed load 2 of JSON in 27.099247 seconds

        # config_history_payload_500000-items_20250406170928.json.gz - 25MB zipped
        #




        processed_count = 0
        total_items = 0
        processed_items = []
        
        # Check if configurationItems exists and is not empty
        if 'configurationItems' not in json_content:
            raise ValueError("JSON file does not contain 'configurationItems' field")
        
        if not json_content['configurationItems']:
            raise ValueError("'configurationItems' array is empty")
        
        # Count and log total items
        total_items = len(json_content['configurationItems'])
        logger.info(f"====CRCD==== Found {total_items} items in configurationItems array")
        
        # Get the common fields that need to be preserved
        output_template = {
            "fileVersion": json_content.get("fileVersion", "1.0"),
            "configSnapshotId": json_content.get("configSnapshotId", ""),
            "configurationItems": []
        }
        
        # Process each configuration item
        for index, item in enumerate(json_content['configurationItems'], 1):
            try:
                # Create a new output object for this item
                output_json = output_template.copy()
                output_json['configurationItems'] = [item]
                
                resource_type = sanitize_s3_name(item.get('resourceType', '').replace('::', '-'))
                resource_name = sanitize_s3_name(item.get('resourceId', ''))
                
                run_id = args['CRCD_JOB_RUN_ID']
                
                # Track the item being processed
                item_identifier = f"{resource_type}_{resource_name}"
                processed_items.append(item_identifier)

                # Want to be sure every file name is different and also relates to its content and origin
                random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
                                
                filename_original = f"{random_part}_{resource_type}_{resource_name}_{run_id}.json.gz"
                # filename must not be too long for S3 - Object key names may be up to 1024 characters long
                filename = truncate_s3_key(filename_original)
            
                destination = get_destination_path(
                    args['source_path'],
                    args['destination_path'],
                    filename
                )
                
                logger.info(f"====CRCD-iteration==== Processing item {index}/{total_items}: {filename}")
                
                dest_parts = destination.replace('s3://', '').split('/', 1)
                dest_bucket = dest_parts[0]
                dest_key = dest_parts[1]
                
                # Convert JSON to bytes and compress
                # AWS Config JSON is all on a single line without indentation, 
                # while a problematic JSON is formatted with indentation and newlines. 
                # Athena's JSON SerDe expects each line to be a complete JSON object.
                # remove the indent=2 parameter
                # json_bytes = json.dumps(output_json, indent=2).encode('utf-8')
                json_bytes = json.dumps(output_json).encode('utf-8')
                
                # Create a BytesIO object to hold the gzipped data
                gzip_buffer = io.BytesIO()
                
                # Create a GzipFile object and write the JSON data
                with gzip.GzipFile(mode='wb', fileobj=gzip_buffer) as gz:
                    gz.write(json_bytes)
                
                # Get the gzipped content
                gzip_buffer.seek(0)
                gzipped_content = gzip_buffer.getvalue()
                
                s3 = boto3.client('s3')
                s3.put_object(
                    Bucket=dest_bucket,
                    Key=dest_key,
                    Body=gzipped_content,
                    ContentType='application/json',
                    ContentEncoding='gzip'
                )
                processed_count += 1
                # This is too verbose
                # logger.info(f"====CRCD==== Successfully saved {filename} to {destination}")
                
            except Exception as item_error:
                logger.error(f"Error processing item {index}/{total_items}: {str(item_error)}")
                logger.error(f"Problematic item: {json.dumps(item)}")
                continue  # Continue with next item instead of failing the whole job
        
        # Log summary
        logger.info(f"====CRCD==== Processing Summary:")
        logger.info(f"====CRCD==== Total items found: {total_items}")
        logger.info(f"====CRCD==== Items processed successfully: {processed_count}")
        logger.info(f"====CRCD==== Items missed: {total_items - processed_count}")
        
        if total_items != processed_count:
            logger.info("\nPossible issues:")
            # Check for duplicates in processed items
            item_counts = Counter(processed_items)
            duplicates = {item: count for item, count in item_counts.items() if count > 1}
            if duplicates:
                logger.info("\nFound duplicate resource names (might have overwritten files):")
                for item, count in duplicates.items():
                    logger.info(f"  {item}: {count} occurrences")
            
        update_job_status('COMPLETED', processed_count)
        return processed_count
        
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

# This is used both inside and outside the worker, this is the external version
def decode_s3_key_external(s3_path):
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
    decoded_path = decode_s3_key_external(source_path)
    parts = decoded_path.replace('s3://', '').split('/', 1)
    if len(parts) > 1:
        return parts[1]
    return ''

def update_job_status(status, processed_items=0, error_message=None):
    try:
        update_expression = "SET #status = :status, end_time = :end_time, processed_items = :processed_items, processing_method = :processing_method"
        expression_values = {
            ':status': status,
            ':end_time': datetime.now(timezone.utc).isoformat(),
            ':processed_items': processed_items,
            ':processing_method': 'GLUE_TRANSFORMATION'
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



try:
    # Add more detailed logging
    logger.info("Starting processing file...")
    items_processed = process_file()
    logger.info(f"Successfully processed {items_processed} items")
    job.commit()
except Exception as e:
    logger.error(f"Error processing file: {str(e)}")
    raise
