CREATE OR REPLACE VIEW ${athena_database_name}.config_conformance_packs_compliance AS 
SELECT DISTINCT
  a."AccountId"
, a."Region"
, a."Date"
, a."ResourceId"
, a."ResourceName"
, a."ResourceType"
, a."ComplianceType"
, a."CompliantRuleCount"
, a."NonCompliantRuleCount"
, a."TotalRuleCount"
FROM
  (
   SELECT *
   FROM
     (
      SELECT DISTINCT
        "accountId" "AccountId"
      , "region" "Region"
      , CAST(date_parse("dt", '%Y-%m-%d') AS "Date") "Date"
      , "configurationItem"."resourceId" "ResourceId"
      , "configurationItem"."resourceName" "ResourceName"
      , "configurationItem"."resourceType" "ResourceType"
      , "json_extract_scalar"("configurationItem"."configuration", '$.complianceType') "ComplianceType"
      , "json_extract_scalar"("configurationItem"."configuration", '$.compliantRuleCount') "CompliantRuleCount"
      , "json_extract_scalar"("configurationItem"."configuration", '$.nonCompliantRuleCount') "NonCompliantRuleCount"
      , "json_extract_scalar"("configurationItem"."configuration", '$.totalRuleCount') "TotalRuleCount"
      , ROW_NUMBER() OVER (PARTITION BY "configurationItem"."resourceId", YEAR(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")), MONTH(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")) ORDER BY CAST(date_parse("dt", '%Y-%m-%d') AS "Date") DESC) Rowrank
      FROM
        (cid_crcd_config
      CROSS JOIN UNNEST("configurationitems") t (configurationItem))
      WHERE ("configurationItem"."resourcetype" = 'AWS::Config::ConformancePackCompliance')
   )  sub
   WHERE (Rowrank = 1)
)  a
