"""Configure Account Names Lambda

Version that creates a CRCD table on CRCD database pointing to the S3 file where
CID data collection saves organization_data. This was parked because now the bug that
made it impossible to JOIN CRCD table (case sensitive) with organization_data is solved.



TODO add permissions to CFN templete
This Lambda requires the following IAM permissions:
- glue:GetTable, glue:GetPartitions - Read source table metadata
- glue:CreateTable, glue:BatchCreatePartition - Create CRCD tables and partitions
- athena:StartQueryExecution, athena:GetQueryExecution - Execute and poll CREATE/DROP VIEW queries
- s3:PutObject, s3:GetObject, s3:GetBucketLocation - Store Athena query results
- logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents - CloudWatch logging



crcd-read-organization-tags for reference
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowQueryForTags",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::crcddev-cid-data767398072207",
                "arn:aws:s3:::crcddev-cid-data767398072207/*"
            ]
        },
        {
            "Sid": "AllowGetQueryResults",
            "Effect": "Allow",
            "Action": [
                "athena:GetQueryResults"
            ],
            "Resource": [
                "arn:aws:athena:eu-west-1:767398072207:workgroup/crcd-dashboard"
            ]
        }
    ]
}
"""

import re
import json
import os
import boto3
import time
import logging
from botocore.exceptions import ClientError

# Configure the logger
# This lambda is run once
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get the necessary parameters from the environment variables
# All are required and will raise a KeyError if the environment variable doesn't exist
CRCD_DATABASE_NAME = os.environ["CRCD_DATABASE_NAME"]
CRCD_ORGANIZATION_DATA_TABLE = os.environ["CRCD_ORGANIZATION_DATA_TABLE"] # cid_crcd_sys_organization_data or config_sys_organization_data
CRCD_ACCOUNT_NAMES_VIEW_NAME = os.environ["CRCD_ACCOUNT_NAMES_VIEW_NAME"]
ATHENA_QUERY_RESULTS_BUCKET_NAME = os.environ["ATHENA_QUERY_RESULTS_BUCKET_NAME"]
ATHENA_WORKGROUP = os.environ["ATHENA_WORKGROUP"]
ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_DATABASE = os.environ["ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_DATABASE"]
ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_TABLE = os.environ["ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_TABLE"]
ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_DATABASE = os.environ["ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_DATABASE"]
ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_TABLE = os.environ["ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_TABLE"]

class AthenaException(Exception):
    ''''This is raised in case of Exception while running queries on Athena or Glue'''
    pass

def lambda_handler(event, context):
    logger.info(f"Request received:\n{json.dumps(event)}")

    organization_table_exists = False
    account_map_exists = False 

    # Athena and Glue clients
    glue = boto3.client('glue') 
    athena = boto3.client('athena')


    if event['RequestType'] == 'Delete':
        # TODO delete also CRCD_ORGANIZATION_DATA_TABLE if it exists

        # remove view CRCD_ACCOUNT_NAMES_VIEW_NAME
        delete_view_query = f"""
        DROP VIEW IF EXISTS {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME}
        """

        logger.info(f"Deleting view with SQL: {delete_view_query}")

        try:
            # Execute the view creation query    
            success = execute_athena_query(athena, delete_view_query, ATHENA_WORKGROUP, CRCD_DATABASE_NAME, ATHENA_QUERY_RESULTS_BUCKET_NAME)
            if success:
                logger.info(f"View {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} deleted successfully.")
                # Send a successful response back to CloudFormation
                send_response(event, context, 'SUCCESS', {})
            else:
                logger.error(f"View {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} was not deleted successfully.")
                send_response(event, context, 'FAILED', {'Error': 'Athena query was not successful: cloud not delete view.'})
        except AthenaException as ae:
            # Send a failed response back to CloudFormation
            logger.error(f'Exception during query execution: {str(ae)}')
            send_response(event, context, 'FAILED', {'Error': str(ae)})
        except Exception as e:
            # Send a failed response back to CloudFormation
            logger.error(f'Exception during function execution: {str(e)}')
            send_response(event, context, 'FAILED', {'Error': str(e)})

    else:
        try:
            success = False

            # Check which tables exist
            if check_table_exists(glue, ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_DATABASE, ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_TABLE):
                # Organization data collection is the preferred source of account name information
                organization_table_exists = True
            else:
                account_map_exists = check_table_exists(glue, ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_DATABASE, ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_TABLE)

            # Prepare CREATE OR REPLACE VIEW query based on table existence
            if organization_table_exists:
                success = create_organization_table(glue, athena)
            elif account_map_exists:
                create_view_query = f"""
                CREATE OR REPLACE VIEW {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} AS
                SELECT 
                    account_id,
                    parent_account_id as payer_account_id,
                    account_name
                FROM "{ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_DATABASE}"."{ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_TABLE}"
                """
                # Execute the view creation query
                success = execute_athena_query(athena, create_view_query, ATHENA_WORKGROUP, CRCD_DATABASE_NAME, ATHENA_QUERY_RESULTS_BUCKET_NAME)
            else:
                # This creates a view with no rows, but having these columns
                create_view_query = f"""
                CREATE OR REPLACE VIEW {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} AS
                SELECT 
                    'NO_TABLES_EXIST' as account_id,
                    'NO_TABLES_EXIST' as payer_account_id,
                    'NO_TABLES_EXIST' as account_name
                WHERE false
                """
                # Execute the view creation query
                success = execute_athena_query(athena, create_view_query, ATHENA_WORKGROUP, CRCD_DATABASE_NAME, ATHENA_QUERY_RESULTS_BUCKET_NAME)

            if success:
                logger.info(f"View {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} created successfully. Data sources: organization_table_exists {organization_table_exists}, account_map_exists {account_map_exists}")
                # Send a successful response back to CloudFormation
                send_response(event, context, 'SUCCESS', {})
            else:
                send_response(event, context, 'FAILED', {'Error': 'Athena query was not successful'})
        except AthenaException as ae:
            # Send a failed response back to CloudFormation
            logger.error(f'Exception during query execution: {str(ae)}')
            send_response(event, context, 'FAILED', {'Error': str(ae)})
        except Exception as e:
            # Send a failed response back to CloudFormation
            logger.error(f'Exception during function execution: {str(e)}')
            send_response(event, context, 'FAILED', {'Error': str(e)})

