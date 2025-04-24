import re
import os
import time
import json
import boto3
from urllib.parse import unquote
from botocore.exceptions import ClientError
import gzip


TABLE_NAME = os.environ.get("CONFIG_TABLE_NAME")
ATHENA_DATABASE_NAME = os.environ["ATHENA_DATABASE_NAME"]
ATHENA_QUERY_RESULTS_BUCKET_NAME = os.environ["ATHENA_QUERY_RESULTS_BUCKET_NAME"]
ATHENA_WORKGROUP = os.environ['ATHENA_WORKGROUP']
LOGGING_ON = False  # enables additional logging to CloudWatch

# Partitioning of ConfigSnapshot and ConfigHistory records is enabled from parameters
# Pass 0 to skip the record
# Pass 1 to partition the record
PARTITION_ENABLED = '1'
PARTITION_DISABLED = '0'
PARTITION_CONFIG_SNAPSHOT_RECORDS = os.environ['PARTITION_CONFIG_SNAPSHOT_RECORDS']
PARTITION_CONFIG_HISTORY_RECORDS = os.environ['PARTITION_CONFIG_HISTORY_RECORDS']

# This regular expressions pattern is compatible with how ControlTower Config logs AND also with how Config Logs are stored in S3 in standalone account
# Structure for Config Snapshots: ORG-ID/AWSLogs/ACCOUNT-NUMBER/Config/REGION/YYYY/MM/DD/ConfigSnapshot/objectname.json.gz
# Object name follows this pattern: ACCOUNT-NUMBER_Config_REGION_ConfigSnapshot_TIMESTAMP-YYYYMMDDHHMMSS_RANDOM-TEXT.json.gz
# For example: 123412341234_Config_eu-north-1_ConfigSnapshot_20240306T122755Z_09c5h4kc-3jc7-4897-830v-d7a858325638.json.gz
PATTERN = r'^(?P<org_id>[\w-]+)?/?AWSLogs/(?P<account_id>\d+)/Config/(?P<region>[\w-]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<type>ConfigSnapshot|ConfigHistory)/[^//]+$'

# Athena client
athena = boto3.client('athena')

# Create an S3 client
s3 = boto3.client('s3')

# Glue client
glue_client = boto3.client('glue')

class AthenaException(Exception):
    """ This is raised only if the Athena Query is not in state SUCCEEDED"""
    pass

def lambda_handler(event, context):
    if LOGGING_ON: print('This is the event', event)

    event_object_key = None
    event_bucket_name = None
    dataSource = None # this can be ConfigSnapshot or ConfigHistory
    found_event = False

    # deciding what is enabled
    isPartitionConfigSnapshot = (PARTITION_CONFIG_SNAPSHOT_RECORDS == PARTITION_ENABLED)
    isPartitionConfigHistory = (PARTITION_CONFIG_HISTORY_RECORDS == PARTITION_ENABLED)

    # Is this called directly by S3 event notification?
    try:
        event_object_key = event['Records'][0]['s3']['object']['key']
        event_bucket_name = event['Records'][0]['s3']['bucket']['name']
        if LOGGING_ON: print('This is an S3 event')
        found_event = True
    except KeyError:
        # key doesn't exist
        if LOGGING_ON: print('This is not an S3 event, trying SNS')
        pass

    if not found_event:
        # Is this called via SNS topic?
        try:
            message = json.loads(event['Records'][0]['Sns']['Message'])
            if LOGGING_ON: print('This is an SNS event, and this is the message', message)
            event_bucket_name = message['Records'][0]['s3']['bucket']['name']
            event_object_key = message['Records'][0]['s3']['object']['key']
        except KeyError:
            # key doesn't exist
            print('This is not an SNS event either!!')
            # at this point I cannot continue
            return {
                'statusCode': 200,
                'body': 'Function was called with an unsupported event type.'
            }

    if LOGGING_ON:
        print('This is the object key', event_object_key)
        print('This is the bucket', event_bucket_name)

    object_key_parent = f's3://{event_bucket_name}/{os.path.dirname(event_object_key)}/'

    # process object key
    match  = re.match(PATTERN, event_object_key)
    if not match:
        print(f'SKIPPING: Cannot match {event_object_key} as AWS Config file, skipping.')
        return {
            'statusCode': 200,
            'body': 'Object key is not supported, this is not an AWS Config file.'
        }
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
            return {
                'statusCode': 200,
                'body': 'ConfigSnapshot files are disabled in the function\'s environment variables.'
            }
    elif 'ConfigHistory' in event_object_key:
        dataSource = 'ConfigHistory'
        # If not enabled, I can return
        if not isPartitionConfigHistory:
            print(f'SKIPPING: {event_object_key} is a ConfigHistory. These records are disabled in the function\'s environment variables.')
            return {
                'statusCode': 200,
                'body': 'ConfigHistory files are disabled in the function\'s environment variables.'
            }
    else:
        # I can never get here, if the string passed the regex where ConfigSnapshot and ConfigHistory are checks
        print(f'ERROR: {event_object_key} is neither ConfigSnapshot nor ConfigHistory')
        return {
            'statusCode': 200,
            'body': 'Object key is not supported, this is not an AWS Config file.'
        }

    # Considering the use case where many objects are added to the same s3 path at the same time
    # Check if partition exists: need both to avoid calling Athena API too much and create the partition only if it's not there
    # There's no need to create a partition on an S3 path that already exist - Athena will find new files in there
    if not partition_exists(accountid, date, region, dataSource):
        # Create the partition if it doesn't exist
        # I just checked, but another Lambda running on another S3 object may come in between
        add_partition_if_not_exists(accountid, region, date, object_key_parent, dataSource)
        print(f"Partition created for {accountid}, {date}, {region}, {dataSource}")
    else:
        print(f"Partition already exists for {accountid}, {date}, {region}, {dataSource}")

    return {
            'statusCode': 200,
            'body': 'Partition available for {accountid}, {date}, {region}, {dataSource}.'
        }



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


