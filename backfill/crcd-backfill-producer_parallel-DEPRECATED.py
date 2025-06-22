# DEPRECATED

import boto3
import json
import os
import re
import time
import concurrent.futures
from datetime import datetime, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Optional, Tuple, Set

# Environment variables
DASHBOARD_BUCKET_NAME = os.environ["BUCKET_NAME_VAR"]
SQS_QUEUE = os.environ["SQS_QUEUE_URL_VAR"]
# New environment variables for parallel processing
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "10"))  # Default to 10 parallel workers
MAX_PREFIX_DEPTH = int(os.environ.get("MAX_PREFIX_DEPTH", "4"))  # Default prefix depth for partitioning
PROCESS_CHUNK_SIZE = int(os.environ.get("PROCESS_CHUNK_SIZE", "10"))  # Number of prefixes to process per invocation

# How much in the past we want to scan (months)
CONFIG_HISTORY_TIME_LIMIT_MONTHS = 12
CONFIG_SNAPSHOT_TIME_LIMIT_MONTHS = 6

# SQS client
sqs = boto3.client('sqs')

# Create an S3 client
s3 = boto3.client('s3')
  
# Define the batch size of the objects read from S3
batch_size = 1000  # Increased from 500

LOGGING_ON = True  # enables additional logging to CloudWatch

# This regular expressions pattern is compatible with how ControlTower Config logs AND also with how Config Logs are stored in S3 in standalone account
# Structure for Config Snapshots: ORG-ID/AWSLogs/ACCOUNT-NUMBER/Config/REGION/YYYY/MM/DD/ConfigSnapshot/objectname.json.gz
# Object name follows this pattern: ACCOUNT-NUMBER_Config_REGION_ConfigSnapshot_TIMESTAMP-YYYYMMDDHHMMSS_RANDOM-TEXT.json.gz
# For example: 123412341234_Config_eu-north-1_ConfigSnapshot_20240306T122755Z_09c5h4kc-3jc7-4897-830v-d7a858325638.json.gz
PATTERN = r'^(?P<org_id>[\w-]+)?/?AWSLogs/(?P<account_id>\d+)/Config/(?P<region>[\w-]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<type>ConfigSnapshot|ConfigHistory)/[^//]+$'
PATTERN_COMPILED = re.compile(PATTERN)

# Regular expression to get the timestamp of the AWS Config file from its S3 prefix
# Used to apply filters on files depending on the date
DATE_PATTERN = r'^.*/(\d{4})/(\d{1,2})/(\d{1,2})/.*$'

def lambda_handler(event, context):
    """
    Main Lambda handler function that processes S3 objects in parallel.
    
    This function can operate in two modes:
    1. Initial mode: Discovers common prefixes and invokes itself for each prefix chunk
    2. Worker mode: Processes objects within a specific prefix range
    """
    # Check if this is a worker invocation with specific prefixes to process
    if 'prefixes' in event:
        return process_prefixes(event['prefixes'], context)
    
    # If not, this is the initial invocation - discover prefixes and distribute work
    return discover_and_distribute_work(context)

def discover_and_distribute_work(context):
    """
    Discovers common prefixes in the S3 bucket and distributes work by invoking
    worker Lambda functions to process each chunk of prefixes.
    """
    print(f"Starting prefix discovery in bucket {DASHBOARD_BUCKET_NAME}")
    
    # Get common prefixes at the specified depth
    prefixes = get_common_prefixes(DASHBOARD_BUCKET_NAME, MAX_PREFIX_DEPTH)
    total_prefixes = len(prefixes)
    print(f"Discovered {total_prefixes} prefixes to process")
    
    # Calculate time remaining for this Lambda execution
    time_remaining = context.get_remaining_time_in_millis() / 1000  # Convert to seconds
    
    # If we have very few prefixes or plenty of time, process them directly
    if total_prefixes <= PROCESS_CHUNK_SIZE or time_remaining > 60:  # If less than 60 seconds remaining
        print(f"Processing {min(total_prefixes, PROCESS_CHUNK_SIZE)} prefixes directly")
        return process_prefixes(prefixes[:PROCESS_CHUNK_SIZE], context)
    
    # Otherwise, distribute work by invoking worker Lambdas
    lambda_client = boto3.client('lambda')
    function_name = context.function_name
    
    # Split prefixes into chunks
    prefix_chunks = [prefixes[i:i + PROCESS_CHUNK_SIZE] 
                    for i in range(0, len(prefixes), PROCESS_CHUNK_SIZE)]
    
    print(f"Distributing work across {len(prefix_chunks)} worker invocations")
    
    # Invoke worker Lambdas asynchronously
    for i, chunk in enumerate(prefix_chunks):
        payload = {
            'prefixes': chunk,
            'chunk_id': i + 1,
            'total_chunks': len(prefix_chunks)
        }
        
        lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(payload)
        )
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Distributed work across {len(prefix_chunks)} worker invocations to process {total_prefixes} prefixes')
    }

