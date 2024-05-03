import datetime
import re
import boto3
import os

TABLE_NAME = ""  # TODO: this can only be the env variable "CONFIG_TABLE_NAME"
ATHENA_DATABASE_NAME = os.environ["ATHENA_DATABASE_NAME"]
ATHENA_QUERY_RESULTS_BUCKET_NAME = os.environ["ATHENA_QUERY_RESULTS_BUCKET_NAME"]
ATHENA_REGION = os.environ['ATHENA_REGION']
ACCOUNT_ID = None  # Determined at runtime, it is the same AWS Account of the lambda function
ATHENA_WORKGROUP = os.environ['ATHENA_WORKGROUP']
LOGGING_ON = False  # enables additional logging to CloudWatch

# This regular expresions is compatible with how ControlTower stores Config logs in S3
# Structure for Config Snapshots: ORG-ID/AWSLogs/ACCOUNT-NUMBER/Config/REGION/YYYY/MM/DD/ConfigSnapshot/objectname.json.gz
# Object name follows this pattern: ACCOUNT-NUMBER_Config_REGION_ConfigSnapshot_TIMESTAMP-YYYYMMDDHHMMSS_RANDOM-TEXT.json.gz
# For example: 123412341234_Config_eu-north-1_ConfigSnapshot_20240306T122755Z_09c5h4kc-3jc7-4897-830v-d7a858325638.json.gz
REGEX_CONFIG_SNAPSHOT_ORGANIZATION = r'^([\w-]+)/AWSLogs/(\d+)/Config/([\w-]+)/(\d+)/(\d+)/(\d+)/(ConfigSnapshot|ConfigHistory)/[^\\]+$'

# This regular expresions is compatible with how Config Logs are stored in S3 for a standalone account
# Structure for Config Snapshots: AWSLogs/ACCOUNT-NUMBER/Config/REGION/YYYY/MM/DD/ConfigSnapshot/objectname.json.gz
# Object name follows the same pattern above
REGEX_CONFIG_SNAPSHOT_STANDALONE = r'^AWSLogs/(\d+)/Config/([\w-]+)/(\d+)/(\d+)/(\d+)/(ConfigSnapshot|ConfigHistory)/[^\\]+$'

OBJECT_KEY_MATCH_STATUS_FAIL = 0
OBJECT_KEY_MATCH_STATUS_CONFIG_SNAPSHOT_ORGANIZATION = 1
OBJECT_KEY_MATCH_STATUS_CONFIG_SNAPSHOT_STANDALONE = 2

athena = boto3.client('athena')

class AthenaException(Exception):
    # This is raised only if the Query is not in state SUCCEEDED
    pass

def lambda_handler(event, context):
    global ACCOUNT_ID

    object_key = event['Records'][0]['s3']['object']['key']
    
    if LOGGING_ON: print('This is the object key', object_key)

    # the object key contains the full name of the S3 object, including the prefixes
    outcome, match = get_object_key_match(object_key)
    if outcome == OBJECT_KEY_MATCH_STATUS_FAIL:
        return

    ACCOUNT_ID = context.invoked_function_arn.split(':')[4]

    object_key_parent = 's3://{bucket_name}/{object_key_parent}/'.format(
        bucket_name=event['Records'][0]['s3']['bucket']['name'],
        object_key_parent=os.path.dirname(object_key))
    
    if LOGGING_ON: print('This is match.groups', match.groups())

    # Extracting account, region and date of the new object from the object key
    # these are positional on the S3 path - the first element has index 1
    # Config has different positioning depending on the account structure
    #
    # Config in Organizations  match.groups ('ORG-ID', 'ACCOUNT-NUMBER', 'REGION', 'YYYY', 'MM', 'DD')
    # Config in Standalone     match.groups ('ACCOUNT-NUMBER', 'REGION', 'YYYY', 'MM', 'DD')
    accountid = get_accountid(outcome, match)
    region = get_region(outcome, match)
    date = get_date(outcome, match).strftime('%Y-%m-%d')
    
    drop_partition(accountid, region, date)
    add_partition(accountid, region, date, object_key_parent)

def get_object_key_match(object_key):
    global ACCOUNT_ID
    global TABLE_NAME

    # Checks whether this is a Config Snapshot on a multi-account organization
    if (re.match(REGEX_CONFIG_SNAPSHOT_ORGANIZATION, object_key)):
        TABLE_NAME = os.environ["CONFIG_TABLE_NAME"]
        print('Adding partitions for Configuration Snapshot (format: AWS Organizations) object key', object_key)
        return OBJECT_KEY_MATCH_STATUS_CONFIG_SNAPSHOT_ORGANIZATION, re.match(REGEX_CONFIG_SNAPSHOT_ORGANIZATION, object_key)
    

    # Checks whether this is a Config Snapshot on a standalone account
    if (re.match(REGEX_CONFIG_SNAPSHOT_STANDALONE, object_key)):
        TABLE_NAME = os.environ["CONFIG_TABLE_NAME"]
        print('Adding partitions for Configuration Snapshot (format: standalone Account) object key', object_key)
        return OBJECT_KEY_MATCH_STATUS_CONFIG_SNAPSHOT_STANDALONE, re.match(REGEX_CONFIG_SNAPSHOT_STANDALONE, object_key)

    # The object is neither, returning OBJECT_KEY_MATCH_STATUS_FAIL will end the function
    print('Ignoring event for non-Configuration Snapshot object key', object_key)
    return OBJECT_KEY_MATCH_STATUS_FAIL, None

