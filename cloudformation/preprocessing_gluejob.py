import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
import boto3
from datetime import datetime
import os
import json
import gzip
import io
import random
import string
import urllib.parse
from collections import Counter


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

# Configure Spark for better GZIP processing
spark.conf.set("spark.sql.files.maxPartitionBytes", 134217728)  # 128MB
spark.conf.set("spark.sql.files.openCostInBytes", 134217728)  # 128MB
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.enabled", "true")


# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
# table = dynamodb.Table('CRCDFlatteningJobTracking') # TODO delete when tested
table = dynamodb.Table(args['tracking_table_name'])


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

def get_relative_path(source_path):
    """Extract the relative path from the full S3 path"""
    decoded_path = decode_s3_key(source_path)
    parts = decoded_path.replace('s3://', '').split('/', 1)
    if len(parts) > 1:
        return parts[1]
    return ''

def get_destination_path(source_path, destination_base, filename):
    """Generate destination path maintaining the source directory structure"""
    relative_path = get_relative_path(source_path)
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
            ':end_time': datetime.now().isoformat(),
            ':processed_items': processed_items
        }
        
        if error_message:
            update_expression += ", error_message = :error_message"
            expression_values[':error_message'] = error_message

        source_file = get_relative_path(args['source_path'])
        
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
        print(f"Error updating DynamoDB: {str(e)}")

def sanitize_s3_name(name):
    # Generate random string of 10 alphanumeric characters
    default_name = 'unknownResourceId'.join(random.choices(string.ascii_letters + string.digits, k=10))
    if not name:
        return default_name
        
    # Replace characters that could cause issues in S3 paths
    replacements = {
        '/': '-',
        '\\': '-',
        ':': '-',
        '*': '-',
        '?': '-',
        '"': '-',
        '<': '-',
        '>': '-',
        '|': '-',
        ' ': '-',
        '=': '-',
        '@': '-',
        '#': '-',
        '$': '-',
        '&': '-',
        '{': '-',
        '}': '-',
        '[': '-',
        ']': '-',
        '`': '-',
        "'": '-',
        '!': '-',
        '+': '-',
        '^': '-',
        ',': '-'
    }
    
    for char, replacement in replacements.items():
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
def truncate_s3_key(key, max_length=1000):  # leaving some room for safety
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

def process_file():    
    try:
        logger.info("10====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====")
        logger.info(f"Original source path: {args['source_path']}")
        logger.info(f"DDB Table name: {args['tracking_table_name']}")


        # if %3A is on the file name, glue does not find it
        source_path = decode_s3_key(args['source_path'])
        logger.info("11====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====")
        logger.info(f"Decoded source path: {source_path}")

        
        # Use Glue's native S3 reading capabilities instead of sc.wholeTextFiles
        try:
            # For gzipped JSON files, we need to use the grokLog format with custom patterns
            # or use the format="json" with compression="gzip" if the files are properly formatted
            dynamic_frame = glueContext.create_dynamic_frame.from_options(
                connection_type="s3",
                connection_options={
                    "paths": [source_path],
                    "recurse": False,
                    "compressionType": "gzip"
                },
                format="json"
            )
            
            # Convert to DataFrame for easier processing
            df = dynamic_frame.toDF()
            
            logger.info("20====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====")
            logger.info(f"dataframe.count = {df.count()}")
            
            # If the DataFrame is empty, try alternative approach
            if df.count() == 0:
                logger.info("30====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====")
                logger.info("No data read using standard approach, trying alternative method...")
                
                # Use boto3 to read the file directly
                s3_path = args['source_path']
                path_parts = s3_path.replace('s3://', '').split('/', 1)
                bucket = path_parts[0]
                key = path_parts[1] if len(path_parts) > 1 else ''
                
                s3 = boto3.client('s3')
                
                logger.info("40====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====")
                logger.info(f"getting object {key} from bucket {bucket}")
                
                
                response = s3.get_object(Bucket=bucket, Key=key)
                content = response['Body'].read()
                
                # Decompress if gzipped
                if key.endswith('.gz'):
                    content = gzip.decompress(content)
                
                # Parse JSON
                json_content = json.loads(content.decode('utf-8'))
                
                # Create a DataFrame from the JSON
                json_rdd = sc.parallelize([json.dumps(json_content)])
                df = spark.read.json(json_rdd)
            
        except Exception as e:
            
            logger.info("300====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====CRCD====")
            logger.error(f"Error reading with Glue dynamic frame: {str(e)}")
            
            # Fallback to direct boto3 reading
            s3_path = args['source_path']
            path_parts = s3_path.replace('s3://', '').split('/', 1)
            bucket = path_parts[0]
            key = path_parts[1] if len(path_parts) > 1 else ''
            
            s3 = boto3.client('s3')
            response = s3.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()
            
            # Decompress if gzipped
            if key.endswith('.gz'):
                content = gzip.decompress(content)
            
            # Parse JSON
            json_content = json.loads(content.decode('utf-8'))
            
            # Create a DataFrame from the JSON
            json_rdd = sc.parallelize([json.dumps(json_content)])
            df = spark.read.json(json_rdd)
        
        # Convert DataFrame back to Python dict for processing
        json_content = json.loads(df.toJSON().collect()[0])
        
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
        logger.info(f"Found {total_items} items in configurationItems array")
        
        # Get the common fields that need to be preserved
        output_template = {
            "fileVersion": json_content.get("fileVersion", "1.0"),
            "configSnapshotId": json_content.get("configSnapshotId", ""),
            "configurationItems": []
        }
        
        # Process each configuration item
        for index, item in enumerate(json_content['configurationItems'], 1):
            try:
                # TODO test if it works without this
                # Convert configuration field to string if it's an object
                #if 'configuration' in item and isinstance(item['configuration'], dict):
                #    item['configuration'] = json.dumps(item['configuration'])

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
                
                logger.info(f"Processing item {index}/{total_items}: {filename}")
                
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
                logger.info(f"Successfully saved {filename} to {destination}")
                
            except Exception as item_error:
                logger.error(f"Error processing item {index}/{total_items}: {str(item_error)}")
                logger.error(f"Problematic item: {json.dumps(item)}")
                continue  # Continue with next item instead of failing the whole job
        
        # Log summary
        logger.info(f"\nProcessing Summary:")
        logger.info(f"Total items found: {total_items}")
        logger.info(f"Items processed successfully: {processed_count}")
        logger.info(f"Items missed: {total_items - processed_count}")
        
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



try:
    items_processed = process_file()
    print(f"Successfully processed {items_processed} items")
    job.commit()
except Exception as e:
    print(f"Error processing file: {str(e)}")
    raise