def get_common_prefixes(bucket, max_depth):
    """
    Gets common prefixes in the bucket up to the specified depth.
    Returns a list of prefix strings.
    """
    result = []
    prefixes_to_check = ['']  # Start with root
    
    # Iterate through each level of depth
    for depth in range(max_depth):
        next_level_prefixes = []
        
        for prefix in prefixes_to_check:
            response = s3.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                Delimiter='/',
                MaxKeys=1000
            )
            
            # Add common prefixes from this level
            if 'CommonPrefixes' in response:
                for common_prefix in response['CommonPrefixes']:
                    prefix_value = common_prefix['Prefix']
                    next_level_prefixes.append(prefix_value)
                    
                    # For the last level, add these to our result
                    if depth == max_depth - 1:
                        result.append(prefix_value)
        
        # If no more prefixes found, break
        if not next_level_prefixes:
            break
            
        prefixes_to_check = next_level_prefixes
    
    return result

def process_prefixes(prefixes, context):
    """
    Processes objects within the specified prefixes in parallel.
    """
    chunk_id = 1
    total_chunks = 1
    
    if isinstance(prefixes, dict) and 'chunk_id' in prefixes:
        chunk_id = prefixes.get('chunk_id', 1)
        total_chunks = prefixes.get('total_chunks', 1)
        prefixes = prefixes.get('prefixes', [])
    
    print(f"Worker {chunk_id}/{total_chunks} starting to process {len(prefixes)} prefixes")
    
    # Initialize counters
    object_counter = 0
    config_snapshot_counter = 0
    config_history_counter = 0
    potential_object_counter = 0
    actual_object_counter = 0
    
    # Calculate date limits once
    date_limits = calculate_date_limits()
    min_config_snapshot_date = date_limits['min_config_snapshot_date']
    min_config_history_date = date_limits['min_config_history_date']
    
    # Dictionary to store prefixes that need partitioning
    partition_prefixes = {}
    
    # Process prefixes in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Create a list of futures
        future_to_prefix = {
            executor.submit(process_single_prefix, prefix, min_config_snapshot_date, min_config_history_date): 
            prefix for prefix in prefixes
        }
        
        # Process completed futures
        for future in concurrent.futures.as_completed(future_to_prefix):
            prefix = future_to_prefix[future]
            try:
                result = future.result()
                
                # Update counters
                object_counter += result['object_counter']
                config_snapshot_counter += result['config_snapshot_counter']
                config_history_counter += result['config_history_counter']
                potential_object_counter += result['potential_object_counter']
                
                # Merge the prefix dictionaries
                partition_prefixes.update(result['prefixes'])
                
            except Exception as exc:
                print(f'Prefix {prefix} generated an exception: {exc}')
    
    # Send messages to SQS queue
    for k in partition_prefixes:
        actual_object_counter += 1
        
        sqs.send_message(
            QueueUrl=SQS_QUEUE, 
            MessageBody=json.dumps(partition_prefixes[k])
        )
        if LOGGING_ON: print(f'Added to SQS queue the object: {k}')
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Worker {chunk_id}/{total_chunks}: Successfully processed {object_counter} objects. '
                          f'Sent to the queue {actual_object_counter} objects out of {potential_object_counter} '
                          f'valid AWS Config objects ({config_history_counter} ConfigHistory, '
                          f'{config_snapshot_counter} ConfigSnapshot).')
    }

def process_single_prefix(prefix, min_config_snapshot_date, min_config_history_date):
    """
    Processes all objects within a single prefix.
    Returns a dictionary with counters and prefixes to be processed.
    """
    # Initialize counters
    object_counter = 0
    config_snapshot_counter = 0
    config_history_counter = 0
    potential_object_counter = 0
    prefixes = {}
    
    continuation_token = None
    
    while True:
        # List objects in the prefix
        try:
            if continuation_token:
                response = s3.list_objects_v2(
                    Bucket=DASHBOARD_BUCKET_NAME,
                    Prefix=prefix,
                    MaxKeys=batch_size,
                    ContinuationToken=continuation_token
                )
            else:
                response = s3.list_objects_v2(
                    Bucket=DASHBOARD_BUCKET_NAME,
                    Prefix=prefix,
                    MaxKeys=batch_size
                )
        except s3.exceptions.ClientError as e:
            print(f"Error listing objects for prefix {prefix}: {e}")
            break
            
        # Process objects if any exist
        if 'Contents' in response:
            # Filter objects that match the pattern before detailed processing
            matching_objects = filter(
                lambda obj: matches_config_pattern(obj['Key']), 
                response['Contents']
            )
            
            # Process only the matching objects
            for obj in matching_objects:
                object_counter += 1
                key = obj['Key']
                
                if LOGGING_ON and object_counter % 100 == 0: 
                    print(f'Processing object {object_counter}: {key}')
                    
                # Now we know it's a Config file, process based on type
                if can_process(key, min_config_snapshot_date, min_config_history_date):
                    if 'ConfigHistory' in key:
                        config_history_counter += 1
                    if 'ConfigSnapshot' in key:
                        config_snapshot_counter += 1
                        
                    potential_object_counter += 1
                    payload = {
                        "Records": [{
                            "s3": {
                                "object": {"key": key},
                                "bucket": {"name": DASHBOARD_BUCKET_NAME}
                            }
                        }]
                    }
                        
                    prefix_key = f'{os.path.dirname(key)}'
                    prefixes[prefix_key] = payload
        
        # Check if there are more objects to process
        if response.get('IsTruncated', False):
            continuation_token = response.get('NextContinuationToken')
        else:
            break
    
    return {
        'object_counter': object_counter,
        'config_snapshot_counter': config_snapshot_counter,
        'config_history_counter': config_history_counter,
        'potential_object_counter': potential_object_counter,
        'prefixes': prefixes
    }