def get_accountid(outcome, match):
    # Config in Organizations  match.groups ('ORG-ID', 'ACCOUNT-NUMBER', 'REGION', 'YYYY', 'MM', 'DD')
    # Config in Standalone     match.groups ('ACCOUNT-NUMBER', 'REGION', 'YYYY', 'MM', 'DD')

    result = None 
    if outcome == OBJECT_KEY_MATCH_STATUS_CONFIG_SNAPSHOT_ORGANIZATION:
        result = match.group(2)

    if outcome == OBJECT_KEY_MATCH_STATUS_CONFIG_SNAPSHOT_STANDALONE:
        result = match.group(1)

    if LOGGING_ON: print ('account id:', result)
    return result

def get_region(outcome, match):
    # Config in Organizations  match.groups ('ORG-ID', 'ACCOUNT-NUMBER', 'REGION', 'YYYY', 'MM', 'DD')
    # Config in Standalone     match.groups ('ACCOUNT-NUMBER', 'REGION', 'YYYY', 'MM', 'DD')

    result = None  
    if outcome == OBJECT_KEY_MATCH_STATUS_CONFIG_SNAPSHOT_ORGANIZATION:
        result = match.group(3)

    if outcome == OBJECT_KEY_MATCH_STATUS_CONFIG_SNAPSHOT_STANDALONE:
        result = match.group(2)

    if LOGGING_ON: print ('region:', result)
    return result

def get_date(outcome, match):
    # Config in Organizations  match.groups ('ORG-ID', 'ACCOUNT-NUMBER', 'REGION', 'YYYY', 'MM', 'DD')
    # Config in Standalone     match.groups ('ACCOUNT-NUMBER', 'REGION', 'YYYY', 'MM', 'DD')

    result = None
    if outcome == OBJECT_KEY_MATCH_STATUS_CONFIG_SNAPSHOT_ORGANIZATION:
        result = datetime.date(int(match.group(4)), int(match.group(5)), int(match.group(6)))

    if outcome == OBJECT_KEY_MATCH_STATUS_CONFIG_SNAPSHOT_STANDALONE:
        result = datetime.date(int(match.group(3)), int(match.group(4)), int(match.group(5)))

    return result

def add_partition(accountid_partition_value, region_partition_value, dt_partition_value, partition_location):
    execute_query('ALTER TABLE {table_name} ADD PARTITION {partition} location \'{partition_location}\''.format(
        table_name=TABLE_NAME,
        partition=build_partition_string(accountid_partition_value, region_partition_value, dt_partition_value),
        partition_location=partition_location))
        
def drop_partition(accountid_partition_value, region_partition_value, dt_partition_value):
    execute_query('ALTER TABLE {table_name} DROP IF EXISTS PARTITION {partition}'.format(
        table_name=TABLE_NAME,
        partition=build_partition_string(accountid_partition_value, region_partition_value, dt_partition_value)))
        
def build_partition_string(accountid_partition_value, region_partition_value, dt_partition_value):
    return "(accountid='{accountid_partition_value}', dt='{dt_partition_value}', region='{region_partition_value}')".format(
	    accountid_partition_value=accountid_partition_value,
        dt_partition_value=dt_partition_value,
        region_partition_value=region_partition_value)

def execute_query(query):
    print('Executing query:', query)
    query_output_location = 's3://{athena_query_results_bucket}'.format(
        athena_query_results_bucket=ATHENA_QUERY_RESULTS_BUCKET_NAME,
        account_id=ACCOUNT_ID,
        region=ATHENA_REGION)
    start_query_response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': ATHENA_DATABASE_NAME
        },
        ResultConfiguration={
            'OutputLocation': query_output_location,
        },
        WorkGroup=ATHENA_WORKGROUP
    )
    print('Query started')
    
    is_query_running = True
    while is_query_running:
        get_query_execution_response = athena.get_query_execution(
            QueryExecutionId=start_query_response['QueryExecutionId']
        )
        query_state = get_query_execution_response['QueryExecution']['Status']['State']
        is_query_running = query_state in ('RUNNING', 'QUEUED')
        
        if not is_query_running and query_state != 'SUCCEEDED':
            raise AthenaException('Query failed')
    print('Query completed')
