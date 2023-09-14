 CREATE EXTERNAL TABLE `account_mapping`(
   `account_id` string, 
   `account_name` string, 
   `business_unit` string, 
   `team` string, 
   `cost_center` string
   )
 ROW FORMAT DELIMITED 
   FIELDS TERMINATED BY ',' 
 STORED AS INPUTFORMAT 
   'org.apache.hadoop.mapred.TextInputFormat' 
 OUTPUTFORMAT 
   'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
 LOCATION
   '<S3 Destination>'
 TBLPROPERTIES (
   'has_encrypted_data'='false',
   'skip.header.line.count'='1')