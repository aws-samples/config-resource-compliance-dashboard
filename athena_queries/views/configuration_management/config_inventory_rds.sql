-- WIP config_inventory_rds
--CREATE OR REPLACE VIEW "config_inventory_rds" AS 
SELECT DISTINCT
  a."AccountId"
, a."Region"
, a."AvailabilityZone"
, a."Date"
, a."Arn"
, a."TAG1"
, a."TAG2"
, a."TAG3"
, a."TAG4"
, a."AllTags"
, a."DatabaseName"
, a."Engine"
, a."EngineVersion"
, a."InstanceCreateTime"
, a."KmsKeyId"
, a."LatestRestorableTime"
, a."Username"
, a."IsMultiAZ"
, a."IsPubliclyAccessible"
, a."IsStorageEncrypted"
, a."StorageType"
, a."TimeZone"
, a."ResourceCreateTime"
, a."ResourceId"
, a."ResourceName"
FROM
  (
    SELECT *
    FROM
    (
        SELECT
            "configurationItem"."awsAccountId" "AccountId"
            , "configurationItem"."awsregion" "Region"
            , "configurationItem"."availabilityZone" "AvailabilityZone"
            , CAST(date_parse("dt", '%Y-%m-%d') AS "Date") "Date"
            , "configurationItem"."arn" "Arn"
            , "configurationItem"."tags"['TAG1'] "TAG1"
            , "configurationItem"."tags"['TAG2'] "TAG2"
            , "configurationItem"."tags"['TAG3'] "TAG3"
            , "configurationItem"."tags"['TAG4'] "TAG4"
            , "configurationItem"."tags" "AllTags"
            , "json_extract_scalar"("configurationItem"."configuration", '$.dBName') "DatabaseName"
            , "json_extract_scalar"("configurationItem"."configuration", '$.engine') "Engine"
            , "json_extract_scalar"("configurationItem"."configuration", '$.engineVersion') "EngineVersion"
            , "json_extract_scalar"("configurationItem"."configuration", '$.instanceCreateTime') "InstanceCreateTime"
            , "json_extract_scalar"("configurationItem"."configuration", '$.kmsKeyId') "KmsKeyId"
            , "json_extract_scalar"("configurationItem"."configuration", '$.latestRestorableTime') "LatestRestorableTime"
            , "json_extract_scalar"("configurationItem"."configuration", '$.masterUsername') "Username"
            , "json_extract_scalar"("configurationItem"."configuration", '$.multiAZ') "IsMultiAZ"
            , "json_extract_scalar"("configurationItem"."configuration", '$.publiclyAccessible') "IsPubliclyAccessible"
            , "json_extract_scalar"("configurationItem"."configuration", '$.storageEncrypted') "IsStorageEncrypted"
            , "json_extract_scalar"("configurationItem"."configuration", '$.storageType') "StorageType"
            , "json_extract_scalar"("configurationItem"."configuration", '$.timezone') "TimeZone"
            , "configurationItem"."resourceCreationTime" "ResourceCreateTime"
            , "configurationItem"."resourceId" "ResourceId"
            , "configurationItem"."resourceName" "ResourceName"
            , ROW_NUMBER() OVER (PARTITION BY "configurationItem"."arn", YEAR(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")), MONTH(CAST(date_parse("dt", '%Y-%m-%d') AS "Date")) ORDER BY CAST(date_parse("dt", '%Y-%m-%d') AS "Date") DESC) Rowrank
        FROM
            (cid_crcd_config
                CROSS JOIN UNNEST("configurationitems") t (configurationItem))
        WHERE ("configurationItem"."resourcetype" like 'AWS::RDS::DBInstance')
    ) sub
    WHERE (Rowrank = 1)
)  a