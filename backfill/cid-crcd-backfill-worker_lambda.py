# Config Resource Compliance Dashboard
# Backfill worker function triggered by SQS
# Capable of handling batches of S3 prefixes and create partitions in Athena/Glue 
# with the same logic as the CRCD Lambda partitioner function

from datetime import datetime, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta
import calendar
import os
import re
import time
import json
import boto3
import random
import gzip
from urllib.parse import unquote
from botocore.exceptions import ClientError

TABLE_NAME = os.environ.get("CONFIG_TABLE_NAME")
ATHENA_DATABASE_NAME = os.environ["ATHENA_DATABASE_NAME"]
ATHENA_QUERY_RESULTS_BUCKET_NAME = os.environ["ATHENA_QUERY_RESULTS_BUCKET_NAME"]
ATHENA_WORKGROUP = os.environ['ATHENA_WORKGROUP']
LOGGING_ON = True  # enables additional logging to CloudWatch

# Partitioning of ConfigSnapshot and ConfigHistory records is enabled from parameters
# Pass 0 to skip the record
# Pass 1 to partition the record
PARTITION_ENABLED = '1'
PARTITION_DISABLED = '0'
PARTITION_CONFIG_SNAPSHOT_RECORDS = os.environ['PARTITION_CONFIG_SNAPSHOT_RECORDS']
PARTITION_CONFIG_HISTORY_RECORDS = os.environ['PARTITION_CONFIG_HISTORY_RECORDS']

# How much in the past we want to scan (months)
CONFIG_HISTORY_TIME_LIMIT_MONTHS = 12
CONFIG_SNAPSHOT_TIME_LIMIT_MONTHS = 6

DATA_SOURCE_CONFIG_HISTORY = 'ConfigHistory'
DATA_SOURCE_CONFIG_SNAPSHOT = 'ConfigSnapshot'

# This regular expressions pattern is compatible with how ControlTower Config logs AND also with how Config Logs are stored in S3 in standalone account
# Structure for Config Snapshots: ORG-ID/AWSLogs/ACCOUNT-NUMBER/Config/REGION/YYYY/MM/DD/ConfigSnapshot/objectname.json.gz
# Object name follows this pattern: ACCOUNT-NUMBER_Config_REGION_ConfigSnapshot_TIMESTAMP-YYYYMMDDHHMMSS_RANDOM-TEXT.json.gz
# For example: 123412341234_Config_eu-north-1_ConfigSnapshot_20240306T122755Z_09c5h4kc-3jc7-4897-830v-d7a858325638.json.gz
PATTERN = r'^(?P<org_id>[\w-]+)?/?AWSLogs/(?P<account_id>\d+)/Config/(?P<region>[\w-]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<type>ConfigSnapshot|ConfigHistory)/[^//]+$'

# TODO this recognizes up to the region, it may be better for large buckets, then the processing part can 
# generate the dates and add a partition in case the S3 path exists
PATTERN_REGION = r'^(?P<org_id>[\w-]+)?/?AWSLogs/(?P<account_id>\d+)/Config/(?P<region>[\w-]+)/$'
PATTERN_REGION_COMPILED = re.compile(PATTERN_REGION)

# create the clients that are needed
athena = boto3.client('athena')
s3 = boto3.client('s3')
glue_client = boto3.client('glue')

def lambda_handler(event, context):


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
    config_snapshot_dates = generate_config_snapshot_date_strings(min_config_snapshot_date)
    if LOGGING_ON:
        for dt in config_snapshot_dates:
            print(f'Config snapshot date: {dt}')

    # Create datetime for Config history records limit
    year = config_history_date_limit.year
    month = config_history_date_limit.month
    min_config_history_date = datetime(year, month, 1)
    print (f'This is the minimum date for Config history files: {min_config_history_date}')
    config_history_dates = generate_config_history_date_strings(min_config_history_date)
    if LOGGING_ON:
        for dt in config_history_dates:
            print(f'Config history date: {dt}')


    for rec in event['Records']:
        print(f'ITERATION---START--------------------------------------------------')

        event_body = rec['body']
        
        if LOGGING_ON:
            print(f'rec = {rec}')
            print(f'event_body = {event_body}')

        message = json.loads(event_body)
        event_bucket_name = message['Records'][0]['s3']['bucket']['name']
        # print(f'event_bucket_name = {event_bucket_name}')
        event_object_key = message['Records'][0]['s3']['object']['key']
        # print(f'event_object_key = {event_object_key}')

        print(f'Processing backfilling prefix: bucket = {event_bucket_name}, prefix = {event_object_key}')

        # Backfill ConfigSnapshot records
        backfill(event_bucket_name, event_object_key, config_snapshot_dates, DATA_SOURCE_CONFIG_SNAPSHOT)

        # Backfill ConfigHistory records
        backfill(event_bucket_name, event_object_key, config_history_dates, DATA_SOURCE_CONFIG_HISTORY)

        print(f'ITERATION---END--------------------------------------------------')

    print(f'CRCD Backfill Worker DONE')
    return {
        'statusCode': 200,
        'body': 'CRCD Backfill complete.'
    }

