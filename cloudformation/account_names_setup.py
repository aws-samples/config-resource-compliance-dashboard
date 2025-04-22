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

# TODO call these from inside the handler, in case of exceptions no error is returned to CFN and it will hang
CRCD_DATABASE_NAME = os.environ["CRCD_DATABASE_NAME"]   
CRCD_ACCOUNT_NAMES_VIEW_NAME = os.environ["CRCD_ACCOUNT_NAMES_VIEW_NAME"]
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
    ''''This is raised in case of Exception while running queries on Athnea or Glue'''
    pass

def lambda_handler(event, context):
    organization_table_exists = False
    account_map_exists = False 

    if event['RequestType'] == 'Delete':
        # bypass for now
        # TODO handle all request types
        send_response(event, context, 'SUCCESS', {})

    try:
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
                payer_id as payer_account_id,  
                name as account_name
            FROM "optimization_data"."organization_data"
            """
        elif account_map_exists:
            create_view_query = f"""
            CREATE OR REPLACE VIEW {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} AS
            SELECT 
                account_id,
                parent_account_id as payer_account_id,
                account_name
            FROM "cid_cur"."account_map"
            """
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
        success = execute_athena_query(create_view_query)
        if success:
            print(f"View {CRCD_DATABASE_NAME}.{CRCD_ACCOUNT_NAMES_VIEW_NAME} created successfully. Data sources: organization_table_exists {organization_table_exists}, account_map_exists {account_map_exists}")
            # Send a successful response back to CloudFormation
            send_response(event, context, 'SUCCESS', {})
        else:
            send_response(event, context, 'FAILED', {'Error': 'Athena query was not successful'})
    except AthenaException as ae:
        # Send a failed response back to CloudFormation
        send_response(event, context, 'FAILED', {'Error': str(ae)})
    except Exception as e:
        # Send a failed response back to CloudFormation
        send_response(event, context, 'FAILED', {'Error': str(e)})


def check_table_exists(database_name, table_name):
    """Check if table exists in Glue Data Catalog"""
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
        raise AthenaException(f'Query failed: {str(e)}')

def execute_athena_query(query):
    print('Executing query:', query)
    try:
        start_query_response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={
                'Database': CRCD_DATABASE_NAME
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
                    'Database': CRCD_DATABASE_NAME,
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

def send_response(event, context, response_status, response_data):
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

def execute_athena_query_DEPRECATED(query):
    print('Executing query:', query)
    start_query_response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={
            'Database': CRCD_DATABASE_NAME
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