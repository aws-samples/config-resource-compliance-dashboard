# new approach working, before doing code cleanup

# Buckets with many objects, or that also store CloudTrail files will make the Lambda time out before finding all the relevant AWS Config records.
# Here we use the list_objects_v2 API with the delimiter parameter


# AWS Config Resource Compliance Dashboard
# Backfilling producer function, scans your Amazon S3 dashboard bucket and finds all files related to AWS Config that are valid.
# These files are sent to an SQS queue that will trigger another function to add them to the dashboard data.
# 
# Valid files
# 1. all Config history records (WIP: we may go back until a certain date, e.g. max 1 year)
# 2. Config snapshot records on all accounts an regions whose date is the last day of the month, from the last day of the month until 5 monhs ago
# 3. Config snapshot records on all accounts an regions whose date is within the last 5 days

import boto3
import json
import os
import re
from datetime import datetime, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Optional

from collections import deque


DASHBOARD_BUCKET_NAME = os.environ["BUCKET_NAME_VAR"]
SQS_QUEUE = os.environ["SQS_QUEUE_URL_VAR"]

# How much in the past we want to scan (months)
CONFIG_HISTORY_TIME_LIMIT_MONTHS = 12
CONFIG_SNAPSHOT_TIME_LIMIT_MONTHS = 6

# SQS client
sqs = boto3.client('sqs')

# Create an S3 client
s3 = boto3.client('s3')
  
# Define the batch size of the objects read from S3
batch_size = 500 # was: 500

LOGGING_ON = True  # enables additional logging to CloudWatch

# This regular expressions pattern is compatible with how ControlTower Config logs AND also with how Config Logs are stored in S3 in standalone account
# Structure for Config Snapshots: ORG-ID/AWSLogs/ACCOUNT-NUMBER/Config/REGION/YYYY/MM/DD/ConfigSnapshot/objectname.json.gz
# Object name follows this pattern: ACCOUNT-NUMBER_Config_REGION_ConfigSnapshot_TIMESTAMP-YYYYMMDDHHMMSS_RANDOM-TEXT.json.gz
# For example: 123412341234_Config_eu-north-1_ConfigSnapshot_20240306T122755Z_09c5h4kc-3jc7-4897-830v-d7a858325638.json.gz
# PATTERN = r'^(?P<org_id>[\w-]+)?/?AWSLogs/(?P<account_id>\d+)/Config/(?P<region>[\w-]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<type>ConfigSnapshot|ConfigHistory)/[^//]+$'
# PATTERN = r'^(?P<org_id>[\w-]+)?/?AWSLogs/(?P<account_id>\d+)/Config/(?P<region>[\w-]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<type>ConfigSnapshot|ConfigHistory)/[^//]+$'

# I need just to identify the folders, not all the objects
PATTERN = r'^(?P<org_id>[\w-]+)?/?AWSLogs/(?P<account_id>\d+)/Config/(?P<region>[\w-]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<type>ConfigSnapshot|ConfigHistory)/$'
PATTERN_COMPILED = re.compile(PATTERN)

# TODO this recognizes up to the region, it may be better for large buckets, then the processing part can 
# generate the dates and add a partition in case the S3 path exists
PATTERN_REGION = r'^(?P<org_id>[\w-]+)?/?AWSLogs/(?P<account_id>\d+)/Config/(?P<region>[\w-]+)/$'
PATTERN_REGION_COMPILED = re.compile(PATTERN_REGION)

# Regular expression to get the timestamp of the AWS Config file from its S3 prefix
# Used to apply filters on files depending on the date
DATE_PATTERN = r'^.*/(\d{4})/(\d{1,2})/(\d{1,2})/.*$'

