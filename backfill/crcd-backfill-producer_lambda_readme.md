# AWS Config Resource Compliance Dashboard - Backfill Producer Lambda

## Parallelization Solution

The original Lambda function (`crcd-backfill-producer_lambda.py`) was timing out when processing large S3 buckets. This document explains the parallelization solution implemented in `crcd-backfill-producer_parallel.py`.

## How the Parallel Solution Works

The new solution uses a divide-and-conquer approach:

1. **Initial Invocation**: The Lambda first discovers common prefixes in the S3 bucket up to a configurable depth
2. **Work Distribution**: It then splits these prefixes into manageable chunks and invokes copies of itself to process each chunk
3. **Parallel Processing**: Each worker Lambda processes its assigned prefixes using multiple threads
4. **Result Aggregation**: Each worker sends its results directly to the SQS queue

## Key Improvements

1. **Hierarchical Processing**: Instead of scanning the entire bucket at once, the Lambda breaks down the work by prefix
2. **Multi-threading**: Each worker uses thread pools to process multiple prefixes concurrently
3. **Self-invocation**: The Lambda can invoke copies of itself to distribute work
4. **Configurable Parameters**: Processing depth, worker count, and chunk size can be adjusted via environment variables

## Configuration Parameters

Add these environment variables to your Lambda configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| MAX_WORKERS | Number of threads per Lambda worker | 10 |
| MAX_PREFIX_DEPTH | Depth of prefix hierarchy to use for partitioning | 4 |
| PROCESS_CHUNK_SIZE | Number of prefixes to process per worker invocation | 10 |

## Implementation Notes

1. **Lambda Timeout**: Increase the Lambda timeout to at least 5 minutes to allow for prefix discovery
2. **Lambda Memory**: Increase memory allocation to at least 1024MB for better performance
3. **IAM Permissions**: The Lambda needs permission to invoke itself:
   ```json
   {
     "Effect": "Allow",
     "Action": "lambda:InvokeFunction",
     "Resource": "arn:aws:lambda:*:*:function:YOUR_FUNCTION_NAME"
   }
   ```

## Deployment Instructions

1. Deploy the new Lambda function or update the existing one with the new code
2. Add the required environment variables
3. Update the IAM role to allow Lambda self-invocation
4. Increase the Lambda timeout and memory allocation

## Monitoring

Monitor the Lambda execution using CloudWatch Logs. Each worker reports its progress and results.

## Troubleshooting

- If workers are timing out, decrease `PROCESS_CHUNK_SIZE` or increase Lambda timeout
- If processing is too slow, increase `MAX_WORKERS` and Lambda memory
- If you're hitting Lambda concurrency limits, add a concurrency reservation for this function