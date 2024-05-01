CREATE OR REPLACE VIEW ${athena_database_name}.config_inventory_all AS 
SELECT DISTINCT
  a."AccountId"
, a."Region"
, a."Date"
, a."Arn"
, a."TAG1"
, a."TAG2"
, a."TAG3"
, a."TAG4"
, a."AllTags"
, a."LastConfigSnapshot"
, a."ResourceType"
FROM
  (
   SELECT *
   FROM
     (
      SELECT DISTINCT
        "configurationItem"."awsAccountId" "AccountId"
      , "configurationItem"."awsregion" "Region"
      , CAST(date_parse("dt", '%Y-%m-%d') AS "Date") "Date"
      , "configurationItem"."tags"['<TAG1>'] "TAG1"
      , "configurationItem"."tags"['<TAG2>'] "TAG2"
      , "configurationItem"."tags"['<TAG3>'] "TAG3"
      , "configurationItem"."tags"['<TAG4>'] "TAG4"
      , "configurationItem"."tags" "AllTags"
      , "configurationItem"."configurationitemcapturetime" "LastConfigSnapshot"
      , "configurationItem"."resourcetype" "ResourceType"
      , "configurationItem"."arn" "Arn"
      , ROW_NUMBER() OVER (PARTITION BY "configurationItem"."arn", YEAR(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")), MONTH(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")) ORDER BY CAST(date_parse("dt", '%Y-%m-%d') AS "Date") DESC) Rowrank
      FROM
        (cid_crcd_config
      CROSS JOIN UNNEST("configurationitems") t (configurationItem))
   )  sub
   WHERE (Rowrank = 1)
)  a
