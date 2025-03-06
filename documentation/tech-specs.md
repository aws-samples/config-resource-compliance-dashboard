



## Lambda Partitioner



### Partitioning AWS Config files
The Lambda Partitioning function has environment variables that activate the partitioning of AWS Config configuration history and configuration snapshot files separately. The parameters are called:
* `PARTITION_CONFIG_SNAPSHOT_RECORDS`
* `PARTITION_CONFIG_HISTORY_RECORDS`

Pass `1` as value to enable, or `0` to disable the partitioning of the corresponding AWS Config file. By default, in accordance with our prerequisite to leverage AWS Config configuration snapshot files, AWS Config configuration history records are disabled.


### CloudWatch Log Group Retention
* Default: 14 days
* Change in Cloud Formation template, `LambdaFunctionPartitionerConfigLogGroup/Properties/RetentionInDays` before deployment