def generate_config_snapshot_date_strings(start_date):
    """Generates the last day of the month for every month between start_date and today, plus the last 5 days"""
    today = datetime.now()
    
    date_strings = []
    current_date = start_date
    
    while current_date <= today:
        # Get the last day of the current month
        _, last_day = calendar.monthrange(current_date.year, current_date.month)
        last_date_of_month = datetime(current_date.year, current_date.month, last_day)
        
        # If the last day of the month is not in the future, add it to the list
        if last_date_of_month <= today:
            date_strings.append(last_date_of_month.strftime("%Y/%-m/%-d"))
        
        # Move to the first day of the next month
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1)
    
    # Add last 5 days (excluding today if it's already in the list)
    for i in range(5, 0, -1):
        recent_date = today - timedelta(days=i)
        date_str = recent_date.strftime("%Y/%-m/%-d")
        if date_str not in date_strings:  # Avoid duplicates
            date_strings.append(date_str)

    return date_strings

def generate_config_history_date_strings(start_date):
    """Returns an array of dates from the start_date to today"""
    today = datetime.now()
    date_strings = []
    current_date = start_date
    
    while current_date <= today:
        date_strings.append(current_date.strftime("%Y/%-m/%-d"))
        current_date += timedelta(days=1)
    
    return date_strings

# TODO maybe not needed... i iterate throught the dates anyway...
# TODO maybe when you generate the dates, return directly all prefixes, NO because I may need to manage multiple prefixes and don't want to generate the dates every time
def bulk_check_s3_prefixes(bucket_name, prefixes):
    """
    Check existence of multiple S3 prefixes efficiently.
    Each prefix is checked individually since they're all different.
    """
    if not prefixes:
        return []

    s3_client = boto3.client('s3')
    existing_prefixes = []

    try:
        for prefix in prefixes:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=1
            )
            if 'Contents' in response:
                existing_prefixes.append(prefix)

    except ClientError as e:
        print(f"An error occurred: {e}")
        raise  e # Re-raise the exception after logging   

    return existing_prefixes

def check_s3_prefix(bucket_name, prefix):
    """
    Check existence of the given S3 prefix.
    Each prefix is checked individually since they're all different.
    """

    if LOGGING_ON:
        print(f'Checking prefix: {prefix} on bucket: {bucket_name}')

    prefix_exists = False
    try:
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix,
            MaxKeys=1
        )
        if 'Contents' in response:
            prefix_exists = True

    except ClientError as e:
        print(f"An error occurred: {e}")
        raise  e # Re-raise the exception after logging   

    return prefix_exists


