-- WIP
CREATE OR REPLACE VIEW "config_inventory_vpc" AS 
SELECT DISTINCT
  "configurationItem"."awsAccountId" "AccountId"
, "configurationItem"."awsregion" "Region"
, "configurationItem"."resourceid" "ResourceId"
, "configurationItem"."tags"['Name'] "TagName"
, "configurationItem"."tags"['TAG1'] "TAG1"
, "configurationItem"."tags"['TAG2'] "TAG2"
, "configurationItem"."tags"['TAG3'] "TAG3"
, "configurationItem"."tags"['TAG4'] "TAG4"
, "configurationItem"."tags" "AllTags"
, "json_extract_scalar"("configurationItem"."configuration", '$.isDefault') "IsDefault"
, "json_extract_scalar"("configurationItem"."configuration", '$.cidrBlockAssociationSet[0].cidrBlock') "CidrBlock0"
, "json_extract_scalar"("configurationItem"."configuration", '$.cidrBlockAssociationSet[1].cidrBlock') "CidrBlock1"
, "json_extract_scalar"("configurationItem"."configuration", '$.cidrBlockAssociationSet[2].cidrBlock') "CidrBlock2"
, "json_extract_scalar"("configurationItem"."configuration", '$.cidrBlockAssociationSet[3].cidrBlock') "CidrBlock3"
, "json_extract_scalar"("configurationItem"."configuration", '$.cidrBlockAssociationSet[4].cidrBlock') "CidrBlock4"
FROM
  (cid_config_athena_database.aws_config_configuration_snapshots
CROSS JOIN UNNEST("configurationitems") t (configurationItem))
WHERE ("configurationItem"."resourcetype" = 'AWS::EC2::VPC')
