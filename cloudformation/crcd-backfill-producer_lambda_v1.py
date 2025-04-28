# producer with org reading

# Required permissions
# {
#     "Version": "2012-10-17",
#     "Statement": [
#         {
#             "Effect": "Allow",
#             "Action": [
#                 "organizations:DescribeOrganization",
#                 "organizations:ListAccounts"
#             ],
#             "Resource": "*"
#         },
#         {
#             "Effect": "Allow",
#             "Action": [
#                 "sts:GetCallerIdentity"
#             ],
#             "Resource": "*"
#         },
#         {
#             "Effect": "Allow",
#             "Action": [
#                 "ec2:DescribeRegions"
#             ],
#             "Resource": "*"
#         }
#     ]
# }
# 



# AWS Config Resource Compliance Dashboard
# Backfilling producer function, scans your Amazon S3 dashboard bucket and finds all files related to AWS Config that are valid.
# These files are sent to an SQS queue that will trigger another function to add them to the dashboard data.
# 
# Valid files
# 1. all Config history records (WIP: we may go back until a certain date, e.g. max 1 year)
# 2. Config snapshot records on all accounts an regions whose date is the last day of the month, from the last day of the month until 5 monhs ago
# 3. Config snapshot records on all accounts an regions whose date is within the last 5 days

import boto3
import json
import os
import re
from datetime import datetime, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Optional


DASHBOARD_BUCKET_NAME = os.environ["BUCKET_NAME_VAR"]
SQS_QUEUE = os.environ["SQS_QUEUE_URL_VAR"]

# How much in the past we want to scan (months)
CONFIG_HISTORY_TIME_LIMIT_MONTHS = 12
CONFIG_SNAPSHOT_TIME_LIMIT_MONTHS = 6

# SQS client
sqs = boto3.client('sqs')

# Create an S3 client
s3 = boto3.client('s3')
  
# Define the batch size of the objects read from S3
batch_size = 500 # was: 500

LOGGING_ON = False  # enables additional logging to CloudWatch

# This regular expressions pattern is compatible with how ControlTower Config logs AND also with how Config Logs are stored in S3 in standalone account
# Structure for Config Snapshots: ORG-ID/AWSLogs/ACCOUNT-NUMBER/Config/REGION/YYYY/MM/DD/ConfigSnapshot/objectname.json.gz
# Object name follows this pattern: ACCOUNT-NUMBER_Config_REGION_ConfigSnapshot_TIMESTAMP-YYYYMMDDHHMMSS_RANDOM-TEXT.json.gz
# For example: 123412341234_Config_eu-north-1_ConfigSnapshot_20240306T122755Z_09c5h4kc-3jc7-4897-830v-d7a858325638.json.gz
PATTERN = r'^(?P<org_id>[\w-]+)?/?AWSLogs/(?P<account_id>\d+)/Config/(?P<region>[\w-]+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<type>ConfigSnapshot|ConfigHistory)/[^//]+$'

# Regular expression to get the timestamp of the AWS Config file from its S3 prefix
# Used to apply filters on files depending on the date
DATE_PATTERN = r'^.*/(\d{4})/(\d{1,2})/(\d{1,2})/.*$'

