CREATE OR REPLACE VIEW "config_inventory_ec2" AS 
SELECT DISTINCT
  a."AccountId"
, a."Region"
, a."Date"
, a."InstanceId"
, a."TagName"
, a."TAG1"
, a."TAG2"
, a."TAG3"
, a."TAG4"
, a."AllTags"
, a."LastConfigSnapshot"
, a."CreationTime"
, a."LaunchTime"
, a."InstanceType"
, a."KeyName"
, a."AmiId"
, a."PrivateIp"
, a."PublicIp"
, a."State"
FROM
  (
   SELECT *
   FROM
     (
      SELECT DISTINCT
        "configurationItem"."awsAccountId" "AccountId"
      , "configurationItem"."awsregion" "Region"
      , CAST(date_parse("dt", '%Y-%m-%d') AS "Date") "Date"
      , "json_extract_scalar"("configurationItem"."configuration", '$.instanceId') "InstanceId"
      , "configurationItem"."tags"['Name'] "TagName"
      , "configurationItem"."tags"['<TAG1>'] "TAG1"
      , "configurationItem"."tags"['<TAG2>'] "TAG2"
      , "configurationItem"."tags"['<TAG3>'] "TAG3"
      , "configurationItem"."tags"['<TAG4>'] "TAG4"
      , "configurationItem"."tags" "AllTags"
      , "configurationItem"."configurationitemcapturetime" "LastConfigSnapshot"
      , "configurationItem"."resourcecreationtime" "CreationTime"
      , "json_extract_scalar"("configurationItem"."configuration", '$.launchTime') "LaunchTime"
      , "json_extract_scalar"("configurationItem"."configuration", '$.instanceType') "InstanceType"
      , "json_extract_scalar"("configurationItem"."configuration", '$.keyName') "KeyName"
      , "json_extract_scalar"("configurationItem"."configuration", '$.imageId') "AmiId"
      , "json_extract_scalar"("configurationItem"."configuration", '$.privateIpAddress') "PrivateIp"
      , "json_extract_scalar"("configurationItem"."configuration", '$.publicIpAddress') "PublicIp"
      , "json_extract_scalar"("configurationItem"."configuration", '$.state.name') "State"
      , ROW_NUMBER() OVER (PARTITION BY "json_extract_scalar"("configurationItem"."configuration", '$.instanceId'), YEAR(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")), MONTH(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")) ORDER BY CAST(date_parse("dt", '%Y-%m-%d') AS "Date") DESC) Rowrank
      FROM
        (cid_crcd_config
      CROSS JOIN UNNEST("configurationitems") t (configurationItem))
      WHERE ("configurationItem"."resourcetype" = 'AWS::EC2::Instance')
   )  sub
   WHERE (Rowrank = 1)
)  a