def lambda_handler(event, context):
    # Initialize the continuation token
    continuation_token = None
    object_counter = 0
    batch_counter = 0

    config_snapshot_counter = 0
    config_history_counter = 0
    potential_object_counter = 0
    actual_object_counter = 0
    
    # This is to register all S3 prefixes that need a partition
    # Especially with ConfigHistory records, an S3 partition (i.e. path) may contain several files and
    # it does not make sense to create the Athena partition for each file, as the partition points to the S3 prefix
    # KEYS: the S3 prefix, keys are unique and adding a key with the same value of an existing key will simply replace the key and its value
    # VALUES: any S3 object belonging to the prefix
    prefixes = dict()

    # Sends to SQS only AWS Config files 
    # Compliance and Inventory: the dashboard reports the current month of data and the full data from the previous 5 months
    # Event history: the dashbaord has all history - we limit the history to one year
    current_date = datetime.now()
    config_snapshot_date_limit = current_date - relativedelta(months=CONFIG_SNAPSHOT_TIME_LIMIT_MONTHS)
    config_history_date_limit = current_date - relativedelta(months=CONFIG_HISTORY_TIME_LIMIT_MONTHS)

    # Create datetime for last day of month 6 months ago - for Config snapshot files
    # Get year and month from limit date
    year = config_snapshot_date_limit.year
    month = config_snapshot_date_limit.month
    # Get last day of that month using monthrange
    _, last_day = monthrange(year, month)

    # This is the date after which every AWS Config snapshot file have to be sent to SQS
    min_config_snapshot_date = datetime(year, month, last_day)
    print (f'This is the minimum date for Config snapshot files: {min_config_snapshot_date}')

    # Create datetime for Config history records limit
    year = config_history_date_limit.year
    month = config_history_date_limit.month
    min_config_history_date = datetime(year, month, 1)
    print (f'This is the minimum date for Config history files: {min_config_history_date}')

    # TODO get the ORG-ID from env variables and then build the path below, that points to CloudTrail files
    exclude = "o-ggc5oxbobd/AWSLogs/o-ggc5oxbobd"
    bucket = DASHBOARD_BUCKET_NAME
    # prefix = ''
    # We can directly start from this
    prefix = 'o-ggc5oxbobd/AWSLogs'
    delimiter = '/'

    try:
        all_prefixes = set()
        prefixes_to_explore = deque([prefix])
        s3_client = boto3.client('s3')
        paginator = s3_client.get_paginator('list_objects_v2')

        while prefixes_to_explore:
            current_prefix = prefixes_to_explore.popleft()
            
            page_iterator = paginator.paginate(
                Bucket=bucket,
                Prefix=current_prefix,
                Delimiter=delimiter
            )

            for page in page_iterator:
                if 'CommonPrefixes' in page:
                    for common_prefix in page['CommonPrefixes']:
                        prefix_path = common_prefix['Prefix']
                        if not ((exclude and prefix_path.startswith(exclude)) 
                                or ('/OversizedChangeNotification/' in prefix_path)
                                or ('/CloudTrail' in prefix_path)
                                or ('/CloudTrail-Digest' in prefix_path)
                            ):
                            if prefix_path not in all_prefixes:
                                if matches_config_pattern_region(prefix_path): # TODO was matches_config_pattern
                                    if LOGGING_ON: print(f'Found Config prefix {prefix_path}')
                                    all_prefixes.add(prefix_path)
                                    # send it directly to SQS
                                    payload = {
                                        "Records": [{
                                            "s3": {
                                                "object": {"key": prefix_path},
                                                "bucket": {"name": DASHBOARD_BUCKET_NAME}
                                            }
                                        }]
                                    }
                                    sqs.send_message(
                                        QueueUrl=SQS_QUEUE, 
                                        MessageBody=json.dumps(payload)
                                    )
                                else:
                                    if LOGGING_ON: print(f'Exploring prefix {prefix_path}')
                                    prefixes_to_explore.append(prefix_path)
                        else:
                            # the folders checked above are always excluded
                            if LOGGING_ON: print(f'Excluding prefix {prefix_path}')
        return {
            'statusCode': 200,
            'body': {
                'prefixes': sorted(list(all_prefixes)),
                'total_count': len(all_prefixes)
            }
        }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }


    # Intermediate code that did not work, returned ONE prefix only
    try:
        all_prefixes = set()

        # TODO get it from env variables
        exclude = "/o-ggc5oxbobd/AWSLogs/o-ggc5oxbobd"

        while True:
            batch_counter += 1
            # Get next batch of prefixes
            # bucket, prefix, delimiter, batch_size, continuation_token)
            result = get_prefixes_batch(
                DASHBOARD_BUCKET_NAME,
                '',    # params['prefix'],
                '/',   # params['delimiter'],
                # '',    # params['exclude'], maybe try "/o-ggc5oxbobd/AWSLogs/o-ggc5oxbobd/"
                100,   # params['batch_size'],
                continuation_token   # params['continuation_token']
            )

            if LOGGING_ON: print(f'Received prefixes: {result}')
            if LOGGING_ON: print(f'Processing batch {batch_counter} with {len(result.get("CommonPrefixes", []))} prefixes')

            # Add prefixes from this batch (excluding any that match exclude pattern)
            if 'CommonPrefixes' in result:
                for common_prefix in result['CommonPrefixes']:
                    prefix_path = common_prefix['Prefix']
                    if not (exclude and prefix_path.startswith(exclude)):
                        all_prefixes.add(prefix_path)
            
            # Check if there are more batches to process
            if result['IsTruncated']:
                print(f'Calling again')
                continuation_token = result['NextContinuationToken']
            else:
                print(f'Finished')
                break
        
        return {
            'statusCode': 200,
            'body': {
                'prefixes': sorted(list(all_prefixes)),
                'total_count': len(all_prefixes)
            }
        }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }


    # TODO - for now we skip the previous code

    continuation_token = None
    while True:
        # Get the next batch of objects
        response = list_objects_batched(continuation_token)
        batch_counter += 1

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

                if LOGGING_ON: print(f'Processing object {key}')
                    
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

        # Check if there are more batches to process
        if response['IsTruncated']:
            continuation_token = response['NextContinuationToken']
        else:
            break

    # iterate through the prefixes to add them to the SQS queue
    # must do this at the very end, when I have mapped all the files
    for k in prefixes:
        actual_object_counter += 1
        
        sqs.send_message(
            QueueUrl=SQS_QUEUE, 
            MessageBody=json.dumps(prefixes[k])
        )
        if LOGGING_ON: print(f'Added to SQS queue the object : {k}')

    return {
        'statusCode': 200,
        'body': json.dumps(f'Successfully processed {object_counter} objects in the bucket. Sent to the queue for partitioning {actual_object_counter} objects out of {potential_object_counter} valid AWS Config objects, of which there were {config_history_counter} ConfigHistory and {config_snapshot_counter} ConfigSnapshot records.')
    }


