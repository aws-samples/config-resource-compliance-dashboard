CREATE OR REPLACE VIEW ${athena_database_name}.config_inventory_compliance AS
SELECT DISTINCT
a."AccountId"
, a."Region"
, a."Date"
, a."ResourceId"
, a."ResourceType"
, a."ComplianceType"
, b."Application"
, b."Environment"
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
      , "json_extract_scalar"("configurationItem"."configuration", '$.complianceType') "ComplianceType"
      , ROW_NUMBER() OVER (PARTITION BY "json_extract_scalar"("configurationItem"."configuration", '$.targetResourceId'), YEAR(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")), MONTH(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")) ORDER BY CAST(date_parse("dt", '%Y-%m-%d') AS "Date") DESC) Rowrank
      FROM
        (aws_config_configuration_snapshots
      CROSS JOIN UNNEST("configurationitems") t (configurationItem)) t1
      WHERE ("configurationItem"."resourceType" = 'AWS::Config::ResourceCompliance')
    )  sub
    WHERE (Rowrank = 1)
)  a
LEFT JOIN (
    SELECT DISTINCT
    "configurationItem"."resourceId" "ResourceId"
    , "configurationItem"."tags"['Application'] "Application"
    , "configurationItem"."tags"['Environment'] "Environment"
    FROM
    (${athena_database_name}.aws_config_configuration_snapshots
    CROSS JOIN UNNEST("configurationitems") t (configurationItem))
)  b ON (b.ResourceId = a.ResourceId))
