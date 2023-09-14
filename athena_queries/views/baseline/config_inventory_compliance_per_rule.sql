CREATE OR REPLACE VIEW ${athena_database_name}.config_inventory_compliance_per_rule AS
SELECT DISTINCT
a."AccountId"
, a."Region"
, a."Date"
, a."ResourceId"
, a."ResourceType"
, a."RuleName"
, a."Compliant"
, b."ConformancePack"
FROM
  ((
    SELECT *
    FROM
      (
      SELECT DISTINCT
        "accountId" "AccountId"
      , "region" "Region"
      , CAST(date_parse("dt", '%Y-%m-%d') AS "Date") "Date"
      , "json_extract_scalar"("configurationItem"."configuration", '$.targetResourceId') "ResourceId"
      , "json_extract_scalar"("configurationItem"."configuration", '$.targetResourceType') "ResourceType"
      , "json_extract_scalar"(rule, '$.configRuleName') "RuleName"
      , "json_extract_scalar"(rule, '$.complianceType') "Compliant"
      , ROW_NUMBER() OVER (PARTITION BY "json_extract_scalar"(rule, '$.configRuleName'), "json_extract_scalar"("configurationItem"."configuration", '$.targetResourceId'), YEAR(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")), MONTH(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")) ORDER BY CAST(date_parse("dt", '%Y-%m-%d') AS "Date") DESC) Rowrank
      FROM
        ((aws_config_configuration_snapshots
      CROSS JOIN UNNEST("configurationitems") t (configurationItem))
      CROSS JOIN UNNEST(CAST("json_extract"("configurationItem"."configuration", '$.configRuleList') AS array(json))) u (rule))
      WHERE ("configurationItem"."resourcetype" = 'AWS::Config::ResourceCompliance')
    )  sub
    WHERE (Rowrank = 1)
)  a
LEFT JOIN (
    SELECT DISTINCT
      "configurationItem"."resourceId" "ConformancePack"
    , "json_extract_scalar"(rule, '$.configRuleName') "RuleName"
    FROM
      ((aws_config_configuration_snapshots
    CROSS JOIN UNNEST("configurationitems") t (configurationItem))
    CROSS JOIN UNNEST(CAST("json_extract"("configurationItem"."configuration", '$.configRuleList') AS array(json))) u (rule))
    WHERE ("configurationItem"."resourcetype" = 'AWS::Config::ConformancePackCompliance')
)  b ON (b.RuleName = a.RuleName))