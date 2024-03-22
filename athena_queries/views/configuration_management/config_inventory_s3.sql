CREATE OR REPLACE VIEW "config_inventory_s3" AS 
SELECT DISTINCT
  "configurationItem"."awsAccountId" "AccountId"
, "configurationItem"."awsregion" "Region"
, "configurationItem"."arn" "ARN"
, "configurationItem"."resourceName" "BucketName"
, "configurationItem"."tags"['TAG1'] "TAG1"
, "configurationItem"."tags"['TAG2'] "TAG2"
, "configurationItem"."tags"['TAG3'] "TAG3"
, "configurationItem"."tags"['TAG4'] "TAG4"
, "configurationItem"."tags" "AllTags"
, "configurationItem"."configurationitemcapturetime" "LastConfigSnapshot"
, "configurationItem"."resourcecreationtime" "CreationTime"
, "json_extract_scalar"("configurationItem"."configuration", '$.creationDate') "CreationDate"
FROM
  (aws_config_configuration_snapshots
CROSS JOIN UNNEST("configurationitems") t (configurationItem))
WHERE ("configurationItem"."resourcetype" = 'AWS::S3::Bucket')