def backfill(bucket_name, prefix_key, date_array, config_data_source):
    if LOGGING_ON:
        print(f'Backfilling prefix: {prefix_key} on bucket: {bucket_name}')

    # object_key_parent_root = f's3://{bucket_name}/{prefix_key}'

    for dt in date_array:
        # prefix_key ends with '/'
        object_key_parent = f'{prefix_key}{dt}/{config_data_source}/'
        if LOGGING_ON:
            print(f'Config history date: {dt}')
            print(f'object_key_parent = {object_key_parent}')

        # Checks the current prefix exists on S3
        if check_s3_prefix(bucket_name, object_key_parent):
            match  = re.match(PATTERN_REGION, prefix_key)
            if not match:
                # should never get here
                print(f'Cannot match {prefix_key} as AWS Config file, skipping.')
                continue
            if LOGGING_ON:
                print('Prefix exists! match.groupdict() = ', match.groupdict())
            
            accountid = match.groupdict()['account_id']
            region = match.groupdict()['region']
            
            print(f'Creating partition for item: bucket = {bucket_name}, accountid = {accountid}, region = {region}, dt = {dt}')

            # TODO delete old code
            #drop_partition(accountid, region, dt, DATA_SOURCE_CONFIG_HISTORY)
            #add_partition(accountid, region, dt, object_key_parent, DATA_SOURCE_CONFIG_HISTORY)

            # Considering the use case where many objects are added to the same s3 path at the same time
            # Check if partition exists: need both to avoid calling Athena API too much and create the partition only if it's not there
            # There's no need to create a partition on an S3 path that already exist - Athena will find new files in there
            if not partition_exists(accountid, dt, region, config_data_source):
                # Create the partition if it doesn't exist
                # I just checked, but another Lambda running on another S3 object may come in between
                # TODO build object_location
                # LOCATION 's3://crcd-dashboard-bucket-058264555211-eu-north-1/AWSLogs/058264555211/Config/eu-west-1/2025/6/8/ConfigSnapshot/'
                object_location = f's3://{bucket_name}/{object_key_parent}'
                add_partition_if_not_exists(accountid, region, dt, object_location, config_data_source)
                print(f"Partition created for {accountid}, {dt}, {region}, {config_data_source}")
            else:
                print(f"Partition already exists for {accountid}, {dt}, {region}, {config_data_source}")



        else:
            if LOGGING_ON:
                print(f'Prefix does not exist: {object_key_parent}')

        
def partition_exists(account_id, dt, region, data_source):
    """
    Check if a partition exists using the Glue API
    """
    try:
        # Define partition values in the same order as defined in the Glue table
        partition_values = [account_id, dt, region, data_source]
        
        # Get partition
        response = glue_client.get_partition(
            DatabaseName=ATHENA_DATABASE_NAME,
            TableName=TABLE_NAME,
            PartitionValues=partition_values
        )
        
        # If we get here, the partition exists
        return True
    except ClientError as e:
        # If the error is EntityNotFoundException, the partition doesn't exist
        if e.response['Error']['Code'] == 'EntityNotFoundException':
            return False
        # For any other error, raise it
        raise

def add_partition_if_not_exists(accountid, region, date, location, dataSource):
    execute_query(f"""
        ALTER TABLE {TABLE_NAME}
        ADD IF NOT EXISTS PARTITION (accountid='{accountid}', dt='{date}', region='{region}', dataSource='{dataSource}')
        LOCATION '{location}'
    """)


def backfill_legacy(event_bucket_name, event_object_key):
    object_key_parent = f's3://{event_bucket_name}/{os.path.dirname(event_object_key)}/'

    # deciding what is enabled
    isPartitionConfigSnapshot = (PARTITION_CONFIG_SNAPSHOT_RECORDS == PARTITION_ENABLED)
    isPartitionConfigHistory = (PARTITION_CONFIG_HISTORY_RECORDS == PARTITION_ENABLED)

    # process object key
    match  = re.match(PATTERN, event_object_key)
    if not match:
        print(f'Cannot match {event_object_key} as AWS Config file, skipping.')
        return
    if LOGGING_ON:
        print('match.groupdict() = ', match.groupdict())
    
    accountid = match.groupdict()['account_id']
    region = match.groupdict()['region']
    date = '{year}-{month}-{day}'.format(**match.groupdict())

    if 'ConfigSnapshot' in event_object_key:
        dataSource = 'ConfigSnapshot'

        # If not enabled, I can return
        if not isPartitionConfigSnapshot:
            print(f'SKIPPING: {event_object_key} is a ConfigSnapshot. These records are disabled in the function\'s environment variables.')
            return
    elif 'ConfigHistory' in event_object_key:
        dataSource = 'ConfigHistory'
        # If not enabled, I can return
        if not isPartitionConfigHistory:
            print(f'SKIPPING: {event_object_key} is a ConfigHistory. These records are disabled in the function\'s environment variables.')
            return
    else:
        # I can never get here, if the string passed the regex where ConfigSnapshot and ConfigHistory are checks
        print(f'ERROR - Cannot match {event_object_key} as AWS Config file, skipping.')
        return
    
    drop_partition(accountid, region, date, dataSource)
    add_partition(accountid, region, date, object_key_parent, dataSource)

