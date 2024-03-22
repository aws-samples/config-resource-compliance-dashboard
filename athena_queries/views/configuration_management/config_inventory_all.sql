CREATE OR REPLACE VIEW "config_inventory_all" AS 
SELECT DISTINCT
  "accountId" "AccountId"
, "region" "Region"
, "configurationItem"."resourceid" "ResourceId"
, "configurationItem"."resourcename" "ResourceName"
, "configurationItem"."resourcetype" "ResourceType"
, "configurationItem"."availabilityzone" "AvailabiltyZone"
, "configurationItem"."resourcecreationtime" "CreationTime"
FROM
  ("cid_config_athena_database"."aws_config_configuration_snapshots"
CROSS JOIN UNNEST("configurationitems") t (configurationItem))
