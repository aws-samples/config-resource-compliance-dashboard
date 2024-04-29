CREATE EXTERNAL TABLE `cid_crcd_config`(
  `fileversion` string COMMENT 'from deserializer', 
  `configsnapshotid` string COMMENT 'from deserializer', 
  `configurationitems` array<struct<configurationitemversion:string,configurationitemcapturetime:string,configurationstateid:bigint,awsaccountid:string,configurationitemstatus:string,resourcetype:string,resourceid:string,resourcename:string,arn:string,awsregion:string,availabilityzone:string,configurationstatemd5hash:string,configuration:string,supplementaryconfiguration:map<string,string>,tags:map<string,string>,resourcecreationtime:string>> COMMENT 'from deserializer')
PARTITIONED BY ( 
  `accountid` string, 
  `dt` string, 
  `region` string)
ROW FORMAT SERDE 
  'org.openx.data.jsonserde.JsonSerDe' 
WITH SERDEPROPERTIES ( 
  'case.insensitive'='false', 
  'mapping.arn'='ARN', 
  'mapping.availabilityzone'='availabilityZone', 
  'mapping.awsaccountid'='awsAccountId', 
  'mapping.awsregion'='awsRegion', 
  'mapping.configsnapshotid'='configSnapshotId', 
  'mapping.configurationitemcapturetime'='configurationItemCaptureTime', 
  'mapping.configurationitems'='configurationItems', 
  'mapping.configurationitemstatus'='configurationItemStatus', 
  'mapping.configurationitemversion'='configurationItemVersion', 
  'mapping.configurationstateid'='configurationStateId', 
  'mapping.configurationstatemd5hash'='configurationStateMd5Hash', 
  'mapping.fileversion'='fileVersion', 
  'mapping.resourceid'='resourceId', 
  'mapping.resourcename'='resourceName', 
  'mapping.resourcetype'='resourceType', 
  'mapping.supplementaryconfiguration'='supplementaryConfiguration') 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.IgnoreKeyTextOutputFormat'
LOCATION
  '<S3 Destination>'
TBLPROPERTIES (
  'transient_lastDdlTime'='1713190251')