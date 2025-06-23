# AWS Config Resource Compliance Dashboard
# Backfilling producer function, scans your Amazon S3 dashboard bucket and finds all prefixes related to AWS Config.
# The prefix structure of an AWS Config file is as follows (for an AWS Config Snapshot): 
#   ORG-ID/AWSLogs/ACCOUNT-NUMBER/Config/REGION/YYYY/MM/DD/ConfigSnapshot/objectname.json.gz
# For performance reasons, this function identifies all AWS Config prefixes down to REGION.
# These prefixes are sent to an SQS queue that will trigger another function to add them to the dashboard data.

import boto3
import json
import os
import re
from collections import deque

# Reads mandatory environment variables
DASHBOARD_BUCKET_NAME = os.environ["BUCKET_NAME_VAR"]
SQS_QUEUE = os.environ["SQS_QUEUE_URL_VAR"]
ORGANIZATION_ID = os.environ["ORGANIZATION_ID"]

# SQS and S3 client
sqs = boto3.client('sqs')
s3 = boto3.client('s3')

LOGGING_ON = False  # enables additional logging to CloudWatch

# This regular expressions pattern is compatible with how ControlTower Config logs AND also with how Config Logs are stored in S3 in standalone account
# Structure for Config Snapshots: ORG-ID/AWSLogs/ACCOUNT-NUMBER/Config/REGION/YYYY/MM/DD/ConfigSnapshot/objectname.json.gz
# Object name follows this pattern: ACCOUNT-NUMBER_Config_REGION_ConfigSnapshot_TIMESTAMP-YYYYMMDDHHMMSS_RANDOM-TEXT.json.gz
# For example: 123412341234_Config_eu-north-1_ConfigSnapshot_20240306T122755Z_09c5h4kc-3jc7-4897-830v-d7a858325638.json.gz
# This function needs just to identify the folders until the region, then the processing part can 
# generate the dates and add a partition in case the S3 path exists
PATTERN_REGION = r'^(?P<org_id>[\w-]+)?/?AWSLogs/(?P<account_id>\d+)/Config/(?P<region>[\w-]+)/$'
PATTERN_REGION_COMPILED = re.compile(PATTERN_REGION)

def lambda_handler(event, context):
    # get the ORG-ID from env variables and then build the path that points to CloudTrail files, 
    # must work on a single account too
    exclude = None
    if ORGANIZATION_ID:
        exclude = f'{ORGANIZATION_ID}/AWSLogs/{ORGANIZATION_ID}'
        print(f'Excluding path: {exclude}')

    prefix = ''
    if ORGANIZATION_ID:
        # We can directly start from this and skip 2 iterations
        # The default value starts from the beginning of the bucket
        prefix = f'{ORGANIZATION_ID}/AWSLogs'

    try:
        all_prefixes = set()
        prefixes_to_explore = deque([prefix])
        paginator = s3.get_paginator('list_objects_v2')

        while prefixes_to_explore:
            current_prefix = prefixes_to_explore.popleft()
            
            # Buckets with many objects, or that also store CloudTrail files will make the Lambda time out 
            # before finding all the relevant AWS Config records
            # Here we use the list_objects_v2 API with the delimiter parameter
            page_iterator = paginator.paginate(
                Bucket=DASHBOARD_BUCKET_NAME,
                Prefix=current_prefix,
                Delimiter='/'
            )

            for page in page_iterator:
                if 'CommonPrefixes' in page:
                    for common_prefix in page['CommonPrefixes']:
                        prefix_path = common_prefix['Prefix']

                        # these prefixes do not contain AWS Config files
                        if not ((exclude and prefix_path.startswith(exclude)) 
                                or ('/OversizedChangeNotification/' in prefix_path)
                                or ('/CloudTrail' in prefix_path)
                                or ('/CloudTrail-Digest' in prefix_path)
                            ):

                            # avoiding duplicates
                            if prefix_path not in all_prefixes:
                                if matches_config_pattern_region(prefix_path):
                                    if LOGGING_ON: print(f'Found Config prefix: {prefix_path}')
                                    all_prefixes.add(prefix_path)
                                    # send it directly to SQS
                                    payload = {
                                        "Records": [{
                                            "s3": {
                                                "object": {"key": prefix_path},
                                                "bucket": {"name": DASHBOARD_BUCKET_NAME}
                                            }
                                        }]
                                    }
                                    sqs.send_message(
                                        QueueUrl=SQS_QUEUE, 
                                        MessageBody=json.dumps(payload)
                                    )
                                else:
                                    # still a possibly valid AWS Config prefix that needs scanning
                                    if LOGGING_ON: print(f'Exploring prefix: {prefix_path}')
                                    prefixes_to_explore.append(prefix_path)
                        else:
                            # the folders checked above are always excluded
                            if LOGGING_ON: print(f'Excluding prefix: {prefix_path}')
        
        print(f'Found {len(all_prefixes)} prefixes')

        return {
            'statusCode': 200,
            'body': {
                'prefixes': sorted(list(all_prefixes)),
                'total_count': len(all_prefixes)
            }
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }

def matches_config_pattern_region(key: str) -> bool:
    """Two-stage check for Config files"""
    # Quick check before expensive regex
    if not ('/Config/' in key):
        return False

    # Only perform regex if basic pattern matches
    return bool(re.match(PATTERN_REGION_COMPILED, key))
    