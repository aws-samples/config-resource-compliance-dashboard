# This works, TODO build the queries according to what table/db exists, only with account names for now


# TODO
# VIEW_IS_STALE: line 1:15: View 'awsdatacatalog.cid_crcd_database.config_test' is stale or in invalid state: column [account_id] of type varchar projected from query view at position 0 cannot be coerced to column [account_id] of type varchar(15) stored in view definition
# A view build from a sys view will be stale if the sys view changes, rebuild if exists?


# TODO this is the policy it needs

# crcd-glue-account-names-policy  
# 
# {
# 	"Version": "2012-10-17",
# 	"Statement": [
# 		{
# 			"Sid": "ReadGlueTables",
# 			"Effect": "Allow",
# 			"Action": "glue:GetTable",
# 			"Resource": [
# 				"arn:aws:glue:eu-west-1:135808949561:catalog",
# 				"arn:aws:glue:eu-west-1:135808949561:database/*",
# 				"arn:aws:glue:eu-west-1:135808949561:table/*",
# 				"arn:aws:glue:eu-west-1:135808949561:table/*/*"
# 			]
# 		},
# 		{
# 			"Sid": "AddSystemView",
# 			"Effect": "Allow",
# 			"Action": "glue:UpdateTable",
# 			"Resource": [
# 				"arn:aws:glue:eu-west-1:135808949561:catalog",
# 				"arn:aws:glue:eu-west-1:135808949561:database/cid_crcd_database",
# 				"arn:aws:glue:eu-west-1:135808949561:table/cid_crcd_database/*"
# 			]
# 		}
# 	]
# }




# -----------------------------


import json
import os
import boto3
import time


# CRCD_TABLE_NAME = os.environ["CRCD_TABLE_NAME"] # TODO probably not used
CRCD_DATABASE_NAME = os.environ["CRCD_DATABASE_NAME"]   
CRCD_ACCOUNT_NAMES_VIEW_NAME = os.environ["CRCD_ACCOUNT_NAMES_VIEW_NAME"]
ATHENA_DATABASE_NAME = os.environ["ATHENA_DATABASE_NAME"]
ATHENA_QUERY_RESULTS_BUCKET_NAME = os.environ["ATHENA_QUERY_RESULTS_BUCKET_NAME"]
ATHENA_WORKGROUP = os.environ['ATHENA_WORKGROUP']
ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_DATABASE = os.environ["ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_DATABASE"]
ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_TABLE = os.environ["ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_TABLE"]
ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_DATABASE = os.environ["ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_DATABASE"]
ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_TABLE = os.environ["ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_TABLE"]

LOGGING_ON = False  # enables additional logging to CloudWatch

# Athena and Glue clients
glue = boto3.client('glue') 
athena = boto3.client('athena')

class AthenaException(Exception):
    ''''This is raised only if the Query is not in state SUCCEEDED'''
    pass

def lambda_handler(event, context):
    organization_table_exists = False
    account_map_exists = False 

    # Check which tables exist
    if check_table_exists(ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_DATABASE, ACCOUNT_NAMES_SOURCE_ORGANIZATION_DATA_TABLE):
        organization_table_exists = True
    else:
        account_map_exists = check_table_exists(ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_DATABASE, ACCOUNT_NAMES_SOURCE_ACCOUNT_MAP_TABLE)

    # Prepare CREATE OR REPLACE VIEW query based on table existence
    if organization_table_exists:
        create_view_query = f"""
        CREATE OR REPLACE VIEW {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} AS
        SELECT 
            id as account_id,
            arn as account_arn,
            email as account_email,
            name as account_name,
            parentid as parent_id
        FROM "optimization_data"."organization_data"
        """
    elif account_map_exists:
        create_view_query = f"""
        CREATE OR REPLACE VIEW {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} AS
        SELECT 
            account_id,
            'ARN' as account_arn,
            'EMAIL' as account_email,
            account_name,
            parent_account_id as parent_id
        FROM "cid_cur"."account_map"
        """
    else:
        # This creates a view with no rows, but having these columns
        create_view_query = f"""
        CREATE OR REPLACE VIEW {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} AS
        SELECT 
            'NO_TABLES_EXIST' as account_id,
            'NO_TABLES_EXIST' as account_arn,
            'NO_TABLES_EXIST' as account_email,
            'NO_TABLES_EXIST' as account_name,
            'NO_TABLES_EXIST' as parent_id
        WHERE false
        """

    # Execute the view creation query
    success = execute_athena_query(create_view_query)
    
    return {
        'statusCode': 200 if success else 500,
        'body': {
            'message': 'View created successfully' if success else 'Failed to create view',
            'optimization_table_exists': organization_table_exists,
            'account_map_exists': account_map_exists,
            'view_name': f"{CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME}"
        }
    }


def check_table_exists(database_name, table_name):
    """Check if table exists in Glue Data Catalog"""
    if LOGGING_ON:
        print(f"Checking existence of table {table_name} on database {database_name}")

    try:
        glue.get_table(DatabaseName=database_name, Name=table_name)
        if LOGGING_ON:
            print("Table exists")
        return True
    except glue.exceptions.EntityNotFoundException:
        if LOGGING_ON:
            print("Table does not exist")
        return False
    except Exception as e:
        print(f"Error checking table existence: {str(e)}")
        return False

def execute_athena_query(query):
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

def execute_athena_query_DEPRECATED(query):
    print('Executing query:', query)
    start_query_response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': ATHENA_DATABASE_NAME
        },
        ResultConfiguration={
            'OutputLocation': f's3://{ATHENA_QUERY_RESULTS_BUCKET_NAME}/crcd-account-names-setup',
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