def get_prefixes_batch(bucket, prefix, delimiter, batch_size, continuation_token=None):
    s3_client = boto3.client('s3')
    
    params = {
        'Bucket': bucket,
        'Prefix': prefix,
        'Delimiter': delimiter,
        'MaxKeys': batch_size
    }

    if continuation_token:
        params['ContinuationToken'] = continuation_token
        
    return s3_client.list_objects_v2(**params)

def list_prefixes_paginated_deprecated(s3_client, bucket, prefix, delimiter, exclude, page_size, continuation_token):
    # Initialize state
    all_prefixes = set()
    prefixes_to_check = []
    next_token = None
    
    # If we have a continuation token, deserialize the state
    if continuation_token:
        state = json.loads(continuation_token)
        all_prefixes = set(state['all_prefixes'])
        prefixes_to_check = state['prefixes_to_check']
        current_prefix = state['current_prefix']
    else:
        # Initial state
        prefixes_to_check = [prefix]
        current_prefix = prefix
    
    # Process prefixes until we hit the page size limit or run out of prefixes
    while prefixes_to_check and len(all_prefixes) < page_size:
        if not current_prefix:
            current_prefix = prefixes_to_check.pop(0)
            
        # Skip if current prefix is in excluded path
        if should_exclude(current_prefix, exclude):
            current_prefix = None
            continue
            
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(
            Bucket=bucket,
            Prefix=current_prefix,
            Delimiter=delimiter
        )
        
        for page in page_iterator:
            if 'CommonPrefixes' in page:
                for common_prefix in page['CommonPrefixes']:
                    prefix_path = common_prefix['Prefix']
                    if not should_exclude(prefix_path, exclude):
                        if prefix_path not in all_prefixes:
                            all_prefixes.add(prefix_path)
                            prefixes_to_check.append(prefix_path)
                            
                            # Check if we've hit the page size limit
                            if len(all_prefixes) >= page_size:
                                # Create continuation token
                                next_token = json.dumps({
                                    'all_prefixes': list(all_prefixes),
                                    'prefixes_to_check': prefixes_to_check,
                                    'current_prefix': None
                                })
                                break
        
        current_prefix = None
    
    # Prepare response
    response = {
        'prefixes': sorted(list(all_prefixes)),
        'count': len(all_prefixes),
        'has_more': bool(prefixes_to_check)
    }
    
    if prefixes_to_check:
        response['continuation_token'] = next_token
    
    return response

