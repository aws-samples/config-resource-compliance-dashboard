import datetime
import re
import boto3
import os

TABLE_NAME = ""
DATABASE_NAME = os.environ["DATABASE_NAME"]
ATHENA_QUERY_RESULTS_BUCKET_NAME = os.environ["ATHENA_QUERY_RESULTS_BUCKET_NAME"]
REGION = os.environ['REGION']
ACCOUNT_ID = None # Determined at runtime
WORKGROUP = os.environ['WORKGROUP']

athena = boto3.client('athena')

class AthenaException(Exception):
    pass

def lambda_handler(event, context):
    global ACCOUNT_ID

    object_key = event['Records'][0]['s3']['object']['key']
    match = get_object_key_match(object_key)
    if match == 0:
        return
    
    ACCOUNT_ID = context.invoked_function_arn.split(':')[4]
    object_key_parent = 's3://{bucket_name}/{object_key_parent}/'.format(
        bucket_name=event['Records'][0]['s3']['bucket']['name'],
        object_key_parent=os.path.dirname(object_key))
    accountid = get_accountid(match)
    region = get_region(match)
    date = get_date(match).strftime('%Y-%m-%d')
    
    drop_partition(accountid, region, date)
    add_partition(accountid, region, date, object_key_parent)
    
def get_object_key_match(object_key):
    global ACCOUNT_ID
    global TABLE_NAME
    
    # Matches object keys like AWSLogs/123456789012/Config/us-east-1/2018/4/11/ConfigSnapshot/123456789012_Config_us-east-1_ConfigSnapshot_20180411T054711Z_a970aeff-cb3d-4c4e-806b-88fa14702hdb.json.gz
    if (re.match('^AWSLogs/(\d+)/Config/([\w-]+)/(\d+)/(\d+)/(\d+)/ConfigSnapshot/[^\\\]+$', object_key)):
        TABLE_NAME = os.environ["CONFIG_TABLE_NAME"]
        print('Adding partitions for Configuration Snapshot object key', object_key)
        return re.match('^AWSLogs/(\d+)/Config/([\w-]+)/(\d+)/(\d+)/(\d+)/ConfigSnapshot/[^\\\]+$', object_key)
        
    # Matches object keys like AWSLogs/123456789012/CloudTrail/us-east-1/2018/4/11/123456789012_CloudTrail_us-east-1_20180411T054711Z_a970aeff-cb3d-4c4e-806b-88fa14702hdb.json.gz
    if (re.match('^AWSLogs/(\d+)/CloudTrail/([\w-]+)/(\d+)/(\d+)/(\d+)/[^\\\]+$', object_key)):
        TABLE_NAME = os.environ["CLOUDTRAIL_TABLE_NAME"]
        print('Adding partitions for CloudTrail event object key', object_key)
        return re.match('^AWSLogs/(\d+)/CloudTrail/([\w-]+)/(\d+)/(\d+)/(\d+)/[^\\\]+$', object_key)
    print('Ignoring event for non-Configuration Snapshot nor CloudTrail event object key', object_key)
    return 0

def get_accountid(match):
    print('AccountId:', match.group(1))
    return match.group(1)

def get_region(match):
    return match.group(2)

def get_date(match):
    return datetime.date(int(match.group(3)), int(match.group(4)), int(match.group(5)))
    
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
        athena_query_results_bucket = ATHENA_QUERY_RESULTS_BUCKET_NAME,
        account_id=ACCOUNT_ID,
        region=REGION)
    start_query_response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': DATABASE_NAME
        },
        ResultConfiguration={
            'OutputLocation': query_output_location,
        },
        WorkGroup=WORKGROUP
    )
    print('Query started')
    
    is_query_running = True
    while is_query_running:
        get_query_execution_response = athena.get_query_execution(
            QueryExecutionId=start_query_response['QueryExecutionId']
        )
        query_state = get_query_execution_response['QueryExecution']['Status']['State']
        is_query_running = query_state in ('RUNNING','QUEUED')
        
        if not is_query_running and query_state != 'SUCCEEDED':
            raise AthenaException('Query failed')
    print('Query completed')