def create_organization_table(glue, athena):
    """Create a CRCD-owned external table and view from organization data source.
    The definition of the organization data source table is case insensitive and cannot join with CRCD table (case-sesitive).
    For this reason, we need to create an external table based on the location of the organization data table.
    """
    success = False

    # STEP 1: prep data
    response = glue.get_table(DatabaseName=ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_DATABASE, Name=ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_TABLE)
    location = response['Table']['StorageDescriptor']['Location']
    logger.info(f"Location of table {ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_TABLE} is {location}")

    partitions = glue.get_partitions(
        DatabaseName=ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_DATABASE,
        TableName=ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_TABLE
    )
    for p in partitions['Partitions']:
        payer_id = p['Values'][0]  # First partition key value
    logger.info(f"Payer ID is {payer_id}")


    # STEP 2: Create the external table in the CRCD database, by copying the structure from the source table and
    # creating a CRCD-owned table based on this location
    # TODO add comments to the columns?
    try:
        glue.create_table(
            DatabaseName=CRCD_DATABASE_NAME,
            TableInput={
                'Name': CRCD_ORGANIZATION_DATA_TABLE,
                'TableType': 'EXTERNAL_TABLE',
                'StorageDescriptor': {
                    'Columns': [
                        {'Name': 'id', 'Type': 'string'},
                        {'Name': 'arn', 'Type': 'string'},
                        {'Name': 'email', 'Type': 'string'},
                        {'Name': 'name', 'Type': 'string'},
                        {'Name': 'status', 'Type': 'string'},
                        {'Name': 'joinedmethod', 'Type': 'string'},
                        {'Name': 'joinedtimestamp', 'Type': 'string'},
                        {'Name': 'hierarchy', 'Type': 'array<struct<id:string,type:string,name:string>>'},
                        {'Name': 'hierarchypath', 'Type': 'string'},
                        {'Name': 'hierarchytags', 'Type': 'array<struct<key:string,value:string>>'},
                        {'Name': 'managementaccountid', 'Type': 'string'},
                        {'Name': 'parent', 'Type': 'string'},
                        {'Name': 'parentid', 'Type': 'string'},
                        {'Name': 'parenttags', 'Type': 'array<struct<key:string,value:string>>'},
                    ],
                    'Location': location,
                    'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
                    'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
                    'SerdeInfo': {
                        'SerializationLibrary': 'org.apache.hive.hcatalog.data.JsonSerDe'
                    }
                },
                'PartitionKeys': [
                    {'Name': 'payer_id', 'Type': 'string'}
                ]
            }
        )
        success = True
    except ClientError as ce:
        success = False
        error_code = ce.response['Error']['Code']  # e.g., 'AlreadyExistsException'
        error_message = ce.response['Error']['Message']
        logger.error(f"Glue error: {error_code} - {error_message}")
        # TODO raise?raise AthenaException(f'Query failed: {str(ce)}')


    #create_external_table_query = f"""
    #CREATE TABLE "{CRCD_DATABASE_NAME}"."{CRCD_ORGANIZATION_DATA_TABLE}"(
    #    "id" string COMMENT 'from deserializer', 
    #    "arn" string COMMENT 'from deserializer', 
    #    "email" string COMMENT 'from deserializer', 
    #    "name" string COMMENT 'from deserializer', 
    #    "status" string COMMENT 'from deserializer', 
    #    "joinedmethod" string COMMENT 'from deserializer', 
    #    "joinedtimestamp" string COMMENT 'from deserializer', 
    #    "hierarchy" array<struct<id:string,type:string,name:string>> COMMENT 'from deserializer',
    #    "hierarchypath" string COMMENT 'from deserializer', 
    #    "hierarchytags" array<struct<key:string,value:string>> COMMENT 'from deserializer', 
    #    "managementaccountid" string COMMENT 'from deserializer', 
    #    "parent" string COMMENT 'from deserializer', 
    #    "parentid" string COMMENT 'from deserializer', 
    #    "parenttags" array<struct<key:string,value:string>> COMMENT 'from deserializer')
    #    PARTITIONED BY ( 
    #    "payer_id" string)
    #    ROW FORMAT SERDE 
    #    'org.apache.hive.hcatalog.data.JsonSerDe' 
    #    STORED AS INPUTFORMAT 
    #    'org.apache.hadoop.mapred.TextInputFormat' 
    #    OUTPUTFORMAT 
    #    'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
    #    LOCATION
    #    '{location}'
    #    TBLPROPERTIES ('transient_lastDdlTime'='1750149550')
    #"""
    # Execute the view creation query    
    #success = execute_athena_query(athena, create_external_table_query, ATHENA_WORKGROUP, CRCD_DATABASE_NAME, ATHENA_QUERY_RESULTS_BUCKET_NAME)

    # STEP 3: add partition
    if success:
        try:
            glue.batch_create_partition(
                DatabaseName=CRCD_DATABASE_NAME,
                TableName=CRCD_ORGANIZATION_DATA_TABLE,
                PartitionInputList=[
                    {
                        'Values': [f'{payer_id}'],  # payer_id value
                        'StorageDescriptor': {
                            'Location': f'{location}payer_id={payer_id}/',
                            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
                            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
                            'SerdeInfo': {'SerializationLibrary': 'org.apache.hive.hcatalog.data.JsonSerDe'}
                        }
                    }
                ]
            )
        except ClientError as ce:
            success = False
            error_code = ce.response['Error']['Code']  # e.g., 'AlreadyExistsException'
            error_message = ce.response['Error']['Message']
            logger.error(f"Glue error: {error_code} - {error_message}")
            # TODO raise?raise AthenaException(f'Query failed: {str(ce)}')

    if success:
        # STEP 3: read all org and account tags to build the view
        create_view_query = build_view_query(athena)

    
        #create_view_query = f"""
        #CREATE OR REPLACE VIEW {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} AS
        #SELECT 
        #    id as account_id,
        #    payer_id as payer_account_id,  
        #    name as account_name
        #FROM "{CRCD_DATABASE_NAME}"."{CRCD_ORGANIZATION_DATA_TABLE}"
        #"""

        # Execute the view creation query    
        success = execute_athena_query(athena, create_view_query, ATHENA_WORKGROUP, CRCD_DATABASE_NAME, ATHENA_QUERY_RESULTS_BUCKET_NAME)

    return success

