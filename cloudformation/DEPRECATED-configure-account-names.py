"""Configure Account Names Lambda

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
                create_view_query = build_view_query(athena)
                #create_view_query = f"""
                #CREATE OR REPLACE VIEW {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} AS
                #SELECT 
                #    id as account_id,
                #    payer_id as payer_account_id,
                #    parent as organization_unit,
                #    name as account_name
                #FROM "{ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_DATABASE}"."{ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_TABLE}"
                #"""

            elif account_map_exists:
                # Account map table has only: account_id, account_name, parent_account_id, parent_account_name
                create_view_query = f"""
                CREATE OR REPLACE VIEW {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} AS
                SELECT 
                    account_id,
                    parent_account_id as payer_account_id,
                    'NO_DATA' as organization_unit,
                    account_name
                FROM "{ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_DATABASE}"."{ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_TABLE}"
                """
            else:
                # This creates a view with no rows, but having these columns
                create_view_query = f"""
                CREATE OR REPLACE VIEW {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} AS
                SELECT 
                    'NO_DATA' as account_id,
                    'NO_DATA' as payer_account_id,
                    'NO_DATA' as organization_unit,
                    'NO_DATA' as account_name
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

def build_view_query(athena):

    # read the hierarchytags of the entire table and iterates through its rows
    query = f"""
    SELECT hierarchytags 
    FROM "{ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_DATABASE}"."{ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_TABLE}"
    """

    logger.info(f"Executing query to extract tags: {query}")
    # execute this query on the organization database
    query_execution_id = execute_athena_query(athena, query, ATHENA_WORKGROUP, ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_DATABASE, ATHENA_QUERY_RESULTS_BUCKET_NAME)
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
        FROM "{ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_DATABASE}"."{ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_TABLE}"
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
    # when developing the function and testing without Cloud Formation, uncomment the line below
    # return True

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