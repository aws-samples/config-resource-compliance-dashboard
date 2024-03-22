CREATE OR REPLACE VIEW "config_inventory_iam" AS 
SELECT DISTINCT
  "configurationItem"."awsAccountId" "AccountId"
, "configurationItem"."awsregion" "Region"
, "configurationItem"."resourcetype" "Type"
, "configurationItem"."arn" "ARN"
, "configurationItem"."resourcecreationtime" "CreationTime"
FROM
  (cid_config_athena_database.aws_config_configuration_snapshots
CROSS JOIN UNNEST("configurationitems") t (configurationItem))
WHERE (("configurationItem"."resourcetype" = 'AWS::IAM::User') 
  OR ("configurationItem"."resourcetype" = 'AWS::IAM::Role') 
  OR ("configurationItem"."resourcetype" = 'AWS::IAM::Policy') 
  OR ("configurationItem"."resourcetype" = 'AWS::IAM::Group'))