def lambda_handler(event, context):
  # Initialize the continuation token
  continuation_token = None
  object_counter = 0
  batch_counter = 0

  config_snapshot_counter = 0
  config_history_counter = 0
  potential_object_counter = 0
  actual_object_counter = 0
  
  # This is to register all S3 prefixes that need a partition
  # Especially with ConfigHistory records, an S3 partition (i.e. path) may contain several files and
  # it does not make sense to create the Athena partition for each file, as the partition points to the S3 prefix
  # KEYS: the S3 prefix, keys are unique and adding a key with the same value of an existing key will simply replace the key and its value
  # VALUES: any S3 object belonging to the prefix
  prefixes = dict()

  # Sends to SQS only AWS Config files 
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


  # Create datetime for Config history records limit
  year = config_history_date_limit.year
  month = config_history_date_limit.month
  min_config_history_date = datetime(year, month, 1)
  print (f'This is the minimum date for Config history files: {min_config_history_date}')

  # Get organization details
  org_details = get_organization_details()
        
  # Generate prefixes
  prefixes = generate_config_prefixes(org_details)

  for p in prefixes:
     print(p)




  # Iterate over the object keys in batches
  while True:
    # Get the next batch of objects
    response = list_objects_batched(continuation_token)
    batch_counter +=1

    # Process the objects in the batch
    for obj in response.get('Contents', []):
      object_counter +=1
      key = obj['Key']
          
      # all types of Config files must be sent to the worker
      if can_process(key, min_config_snapshot_date, min_config_history_date):
        if 'ConfigHistory' in key:
          config_history_counter +=1
          if LOGGING_ON: print (f'This is a ConfigHistory: {key}')
        
        if 'ConfigSnapshot' in key:
          config_snapshot_counter +=1
          if LOGGING_ON: print (f'This is a ConfigSnapshot: {key}')

        potential_object_counter += 1
        # fakes an S3 trigger as payload for the SQS message
        payload = {
          "Records": [
            {
              "s3": {
                "object": {
                  "key": key
                },
                "bucket": {
                  "name": DASHBOARD_BUCKET_NAME
                }
              }
            }
          ]
        }
            
        # adding the S3 prefix to the list, this will be processed later
        # multiple files may be in te same prefix, and I need to invoke the partitioner function only once per prefix
        prefix_key = f'{os.path.dirname(key)}'
        # print('This is the object key', key)
        # print(f'[{batch_counter}/{object_counter}] This is the S3 path {prefix_key}')
        prefixes[prefix_key] = payload

        # -------------------------------------------------------------------------------
        # only for development
        # break here after a few objects
        # if object_counter >= 20: break
        # -------------------------------------------------------------------------------
        

    # Check if there are more batches to process
    if response['IsTruncated']:
      continuation_token = response['NextContinuationToken']
    else:
      break
  
  # iterate through the prefixes to add them to the SQS queue
  # must do this at the very end, when I have mapped all the files
  for k in prefixes:
    actual_object_counter += 1
    
    sqs.send_message(
      QueueUrl=SQS_QUEUE, 
      MessageBody=json.dumps(prefixes[k])
    )
    if LOGGING_ON: print(f'Added to SQS queue the object : {k}')

  return {
      'statusCode': 200,
      'body': json.dumps(f'Successfully processed {object_counter} objects in the bucket. Sent to the queue for partitioning {actual_object_counter} objects out of {potential_object_counter} valid AWS Config objects, of which there were {config_history_counter} ConfigHistory and {config_snapshot_counter} ConfigSnapshot records.')
  }

# Define the function to list objects in batches
def list_objects_batched(continuation_token=None):
  try:
    response = s3.list_objects_v2(
      Bucket=DASHBOARD_BUCKET_NAME,
      MaxKeys=batch_size,
      ContinuationToken=continuation_token or ''
    )
  except s3.exceptions.ClientError as e:
    if e.response['Error']['Code'] == 'InvalidArgument':
      print('Invalid continuation token, starting from the beginning.')
      response = s3.list_objects_v2(Bucket=DASHBOARD_BUCKET_NAME, MaxKeys=batch_size)
    else:
      raise e
  
  return response 

# returns true if the given object name corresponds to an AWS Config snapshot or history record
# and it is within the time frame of historical data, i.e. current month and the previous full five months
def can_process(object_key, min_config_snapshot_date, min_config_history_date):
  # process object key
  match  = re.match(PATTERN, object_key)

  # if match it is a config file
  if match:
    if LOGGING_ON: print(f'{object_key} is an AWS Config file, checking its timestamp.')

    # Use regex pattern for date extraction  
    date_match = re.match(DATE_PATTERN, object_key)

    if date_match:
      year, month, day = map(int, date_match.groups())
      config_file_date = datetime(year, month, day)

      if 'ConfigHistory' in object_key:
        if config_file_date < min_config_history_date:
          if LOGGING_ON: print(f'ConfigHistory file is dated {config_file_date}: too old for the dashboard. Skipping.')
          match = False
        else:
          if LOGGING_ON: print(f'ConfigHistory file is dated {config_file_date}: will be send to the SQS queue.')
          match = True
      
      if 'ConfigSnapshot' in object_key:
        # only the last day of the month for the previous CONFIG_SNAPSHOT_TIME_LIMIT_MONTHS months and the last 5-ish days
        match = is_config_snapshot_date_valid(config_file_date)
    else:
      # cannot extract the date from the prefix - should never get here
      print(f'ERROR: Cannot extract the date from prefix {object_key}. Skipping.')
      match = False
  else:
    print(f'Cannot match {object_key} as AWS Config file. Skipping.')
    match = False

  return match
  