# Adds an Athena partition with exponential backoff
def add_partition(accountid, region, date, location, dataSource):
    backoff_retry(
        lambda: execute_query(f"""
                ALTER TABLE {TABLE_NAME}
                ADD PARTITION (accountid='{accountid}', dt='{date}', region='{region}', dataSource='{dataSource}')
                LOCATION '{location}'
            """)
    )

# Drops an Athena partition with exponential backoff
def drop_partition(accountid, region, date, dataSource):
    backoff_retry(
        lambda: execute_query(f"""
                ALTER TABLE {TABLE_NAME}
                DROP IF EXISTS PARTITION (accountid='{accountid}', dt='{date}', region='{region}', dataSource='{dataSource}')
            """)
    )

# Runs an SQL statemetn against Athena
def execute_query(query):
    """
        Executes an Athena query (to create a partition) with additional logging and troubleshooting
        It may happen that multiple objects are added to the bucket at the same time
        Every object may need to create an Athena partition, and we need to handle concurrency and limit the impact on Athena API
    """
    print('Executing query:', query)
    try:
        start_query_response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={
                'Database': ATHENA_DATABASE_NAME
            },
            ResultConfiguration={
                'OutputLocation': f's3://{ATHENA_QUERY_RESULTS_BUCKET_NAME}',
            },
            WorkGroup=ATHENA_WORKGROUP
        )
        query_execution_id = start_query_response['QueryExecutionId']
        print(f'Query started with execution ID: {query_execution_id}')

        is_query_running = True
        while is_query_running:
            time.sleep(1)
            execution_status = athena.get_query_execution(
                QueryExecutionId=query_execution_id
            )
            query_execution = execution_status['QueryExecution']
            query_state = query_execution['Status']['State']
            is_query_running = query_state in ('RUNNING', 'QUEUED')

            if not is_query_running and query_state != 'SUCCEEDED':
                error_reason = query_execution['Status'].get('StateChangeReason', 'No reason provided')
                error_details = {
                    'QueryExecutionId': query_execution_id,
                    'State': query_state,
                    'StateChangeReason': error_reason,
                    'Database': ATHENA_DATABASE_NAME,
                    'WorkGroup': ATHENA_WORKGROUP,
                    'OutputLocation': f's3://{ATHENA_QUERY_RESULTS_BUCKET_NAME}'
                }
                print(f'Query failed: {json.dumps(error_details)}')
                raise AthenaException(f'Query failed: {error_reason}')
        
        print(f'Query completed successfully. Execution ID: {query_execution_id}')
        return query_execution_id
    except Exception as e:
        print(f'Exception during query execution: {str(e)}')
        raise

def execute_query_legacy(query):
    print('Executing query:', query)
    start_query_response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': ATHENA_DATABASE_NAME
        },
        ResultConfiguration={
            'OutputLocation': f's3://{ATHENA_QUERY_RESULTS_BUCKET_NAME}',
        },
        WorkGroup=ATHENA_WORKGROUP
    )
    print('Query started')

    is_query_running = True
    while is_query_running:
        time.sleep(1)
        execution_status = athena.get_query_execution(
            QueryExecutionId=start_query_response['QueryExecutionId']
        )
        query_state = execution_status['QueryExecution']['Status']['State']
        is_query_running = query_state in ('RUNNING', 'QUEUED')

        if not is_query_running and query_state != 'SUCCEEDED':
            raise AthenaException('Query failed')
    print('Query completed')

# Exponential backoff implementation
def backoff_retry(func, max_retries=10, base_delay=1, max_delay=120):
    retries = 0
    while True:
        try:
            return func()
        except Exception as e:
            print(f"Error in backoff retry: {e}")
            retries += 1
            if retries > max_retries:
                raise e
            
            # Calculate delay with exponential backoff and jitter
            delay = min(max_delay, base_delay * (2 ** (retries - 1)))
            jitter = random.uniform(0, 0.1 * delay)
            total_delay = delay + jitter
            
            print(f"Retry {retries} after {total_delay:.2f} seconds")
            time.sleep(total_delay)

class AthenaException(Exception):
    ''''This is raised only if the Query is not in state SUCCEEDED'''
    pass
