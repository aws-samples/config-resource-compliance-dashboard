CREATE OR REPLACE VIEW "config_inventory_ec2" AS 
SELECT DISTINCT
  "configurationItem"."awsAccountId" "AccountId"
, "configurationItem"."awsregion" "Region"
, "json_extract_scalar"("configurationItem"."configuration", '$.instanceId') "InstanceId"
, "configurationItem"."tags"['Name'] "TagName"
, "configurationItem"."tags"['TAG1'] "TAG1"
, "configurationItem"."tags"['TAG2'] "TAG2"
, "configurationItem"."tags"['TAG3'] "TAG3"
, "configurationItem"."tags"['TAG4'] "TAG4"
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
FROM
  (aws_config_configuration_snapshots
CROSS JOIN UNNEST("configurationitems") t (configurationItem))
WHERE ("configurationItem"."resourcetype" = 'AWS::EC2::Instance')