# Resource deletion info comes only from History records
# These must always be indexed
# TODO delete
def contains_deleted_resource_DEPRECATED(bucket_name, object_key):
    try:
        # parse the object name before loading it
        # if ':' is encoded as '%3A' in the object key, the load will fail
        decoded_object_key = unquote(object_key)
        print(f'Loading object {decoded_object_key} of bucket {bucket_name} to check it has resource deleted notifications')
        obj = s3.get_object(Bucket=bucket_name, Key=decoded_object_key)
            
        # Read the gzipped JSON data from the S3 object
        gz_data = obj['Body'].read()
        json_data = gzip.decompress(gz_data).decode('utf-8')

        # Load the JSON data into a dictionary
        data = json.loads(json_data)

        for item in data.get('configurationItems', []):
            print(f"Current configurationItemStatus: {item.get('configurationItemStatus')}")

            if item.get('configurationItemStatus') == 'ResourceDeleted':
                return True
        return False

    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print(f"Error: The S3 object does not exist.")
        else:
            print(f"Error: {e}")
        raise e
    except Exception as e:
        print(f"Error: {e}")
        raise e

# TODO DEPRECATED
def add_partition_DEPRECATED(accountid, region, date, location, dataSource):
    execute_query(f"""
        ALTER TABLE {TABLE_NAME}
        ADD PARTITION (accountid='{accountid}', dt='{date}', region='{region}', dataSource='{dataSource}')
        LOCATION '{location}'
    """)

# TODO DEPRECATED
def drop_partition_DEPRECATED(accountid, region, date, dataSource):
    execute_query(f"""
        ALTER TABLE {TABLE_NAME}
        DROP IF EXISTS PARTITION (accountid='{accountid}', dt='{date}', region='{region}', dataSource='{dataSource}')
    """)

# TODO DEPRECATED
def execute_query_DEPRECATED(query):
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
    
    query_execution_id = start_query_response['QueryExecutionId']
    print(f'Query started with execution ID: {query_execution_id}')


    is_query_running = True
    while is_query_running:
        time.sleep(1)
        execution_status = athena.get_query_execution(
            QueryExecutionId=query_execution_id # start_query_response['QueryExecutionId']
        )


        #query_state = execution_status['QueryExecution']['Status']['State']
        #is_query_running = query_state in ('RUNNING', 'QUEUED')

        #if not is_query_running and query_state != 'SUCCEEDED':
        #    raise AthenaException('Query failed')
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




