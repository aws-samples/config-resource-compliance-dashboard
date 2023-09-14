output "athena_workgroup_arn" {
    description = "ARN of the Athena Work Group"
    value = aws_athena_workgroup.athena_workgroup.arn
}