def should_exclude(prefix, exclude_prefix):
    if not exclude_prefix:
        return False
    return prefix.startswith(exclude_prefix)


def matches_config_pattern_region(key: str) -> bool:
    """Two-stage check for Config files"""
    # Quick check before expensive regex
    if not ('/Config/' in key):
        return False

    # Only perform regex if basic pattern matches
    # return bool(re.match(PATTERN_COMPILED, key))
    return bool(re.match(PATTERN_REGION_COMPILED, key))

def matches_config_pattern(key: str) -> bool:
    """Two-stage check for Config files"""
    # Quick check before expensive regex
    if not ('/Config/' in key and ('/ConfigSnapshot/' in key or '/ConfigHistory/' in key)):
        return False

    # Only perform regex if basic pattern matches
    return bool(re.match(PATTERN_COMPILED, key))


# Define the function to list objects in batches
def list_objects_batched(continuation_token=None):
    try:
        response = s3.list_objects_v2(
            Bucket=DASHBOARD_BUCKET_NAME,
            MaxKeys=batch_size,
            ContinuationToken=continuation_token or ''
        )
    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'InvalidArgument':
            print('Invalid continuation token, starting from the beginning.')
            response = s3.list_objects_v2(Bucket=DASHBOARD_BUCKET_NAME, MaxKeys=batch_size)
        else:
            raise e
    
    return response 

# returns true if the given object name corresponds to an AWS Config snapshot or history record
# and it is within the time frame of historical data, i.e. current month and the previous full five months
def can_process(object_key, min_config_snapshot_date, min_config_history_date):
    
    # Quick check before expensive regex
    if not ('/Config/' in object_key and ('/ConfigSnapshot/' in object_key or '/ConfigHistory/' in object_key)):
        if LOGGING_ON: print(f'Cannot match {object_key} as AWS Config file. Skipping.')
        return False

    # process object key TODO maybe can be skipped since it's filtered before?
    match  = re.match(PATTERN, object_key)

    # if match it is a config file
    if match:
        if LOGGING_ON: print(f'{object_key} is an AWS Config file, checking its timestamp.')

        # Use regex pattern for date extraction  
        date_match = re.match(DATE_PATTERN, object_key)

        if date_match:
            year, month, day = map(int, date_match.groups())
            config_file_date = datetime(year, month, day)

            if 'ConfigHistory' in object_key:
                if config_file_date < min_config_history_date:
                    if LOGGING_ON: print(f'ConfigHistory file is dated {config_file_date}: too old for the dashboard. Skipping.')
                    match = False
                else:
                    if LOGGING_ON: print(f'ConfigHistory file is dated {config_file_date}: will be send to the SQS queue.')
                    match = True
            
            if 'ConfigSnapshot' in object_key:
                # only the last day of the month for the previous CONFIG_SNAPSHOT_TIME_LIMIT_MONTHS months and the last 5-ish days
                match = is_config_snapshot_date_valid(config_file_date)
        else:
            # cannot extract the date from the prefix - should never get here
            print(f'ERROR: Cannot extract the date from prefix {object_key}. Skipping.')
            match = False
    else:
        if LOGGING_ON: print(f'Cannot match {object_key} as AWS Config file. Skipping.')
        match = False

    return match
    
def is_config_snapshot_date_valid(config_file_date):
    today = datetime.now().date()
    
    # Check if date is within last 5 days
    five_days_ago = today - timedelta(days=5)
    if five_days_ago <= config_file_date.date() <= today:
        if LOGGING_ON: print(f'ConfigSnapshot file is dated {config_file_date}: will be send to the SQS queue.')
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
            if LOGGING_ON: print(f'ConfigSnapshot file is dated {config_file_date}: will be send to the SQS queue.')
            return True
    
    if LOGGING_ON: print(f'ConfigSnapshot file is dated {config_file_date}: too old or not a end of month date. Skipping.')
    return False