def is_config_snapshot_date_valid(config_file_date):
    today = datetime.now().date()
    
    # Check if date is within last 5 days
    five_days_ago = today - timedelta(days=5)
    if five_days_ago <= config_file_date.date() <= today:
        if LOGGING_ON: print(f'ConfigSnapshot file is dated {config_file_date}: will be send to the SQS queue.')
        return True
    
    # Check last days of previous months
    current_year = today.year
    current_month = today.month
    
    # Check previous months until the limit
    for i in range(1, CONFIG_SNAPSHOT_TIME_LIMIT_MONTHS):  
        # Calculate the year and month we're checking
        check_month = current_month - i
        check_year = current_year
        
        # Adjust year if we need to go back to previous year
        if check_month <= 0:
            check_month += 12
            check_year -= 1
            
        # Get the last day of that month
        _, last_day = monthrange(check_year, check_month)
        last_date = datetime(check_year, check_month, last_day).date()
        
        # Compare with config_file_date
        if config_file_date.date() == last_date:
            if LOGGING_ON: print(f'ConfigSnapshot file is dated {config_file_date}: will be send to the SQS queue.')
            return True
    
    if LOGGING_ON: print(f'ConfigSnapshot file is dated {config_file_date}: too old or not a end of month date. Skipping.')
    return False            







def get_organization_details() -> Dict:
    """Get AWS Organization ID and list of account IDs"""
    org_client = boto3.client('organizations')
    
    try:
        # Get Organization ID
        org_response = org_client.describe_organization()
        org_id = org_response['Organization']['Id']
        
        # Get list of all accounts
        accounts = []
        paginator = org_client.get_paginator('list_accounts')
        
        for page in paginator.paginate():
            # Only include ACTIVE accounts
            active_accounts = [
                account['Id'] 
                for account in page['Accounts'] 
                if account['Status'] == 'ACTIVE'
            ]
            accounts.extend(active_accounts)
            
        return {
            "organization_id": org_id,
            "account_ids": accounts,
            "is_organization": True
        }
        
    except org_client.exceptions.AWSOrganizationsNotInUseException:
        # Not using Organizations, return current account only
        sts_client = boto3.client('sts')
        current_account = sts_client.get_caller_identity()['Account']
        
        return {
            "organization_id": None,
            "account_ids": [current_account],
            "is_organization": False
        }


def generate_config_prefixes(org_details: Dict) -> List[str]:
    """Generate S3 prefixes for Config files based on organization structure"""
    prefixes = []
    regions = get_enabled_regions()
    
    for account_id in org_details['account_ids']:
        if org_details['is_organization']:
            # Organization structure: {org_id}/AWSLogs/{account_id}/Config/{region}/...
            base_prefix = f"{org_details['organization_id']}/AWSLogs/{account_id}/Config"
        else:
            # Single account structure: AWSLogs/{account_id}/Config/{region}/...
            base_prefix = f"AWSLogs/{account_id}/Config"
            
        # Add region-specific prefixes
        for region in regions:
            prefixes.append(f"{base_prefix}/{region}/")
    
    return prefixes

def get_enabled_regions() -> List[str]:
    """Get list of enabled regions in the account"""
    ec2_client = boto3.client('ec2')
    
    try:
        response = ec2_client.describe_regions()
        return [region['RegionName'] for region in response['Regions']]
    except Exception as e:
        # Fallback to common regions if unable to get enabled regions
        return ['us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'eu-west-1']
