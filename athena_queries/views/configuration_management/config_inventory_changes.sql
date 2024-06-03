CREATE OR REPLACE VIEW "config_inventory_changes" AS 
SELECT DISTINCT
  a."AccountId"
, a."Region"
, a."Date"
, a."Arn"
, a."Rowrank"
, a."TAG1"
, a."TAG2"
, a."TAG3"
, a."TAG4"
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
      , "configurationItem"."tags"['CostCenter'] "TAG1"
      , "configurationItem"."tags"['Application'] "TAG2"
      , "configurationItem"."tags"['Environment'] "TAG3"
      , "configurationItem"."tags"['Owner'] "TAG4"
      , "configurationItem"."tags" "AllTags"
      , "configurationItem"."configurationitemcapturetime" "LastConfigSnapshot"
      , "configurationItem"."resourcetype" "ResourceType"
      , "configurationItem"."arn" "Arn"
      , ROW_NUMBER() OVER (PARTITION BY "configurationItem"."arn", YEAR(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")), MONTH(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")) ORDER BY CAST(date_parse("dt", '%Y-%m-%d') AS "Date") DESC) Rowrank
      FROM
        (cid_crcd_config
      CROSS JOIN UNNEST("configurationitems") t (configurationItem))
   )  sub
   -- WHERE (Rowrank = 1)
)  a
