CREATE OR REPLACE VIEW ${athena_database_name}.config_inventory_compliance AS
SELECT DISTINCT
  a."AccountId"
, a."Region"
, a."Date"
, a."ResourceId"
, a."ResourceType"
, a."ComplianceType"
FROM
  (
   SELECT *
   FROM
     (
      SELECT DISTINCT
        "accountId" "AccountId"
      , "region" "Region"
      , CAST(date_parse("dt", '%Y-%m-%d') AS "Date") "Date"
      , "json_extract_scalar"("configurationItem"."configuration", '$.targetResourceId') "ResourceId"
      , "json_extract_scalar"("configurationItem"."configuration", '$.targetResourceType') "ResourceType"
      , "json_extract_scalar"("configurationItem"."configuration", '$.complianceType') "ComplianceType"
      , ROW_NUMBER() OVER (PARTITION BY "json_extract_scalar"("configurationItem"."configuration", '$.targetResourceId'), YEAR(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")), MONTH(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")) ORDER BY CAST(date_parse("dt", '%Y-%m-%d') AS "Date") DESC) Rowrank
      FROM
        (cid_crcd_config
      CROSS JOIN UNNEST("configurationitems") t (configurationItem)) t1
      WHERE ("configurationItem"."resourceType" = 'AWS::Config::ResourceCompliance')
   )  sub
   WHERE (Rowrank = 1)
)  a