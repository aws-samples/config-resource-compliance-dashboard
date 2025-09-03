# CRCD
# This Lambda function is an AWS Config custom rule that enforces IAM security by detecting users with programmatic access keys.
# Security purpose:
# Enforces the security best practice of avoiding long-term access keys for IAM users. 
# This helps organizations identify users with programmatic access and encourages migration to temporary credentials, IAM roles, 
# or federated access.

# Integration:
# Results feed into the Config Resource Compliance Dashboard (CRCD), providing visibility into IAM security posture across AWS accounts 
# and regions. Non-compliant users appear in dashboard reports for remediation tracking.

# This rule helps maintain IAM security hygiene by continuously monitoring and flagging users with access keys across your AWS organization.

import botocore
import boto3
import datetime
import json
import logging

# Configure the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Set the minimum logging level to INFO in Production


# Set to True to get the lambda to assume the Role attached on the Config Service (useful for cross-account).
# This check does not need cross-account access
ASSUME_ROLE_MODE = False


def lambda_handler(event, context):
    global AWS_CONFIG_CLIENT

    check_defined(event, 'event')
    logger.debug('CRCD-CIRT: Received event: ' + json.dumps(event))


    # Parse invokingEvent to get configuration item
    invoking_event = json.loads(event['invokingEvent'])
    logger.debug('CRCD-CIRT: Received invoking event: ' + json.dumps(invoking_event))

    rule_parameters = {}
    if 'ruleParameters' in event:
        rule_parameters = json.loads(event['ruleParameters'])

    compliance_value = 'NOT_APPLICABLE'
    AWS_CONFIG_CLIENT = get_client('config', event)

    configuration_item = get_configuration_item(invoking_event)
    logger.debug('CRCD-CIRT: Received configuration item: ' + json.dumps(configuration_item))
    
    if is_applicable(configuration_item, event):
        compliance_value = evaluate_change_notification_compliance(
                configuration_item, rule_parameters, event)

    response = AWS_CONFIG_CLIENT.put_evaluations(
       Evaluations=[
           {
               'ComplianceResourceType': invoking_event['configurationItem']['resourceType'],
               'ComplianceResourceId': invoking_event['configurationItem']['resourceId'],
               'ComplianceType': compliance_value,
               'OrderingTimestamp': invoking_event['configurationItem']['configurationItemCaptureTime']
           },
       ],
       ResultToken=event['resultToken'])

def evaluate_change_notification_compliance(configuration_item, rule_parameters, event):
    """
    Evaluate resource compliance for the IAM User.
    Returns: 'COMPLIANT' if the user has no access keys or has only disabled access keys, 'NON_COMPLIANT' if the user has active access keys, or 'NOT_APPLICABLE'
    """
    check_defined(configuration_item, 'configuration_item')
    check_defined(configuration_item['configuration'], 'configuration_item[\'configuration\']')
    if rule_parameters:
        check_defined(rule_parameters, 'rule_parameters')

    resource_type = configuration_item['resourceType']
    
    # Check IAM users for access key compliance - COMPLIANT if no access keys or access key is disabled, NON_COMPLIANT if active access keys exist
    if resource_type == 'AWS::IAM::User':
        iam_client = get_client('iam', event)

        user_name = configuration_item['resourceName']
        logger.info('CRCD-CIRT: checking IAM user ' + user_name)
        
        try:
            response = iam_client.list_access_keys(UserName=user_name)
            access_keys = response.get('AccessKeyMetadata', [])
            
            # Check for active access keys only
            active_keys = [key for key in access_keys if key['Status'] == 'Active']
            logger.info('CRCD-CIRT: Access keys found: ' + str(len(access_keys)) + ', Active keys: ' + str(len(active_keys)))
            
            if active_keys:
                return 'NON_COMPLIANT'
            return 'COMPLIANT'
        except Exception:
            return 'NOT_APPLICABLE'
    
    return 'NOT_APPLICABLE'

# Helper function used to validate input
def check_defined(reference, reference_name):
    if not reference:
        raise Exception('Error: ', reference_name, 'is not defined')
    return reference


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

def get_assume_role_credentials(role_arn):
    sts_client = boto3.client('sts')
    try:
        assume_role_response = sts_client.assume_role(RoleArn=role_arn, RoleSessionName="configLambdaExecution")
        return assume_role_response['Credentials']
    except botocore.exceptions.ClientError as ex:
        # Scrub error message for any internal account info leaks
        if 'AccessDenied' in ex.response['Error']['Code']:
            ex.response['Error']['Message'] = "AWS Config does not have permission to assume the IAM role."
        else:
            ex.response['Error']['Message'] = "InternalError"
            ex.response['Error']['Code'] = "InternalError"
        raise ex

# Based on the type of message get the configuration item
# either from configurationItem in the invoking event
# or using the getResourceConfigHistory API in getConfiguration function.
def get_configuration_item(invokingEvent):
    check_defined(invokingEvent, 'invokingEvent')
    if is_oversized_changed_notification(invokingEvent['messageType']):
        configurationItemSummary = check_defined(invokingEvent['configurationItemSummary'], 'configurationItemSummary')
        return get_configuration(configurationItemSummary['resourceType'], configurationItemSummary['resourceId'], configurationItemSummary['configurationItemCaptureTime'])
    return check_defined(invokingEvent['configurationItem'], 'configurationItem')

# Check whether the message is OversizedConfigurationItemChangeNotification or not
def is_oversized_changed_notification(message_type):
    check_defined(message_type, 'messageType')
    return message_type == 'OversizedConfigurationItemChangeNotification'

# Get configurationItem using getResourceConfigHistory API
# in case of OversizedConfigurationItemChangeNotification
def get_configuration(resource_type, resource_id, configuration_capture_time):
    result = AWS_CONFIG_CLIENT.get_resource_config_history(
        resourceType=resource_type,
        resourceId=resource_id,
        laterTime=configuration_capture_time,
        limit=1)
    configurationItem = result['configurationItems'][0]
    return convert_api_configuration(configurationItem)


# Convert from the API model to the original invocation model
def convert_api_configuration(configurationItem):
    for k, v in configurationItem.items():
        if isinstance(v, datetime.datetime):
            configurationItem[k] = str(v)
    configurationItem['awsAccountId'] = configurationItem['accountId']
    configurationItem['ARN'] = configurationItem['arn']
    configurationItem['configurationStateMd5Hash'] = configurationItem['configurationItemMD5Hash']
    configurationItem['configurationItemVersion'] = configurationItem['version']
    configurationItem['configuration'] = json.loads(configurationItem['configuration'])
    if 'relationships' in configurationItem:
        for i in range(len(configurationItem['relationships'])):
            configurationItem['relationships'][i]['name'] = configurationItem['relationships'][i]['relationshipName']
    return configurationItem

# Check whether the resource has been deleted. If it has, then the evaluation is unnecessary.
def is_applicable(configurationItem, event):
    try:
        check_defined(configurationItem, 'configurationItem')
        check_defined(event, 'event')
    except:
        return True
    
    status = configurationItem['configurationItemStatus']
    eventLeftScope = event['eventLeftScope']
    if status == 'ResourceDeleted':
        logger.info("CRCD-CIRT: Resource Deleted, setting Compliance Status to NOT_APPLICABLE.")
    
    return (status == 'OK' or status == 'ResourceDiscovered') and not eventLeftScope