CREATE OR REPLACE VIEW ${athena_database_name}.config_rule_evaluation_costs AS
SELECT DISTINCT
a."AccountId"
, a."Region"
, a."Date"
, a."RuleName"
, a."Evaluations"
, a."Cost"
FROM
(
    WITH
    dataset AS (
    SELECT
        "recipientaccountid" "AccountId"
    , "awsregion" "Region"
    , CAST(date_parse("dt", '%Y-%m-%d') AS "Date") "Date"
    , "json_extract_scalar"("additionaleventdata", '$.configRuleName') "RuleName"
    , CAST("json_extract"("requestparameters", '$.evaluations') AS array(map(varchar, varchar))) "EvaluationsArray"
    FROM
        aws_cloudtrail_events
    WHERE ((eventsource = 'config.amazonaws.com') AND (eventname = 'PutEvaluations'))
    )
,    expanded_dataset AS (
    SELECT
        "RuleName"
    , "Region"
    , "AccountId"
    , "Date"
    , e['complianceType'] compliance_type
    FROM
        dataset
    , UNNEST("EvaluationsArray") t (e)
    WHERE (e['complianceType'] <> 'NOT_APPLICABLE')
    )
    SELECT
    "RuleName"
    , "Region"
    , "AccountId"
    , "Date"
    , "count"(compliance_type) "Evaluations"
    , ("count"(compliance_type) * 1E-3) "Cost"
    FROM
    expanded_dataset
    GROUP BY "RuleName", "Region", "AccountId", "Date"
    ORDER BY "Evaluations" DESC
)  a