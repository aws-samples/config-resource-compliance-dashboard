CREATE EXTERNAL TABLE `aws_config_configuration_snapshots` (
    `fileversion` STRING,
    `configsnapshotid` STRING,
    `configurationitems` ARRAY < STRUCT <
        `configurationItemVersion` : STRING,
        `configurationItemCaptureTime` : STRING,
        `configurationStateId` : BIGINT,
        `awsAccountId` : STRING,
        `configurationItemStatus` : STRING,
        `resourceType` : STRING,
        `resourceId` : STRING,
        `resourceName` : STRING,
        `ARN` : STRING,
        `awsRegion` : STRING,
        `availabilityZone` : STRING,
        `configurationStateMd5Hash` : STRING,
        `configuration` : STRING,
        `supplementaryConfiguration` : MAP <STRING, STRING>,
        `tags` : MAP <STRING, STRING> ,
        `resourceCreationTime` : STRING > >
) 
PARTITIONED BY ( accountid STRING, dt STRING, region STRING )
ROW FORMAT SERDE 
    'org.openx.data.jsonserde.JsonSerDe' 
WITH SERDEPROPERTIES ( 
    'case.insensitive'='false',
    'mapping.fileversion'='fileVersion',
    'mapping.configsnapshotid'='configSnapshotId',
    'mapping.configurationitems'='configurationItems',
    'mapping.configurationitemversion'='configurationItemVersion',
    'mapping.configurationitemcapturetime'='configurationItemCaptureTime',
    'mapping.configurationstateid'='configurationStateId',
    'mapping.awsaccountid'='awsAccountId',
    'mapping.configurationitemstatus'='configurationItemStatus',
    'mapping.resourcetype'='resourceType',
    'mapping.resourceid'='resourceId',
    'mapping.resourcename'='resourceName',
    'mapping.arn'='ARN',
    'mapping.awsregion'='awsRegion',
    'mapping.availabilityzone'='availabilityZone',
    'mapping.configurationstatemd5hash'='configurationStateMd5Hash',
    'mapping.supplementaryconfiguration'='supplementaryConfiguration',
    'mapping.configurationstateid'='configurationStateId'
)
LOCATION '<S3 Destination>';