def build_view_query(athena):

    # read the hierarchytags of the entire table and iterates through its rows
    query = f"""SELECT hierarchytags FROM "{CRCD_DATABASE_NAME}"."{CRCD_ORGANIZATION_DATA_TABLE}" """
    
    logger.info(f"Executing query to extract tags: {query}")
    query_execution_id = execute_athena_query(athena, query, ATHENA_WORKGROUP, CRCD_DATABASE_NAME, ATHENA_QUERY_RESULTS_BUCKET_NAME)
    results = get_query_results(query_execution_id, athena)

    # Skip header row
    data_rows = results[1:]
    
    # Collect all unique keys
    all_keys = set()
    
    logger.info(f"Processing {len(data_rows)} records...")
    for row in data_rows:
        if row and row[0]:  # Check if hierarchytags value exists
            hierarchytags_value = row[0]
            keys = extract_keys_from_hierarchytags(hierarchytags_value)
            all_keys.update(keys)
    
    # Display results
    logger.info("=== All Unique Keys Found in hierarchytags ===")
    query_tags = ""
    for key in sorted(all_keys):
        sanitized_tag_name = sanitize_string(key)
        logger.info(f"  - {key} [{sanitized_tag_name}]")
        query_tags = query_tags + " " + f", TRY(FILTER(hierarchytags, x -> x.key = '{key}')[1].value) as ou_tag_{sanitized_tag_name}"

    
    logger.info(f"Total unique keys: {len(all_keys)}")
    logger.info(f"Final query snippet: {query_tags}")
    
    create_view_query = f"""
        CREATE OR REPLACE VIEW {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} AS
        SELECT 
            id as account_id
            , payer_id as payer_account_id
            , name as account_name
            , parent as organization_unit
            {query_tags}
        FROM "{CRCD_DATABASE_NAME}"."{CRCD_ORGANIZATION_DATA_TABLE}"
        """
    
    logger.info(f"Final query for the view: {create_view_query}")
    return create_view_query

