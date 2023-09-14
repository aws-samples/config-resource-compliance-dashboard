variable "athena_workgroup_name" {
    type = string
    description = "Name of the Athena WorkGroup"
}

variable "athena_database_name" {
    type = string
    description = "Name of the Athena database"
}

variable "athena_query_results_bucket_name" {
    type = string
    description = "Name of bucket used to store the Athena Query results"
}