CREATE EXTERNAL TABLE `aws_cloudtrail_events` (
    `eventVersion` STRING,
    `userIdentity` STRUCT<
        `type`: STRING,
        `principalId`: STRING,
        `arn`: STRING,
        `accountId`: STRING,
        `invokedBy`: STRING,
        `accessKeyId`: STRING,
        `userName`: STRING,
        `sessionContext`: STRUCT<
            `attributes`: STRUCT<
                `mfaAuthenticated`: STRING,
                `creationDate`: STRING>,
            `sessionIssuer`: STRUCT<
                `type`: STRING,
                `principalId`: STRING,
                `arn`: STRING,
                `accountId`: STRING,
                `userName`: STRING>>>,
    `eventTime` STRING,
    `eventSource` STRING,
    `eventName` STRING,
    `awsRegion` STRING,
    `sourceIpAddress` STRING,
    `userAgent` STRING,
    `errorCode` STRING,
    `errorMessage` STRING,
    `requestParameters` STRING,
    `responseElements` STRING,
    `additionalEventData` STRING,
    `requestId` STRING,
    `eventId` STRING,
    `resources` ARRAY<STRUCT<
        `arn`: STRING,
        `accountId`: STRING,
        `type`: STRING>>,
    `eventType` STRING,
    `apiVersion` STRING,
    `readOnly` STRING,
    `recipientAccountId` STRING,
    `serviceEventDetails` STRING,
    `sharedEventID` STRING,
    `vpcEndpointId` STRING
)
PARTITIONED BY (accountid STRING, dt STRING, region STRING )
ROW FORMAT SERDE 'com.amazon.emr.hive.serde.CloudTrailSerde'
STORED AS INPUTFORMAT 'com.amazon.emr.cloudtrail.CloudTrailInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION '<S3 Destination>'
TBLPROPERTIES ('classification'='cloudtrail');