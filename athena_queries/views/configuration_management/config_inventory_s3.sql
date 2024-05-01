CREATE OR REPLACE VIEW "config_inventory_s3" AS 
SELECT DISTINCT
  a."AccountId"
, a."Region"
, a."Date"
, a."ARN"
, a."BucketName"
, a."TAG1"
, a."TAG2"
, a."TAG3"
, a."TAG4"
, a."AllTags"
, a."LastConfigSnapshot"
, a."CreationDate"
FROM
  (
   SELECT *
   FROM
     (
      SELECT DISTINCT
        "configurationItem"."awsAccountId" "AccountId"
      , "configurationItem"."awsregion" "Region"
      , CAST(date_parse("dt", '%Y-%m-%d') AS "Date") "Date"
      , "configurationItem"."arn" "ARN"
      , "configurationItem"."resourceName" "BucketName"
      , "configurationItem"."tags"['<TAG1>'] "TAG1"
      , "configurationItem"."tags"['<TAG2>'] "TAG2"
      , "configurationItem"."tags"['<TAG3>'] "TAG3"
      , "configurationItem"."tags"['<TAG4>'] "TAG4"
      , "configurationItem"."tags" "AllTags"
      , "configurationItem"."configurationitemcapturetime" "LastConfigSnapshot"
      , "json_extract_scalar"("configurationItem"."configuration", '$.creationDate') "CreationDate"
      , ROW_NUMBER() OVER (PARTITION BY "configurationItem"."resourceName", YEAR(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")), MONTH(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")) ORDER BY CAST(date_parse("dt", '%Y-%m-%d') AS "Date") DESC) Rowrank
      FROM
        (cid_crcd_config
      CROSS JOIN UNNEST("configurationitems") t (configurationItem))
      WHERE ("configurationItem"."resourcetype" = 'AWS::S3::Bucket')
   )  sub
   WHERE (Rowrank = 1)
)  a