def calculate_date_limits():
    """Calculate the date limits for Config files"""
    current_date = datetime.now()
    config_snapshot_date_limit = current_date - relativedelta(months=CONFIG_SNAPSHOT_TIME_LIMIT_MONTHS)
    config_history_date_limit = current_date - relativedelta(months=CONFIG_HISTORY_TIME_LIMIT_MONTHS)

    # Create datetime for last day of month 6 months ago - for Config snapshot files
    year = config_snapshot_date_limit.year
    month = config_snapshot_date_limit.month
    _, last_day = monthrange(year, month)
    min_config_snapshot_date = datetime(year, month, last_day)
    
    # Create datetime for Config history records limit
    year = config_history_date_limit.year
    month = config_history_date_limit.month
    min_config_history_date = datetime(year, month, 1)
    
    print(f'Minimum date for Config snapshot files: {min_config_snapshot_date}')
    print(f'Minimum date for Config history files: {min_config_history_date}')
    
    return {
        'min_config_snapshot_date': min_config_snapshot_date,
        'min_config_history_date': min_config_history_date
    }

def matches_config_pattern(key: str) -> bool:
    """Two-stage check for Config files"""
    # Quick check before expensive regex
    if not ('/Config/' in key and ('/ConfigSnapshot/' in key or '/ConfigHistory/' in key)):
        return False

    # Only perform regex if basic pattern matches
    return bool(re.match(PATTERN_COMPILED, key))

def can_process(object_key, min_config_snapshot_date, min_config_history_date):
    """
    Determines if an object should be processed based on its type and date.
    """
    # Quick check before expensive regex
    if not ('/Config/' in object_key and ('/ConfigSnapshot/' in object_key or '/ConfigHistory/' in object_key)):
        return False

    # Process object key
    match = re.match(PATTERN, object_key)

    # If match it is a config file
    if match:
        # Use regex pattern for date extraction  
        date_match = re.match(DATE_PATTERN, object_key)

        if date_match:
            year, month, day = map(int, date_match.groups())
            config_file_date = datetime(year, month, day)

            if 'ConfigHistory' in object_key:
                if config_file_date < min_config_history_date:
                    return False
                else:
                    return True
            
            if 'ConfigSnapshot' in object_key:
                # Only the last day of the month for the previous CONFIG_SNAPSHOT_TIME_LIMIT_MONTHS months and the last 5-ish days
                return is_config_snapshot_date_valid(config_file_date)
        else:
            # Cannot extract the date from the prefix - should never get here
            print(f'ERROR: Cannot extract the date from prefix {object_key}. Skipping.')
            return False
    else:
        return False

def is_config_snapshot_date_valid(config_file_date):
    """
    Checks if a Config snapshot date is valid based on the criteria:
    1. Within the last 5 days
    2. Last day of any month within the time limit
    """
    today = datetime.now().date()
    
    # Check if date is within last 5 days
    five_days_ago = today - timedelta(days=5)
    if five_days_ago <= config_file_date.date() <= today:
        return True
    
    # Check last days of previous months
    current_year = today.year
    current_month = today.month
    
    # Check previous months until the limit
    for i in range(1, CONFIG_SNAPSHOT_TIME_LIMIT_MONTHS):  
        # Calculate the year and month we're checking
        check_month = current_month - i
        check_year = current_year
        
        # Adjust year if we need to go back to previous year
        if check_month <= 0:
            check_month += 12
            check_year -= 1
            
        # Get the last day of that month
        _, last_day = monthrange(check_year, check_month)
        last_date = datetime(check_year, check_month, last_day).date()
        
        # Compare with config_file_date
        if config_file_date.date() == last_date:
            return True
    
    return False