def sanitize_string(input_string):
    """
    Replace spaces and any character that is not a letter or number with '_'
    
    Args:
        input_string: The string to sanitize
        
    Returns:
        Sanitized string with only letters, numbers, and underscores
    """
    # Replace any character that is NOT alphanumeric with underscore
    sanitized = re.sub(r'[^a-zA-Z0-9]', '_', input_string)
    return sanitized

def extract_keys_from_hierarchytags(hierarchytags_value):
    """Extract all keys from a hierarchytags string"""
    keys = set()
    
    # Pattern to match key=value pairs
    pattern = r'key=([^,}\]]+)'
    matches = re.findall(pattern, hierarchytags_value)
    
    for match in matches:
        keys.add(match.strip())
    
    return keys

def check_table_exists(glue, database_name, table_name):
    """Check if table exists in Glue Data Catalog"""
    logger.info(f"Checking existence of table {table_name} on database {database_name}")
    
    try:
        glue.get_table(DatabaseName=database_name, Name=table_name)
        logger.info("Table exists")
        return True
    except glue.exceptions.EntityNotFoundException:
        logger.info("Table does not exist")
        return False
    except Exception as e:
        logger.error(f"Error checking table existence: {str(e)}")
        raise AthenaException(f'Query failed: {str(e)}')

def execute_athena_query(athena, query, athena_workgroup, crcd_database, athena_bucket):
    logger.info(f"Executing query: {query}")
    logger.info(f"ATHENA_WORKGROUP = {athena_workgroup}")

    try:
        start_query_response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={
                'Database': crcd_database
            },
            ResultConfiguration={
                'OutputLocation': f's3://{athena_bucket}',
            },
            WorkGroup=athena_workgroup
        )
        query_execution_id = start_query_response['QueryExecutionId']
        logger.debug(f'Query started with execution ID: {query_execution_id}')

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
                    'Database': crcd_database,
                    'WorkGroup': athena_workgroup,
                    'OutputLocation': f's3://{athena_bucket}'
                }
                logger.error(f'Query failed: {json.dumps(error_details)}')
                raise AthenaException(f'Query failed: {error_reason}')
        
        logger.debug(f'Query completed successfully. Execution ID: {query_execution_id}')
        return query_execution_id
    except Exception as e:
        logger.error(f'Exception during query execution: {str(e)}')
        raise

def get_query_results(query_execution_id, athena):
    """Retrieve query results"""
    results = []
    paginator = athena.get_paginator('get_query_results')
    
    for page in paginator.paginate(QueryExecutionId=query_execution_id):
        for row in page['ResultSet']['Rows']:
            results.append([col.get('VarCharValue', '') for col in row['Data']])
    
    return results

def send_response(event, context, response_status, response_data):
    # TODO developing the function and testing without Cloud Formation, remove the line below
    return True

    """Interacts with the Cloud Formation template that called this Lambda"""
    response_body = json.dumps({
        'Status': response_status,
        'Reason': 'See the details in CloudWatch Log Stream: ' + context.log_stream_name,
        'PhysicalResourceId': context.log_stream_name,
        'StackId': event['StackId'],
        'RequestId': event['RequestId'],
        'LogicalResourceId': event['LogicalResourceId'],
        'Data': response_data
    })

    response_url = event['ResponseURL']
    
    import urllib.request
    req = urllib.request.Request(response_url, data=response_body.encode('utf-8'), method='PUT')
    with urllib.request.urlopen(req) as f:
        print(f.read())
        print(f.info())