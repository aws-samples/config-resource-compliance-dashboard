import boto3
import json
import datetime
from datetime import timedelta

# Set to True to get the lambda to assume the Role attached on the Config Service (useful for cross-account).
ASSUME_ROLE_MODE = False

# This gets the client after assuming the Config service role
# either in the same AWS account or cross-account.
def get_client(service, event):
    """Return the service boto client. It should be used instead of directly calling the client.
    Keyword arguments:
    service -- the service name used for calling the boto.client()
    event -- the event variable given in the lambda handler
    """
    if not ASSUME_ROLE_MODE:
        return boto3.client(service)
    credentials = get_assume_role_credentials(event["executionRoleArn"])
    return boto3.client(service, aws_access_key_id=credentials['AccessKeyId'],
                        aws_secret_access_key=credentials['SecretAccessKey'],
                        aws_session_token=credentials['SessionToken']
                       )

# Helper function used to validate input
def check_defined(reference, reference_name):
    if not reference:
        raise Exception('Error: ', reference_name, 'is not defined')
    return reference

def get_assume_role_credentials(role_arn):
    sts_client = boto3.client('sts')
    try:
        assume_role_response = sts_client.assume_role(RoleArn=role_arn, RoleSessionName="configLambdaExecution")
        return assume_role_response['Credentials']
    except Exception as ex:
        # Scrub error message for any internal account info leaks
        if 'AccessDenied' in str(ex):
            ex.response['Error']['Message'] = "AWS Config does not have permission to assume the IAM role."
        else:
            ex.response['Error']['Message'] = "InternalError"
            ex.response['Error']['Code'] = "InternalError"
        raise ex

# Evaluate periodic rule compliance
def evaluate_periodic_compliance(rule_parameters, event):
    """
    Check if the root account has been used more than the threshold times in the last 7 days.
    """
    # Get the CloudTrail client
    cloudtrail_client = get_client('cloudtrail', event)
    
    # Get the threshold from rule parameters, default to 5 if not provided
    threshold = 5
    if 'threshold' in rule_parameters:
        try:
            threshold = int(rule_parameters['threshold'])
        except ValueError:
            print(f"Invalid threshold value: {rule_parameters['threshold']}. Using default value 5.")
    
    # Calculate the time range for the last 7 days
    end_time = datetime.datetime.now()
    start_time = end_time - timedelta(days=7)
    
    # Query CloudTrail for root account usage events
    root_usage_count = 0
    try:
        paginator = cloudtrail_client.get_paginator('lookup_events')
        
        # CloudTrail lookup parameters
        lookup_params = {
            'StartTime': start_time,
            'EndTime': end_time,
            'LookupAttributes': [
                {
                    'AttributeKey': 'UserIdentity.type',
                    'AttributeValue': 'Root'
                }
            ]
        }
        
        # Use pagination to handle large result sets
        for page in paginator.paginate(**lookup_params):
            root_usage_count += len(page.get('Events', []))
            
        print(f"Found {root_usage_count} root account usage events in the last 7 days.")
        
        # Determine compliance
        if root_usage_count <= threshold:
            return 'COMPLIANT', f"Root account was used {root_usage_count} times in the last 7 days, which is within the threshold of {threshold}."
        else:
            return 'NON_COMPLIANT', f"Root account was used {root_usage_count} times in the last 7 days, exceeding the threshold of {threshold}."
            
    except Exception as e:
        print(f"Error querying CloudTrail: {str(e)}")
        # In case of error, return NON_COMPLIANT as a precaution
        return 'NON_COMPLIANT', f"Error evaluating compliance: {str(e)}"

def lambda_handler(event, context):
    """
    Main Lambda handler function for AWS Config Custom Rule
    """
    global AWS_CONFIG_CLIENT
    
    check_defined(event, 'event')
    invoking_event = json.loads(event['invokingEvent'])
    rule_parameters = {}
    if 'ruleParameters' in event:
        rule_parameters = json.loads(event['ruleParameters'])
    
    AWS_CONFIG_CLIENT = get_client('config', event)
    
    compliance_value = evaluate_periodic_compliance(rule_parameters)
    
    # For periodic rules, we need to put evaluations for all applicable resources
    # This is just a placeholder - you would need to determine the actual resources to evaluate
    evaluations = [
        {
            'ComplianceResourceType': 'AWS::::Account',  # Replace with actual resource type
            'ComplianceResourceId': event['accountId'],  # Replace with actual resource ID
            'ComplianceType': compliance_value,
            'OrderingTimestamp': datetime.datetime.now()
        }
    ]
    
    # Put evaluations
    response = AWS_CONFIG_CLIENT.put_evaluations(
        Evaluations=evaluations,
        ResultToken=event['resultToken']
    )
    
    return response
