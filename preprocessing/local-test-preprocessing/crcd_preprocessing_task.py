"""
AWS Config Snapshot/History file splitter.

Streams a large gzipped AWS Config JSON file from S3, parses it incrementally
(one configurationItem at a time), and writes each item as a separate gzipped
JSON file to a destination S3 bucket. Memory usage stays constant regardless
of input file size.

Designed to run on AWS Fargate (no time limit, modest memory requirements).
"""

import gzip
import io
import json
import os
import re
import urllib.parse
import uuid
from datetime import datetime
from decimal import Decimal

import boto3
import ijson


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj == int(obj):
                return int(obj)
            return float(obj)
        return super().default(obj)

# Matches AWS Config source filenames:
# ConfigSnapshot: {AccountId}_Config_{Region}_ConfigSnapshot_{Timestamp}_{UUID}.json.gz
# ConfigHistory:  {AccountId}_Config_{Region}_ConfigHistory_{ResourceType}_{StartTime}_{EndTime}_{Sequence}.json.gz
SOURCE_SNAPSHOT_PATTERN = re.compile(
    r'^(?P<account_id>\d+)_Config_(?P<region>[\w-]+)_(?P<type>ConfigSnapshot)_(?P<timestamp>\d{8}T\d{6}Z)_(?P<uuid>[\w-]+)\.json\.gz$'
)
SOURCE_HISTORY_PATTERN = re.compile(
    r'^(?P<account_id>\d+)_Config_(?P<region>[\w-]+)_(?P<type>ConfigHistory)_(?P<resource_type>[^_]+(?:_[^_]+)*)_(?P<timestamp>\d{8}T\d{6}Z)_(?P<end_timestamp>\d{8}T\d{6}Z)_(?P<sequence>\d+)\.json\.gz$'
)


def parse_source_filename(source_key):
    """
    Extract account_id, region, type, and timestamp from the source filename.
    Handles both ConfigSnapshot and ConfigHistory naming conventions.
    Returns a dict with the parsed components, or None if the filename doesn't match.
    """
    filename = os.path.basename(source_key)
    match = SOURCE_SNAPSHOT_PATTERN.match(filename)
    if match:
        return match.groupdict()
    match = SOURCE_HISTORY_PATTERN.match(filename)
    if match:
        return match.groupdict()
    return None


def decode_s3_key(s3_path):
    if not s3_path.startswith('s3://'):
        return s3_path

    parts = s3_path[5:].split('/', 1)
    if len(parts) < 2:
        return s3_path

    bucket = parts[0]
    key = urllib.parse.unquote(parts[1])
    return f"s3://{bucket}/{key}"


def get_relative_path(source_path):
    decoded_path = decode_s3_key(source_path)
    parts = decoded_path.replace('s3://', '').split('/', 1)
    if len(parts) > 1:
        return parts[1]
    return ''


def get_destination_key(source_path, filename):
    """Generate destination key maintaining the source directory structure."""
    relative_path = get_relative_path(source_path)
    dir_path = os.path.dirname(relative_path)
    if dir_path:
        return f"{dir_path}/{filename}"
    return filename


def compress_json(data):
    """Compress a dict to gzipped JSON bytes."""
    json_bytes = json.dumps(data, cls=DecimalEncoder).encode('utf-8')
    buffer = io.BytesIO()
    with gzip.GzipFile(mode='wb', fileobj=buffer) as gz:
        gz.write(json_bytes)
    buffer.seek(0)
    return buffer.getvalue()


def build_output_filename(account_id, region, config_type, timestamp, sequence_number):
    """
    Build output filename following the convention:
        {accountId}_Config_{region}_{type}_{timestamp}_{sequence}_{random}.json.gz

    sequence_number wraps at 99999 back to 00000.
    """
    seq = sequence_number % 100000
    random_part = uuid.uuid4().hex[:12]
    return f"{account_id}_Config_{region}_{config_type}_{timestamp}_{seq:05d}_{random_part}.json.gz"


BATCH_SIZE = 500


class StreamingConfigSplitter:
    """
    Streams a gzipped AWS Config file from S3 and writes batches of
    configurationItems as separate gzipped JSON files.
    """

    def __init__(self, source_bucket, source_key, dest_bucket, dest_prefix="",
                 tracking_table_name=None, job_run_id=None):
        self.source_bucket = source_bucket
        self.source_key = source_key
        self.dest_bucket = dest_bucket
        self.dest_prefix = dest_prefix.rstrip('/')
        self.tracking_table_name = tracking_table_name
        self.job_run_id = job_run_id

        self.s3 = boto3.client('s3')
        self.dynamodb_table = None
        if tracking_table_name:
            self.dynamodb_table = boto3.resource('dynamodb').Table(tracking_table_name)

        self.file_version = "1.0"
        self.config_snapshot_id = ""

        self.source_meta = parse_source_filename(source_key)
        if not self.source_meta:
            raise ValueError(
                f"Source key does not match expected AWS Config filename pattern: "
                f"{os.path.basename(source_key)}"
            )

    def process(self):
        """Main entry point. Streams the source file and writes batched output."""
        source_path = f"s3://{self.source_bucket}/{self.source_key}"
        print(f"Processing: {source_path}")
        print(f"Destination: s3://{self.dest_bucket}/{self.dest_prefix}/")
        print(f"Batch size: {BATCH_SIZE} items per file")

        item_count = 0
        file_count = 0
        error_count = 0
        batch = []

        try:
            stream = self._open_stream()

            parser = ijson.parse(stream)

            in_items_array = False
            builder = None
            depth = 0

            for prefix, event, value in parser:
                if prefix == 'fileVersion':
                    self.file_version = value
                elif prefix == 'configSnapshotId':
                    self.config_snapshot_id = value
                elif prefix == 'configurationItems' and event == 'start_array':
                    in_items_array = True
                    continue
                elif prefix == 'configurationItems' and event == 'end_array':
                    in_items_array = False
                    continue

                if in_items_array:
                    if event == 'start_map' and prefix == 'configurationItems.item':
                        builder = ijson.ObjectBuilder()
                        builder.event(event, value)
                        depth = 1
                    elif builder is not None:
                        builder.event(event, value)
                        if event in ('start_map', 'start_array'):
                            depth += 1
                        elif event in ('end_map', 'end_array'):
                            depth -= 1

                        if depth == 0:
                            item = builder.value
                            builder = None
                            batch.append(item)
                            item_count += 1

                            if len(batch) >= BATCH_SIZE:
                                try:
                                    self._write_batch(batch, file_count + 1)
                                    file_count += 1
                                except Exception as e:
                                    error_count += len(batch)
                                    print(f"Error writing batch {file_count + 1}: {e}")
                                batch = []

                            if item_count % 5000 == 0:
                                print(f"Progress: {item_count} items read, {file_count} files written")

            # Write remaining items
            if batch:
                try:
                    self._write_batch(batch, file_count + 1)
                    file_count += 1
                except Exception as e:
                    error_count += len(batch)
                    print(f"Error writing final batch: {e}")

            print(f"\nProcessing complete:")
            print(f"  Items processed: {item_count}")
            print(f"  Files written: {file_count}")
            print(f"  Items with errors: {error_count}")

            self._update_tracking('COMPLETED', item_count)

        except Exception as e:
            print(f"Fatal error: {e}")
            self._update_tracking('FAILED', item_count, str(e))
            raise

        return item_count

    def _open_stream(self):
        """Open a streaming, decompressing reader from S3."""
        response = self.s3.get_object(Bucket=self.source_bucket, Key=self.source_key)
        raw_stream = response['Body']

        if self.source_key.endswith('.gz'):
            return gzip.GzipFile(fileobj=raw_stream)
        return raw_stream

    def _write_batch(self, batch, batch_number):
        """
        Write a batch of configurationItems as a single gzipped JSON file to S3.

        Output naming convention:
            {accountId}_Config_{region}_{type}_{timestamp}_{sequence}_{random}.json.gz

        Account ID, region, type, and timestamp are preserved from the source filename
        to allow correlation between input and output files.
        """
        output = {
            "fileVersion": self.file_version,
            "configSnapshotId": self.config_snapshot_id,
            "configurationItems": batch
        }

        filename = build_output_filename(
            account_id=self.source_meta['account_id'],
            region=self.source_meta['region'],
            config_type=self.source_meta['type'],
            timestamp=self.source_meta['timestamp'],
            sequence_number=batch_number
        )

        source_path = f"s3://{self.source_bucket}/{self.source_key}"
        dest_key = get_destination_key(source_path, filename)
        if self.dest_prefix:
            dest_key = f"{self.dest_prefix}/{dest_key}" if dest_key else self.dest_prefix

        compressed = compress_json(output)

        self.s3.put_object(
            Bucket=self.dest_bucket,
            Key=dest_key,
            Body=compressed,
            ContentType='application/json',
            ContentEncoding='gzip'
        )

    def _update_tracking(self, status, processed_count, error_message=None):
        """Update the DynamoDB tracking table."""
        if not self.dynamodb_table or not self.job_run_id:
            return

        try:
            update_expr = "SET #status = :status, end_time = :end_time, processed_items = :count"
            expr_values = {
                ':status': status,
                ':end_time': datetime.now().isoformat(),
                ':count': processed_count
            }

            if error_message:
                update_expr += ", error_message = :error_message"
                expr_values[':error_message'] = error_message

            self.dynamodb_table.update_item(
                Key={
                    'source_file': self.source_key,
                    'job_run_id': self.job_run_id
                },
                UpdateExpression=update_expr,
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues=expr_values
            )
        except Exception as e:
            print(f"Warning: failed to update tracking table: {e}")


def main():
    """Entry point for Fargate task. Reads configuration from environment variables."""
    source_path = os.environ['SOURCE_PATH']
    dest_bucket = os.environ['DESTINATION_BUCKET']
    dest_prefix = os.environ.get('DESTINATION_PREFIX', '')
    tracking_table = os.environ.get('TRACKING_TABLE_NAME')
    job_run_id = os.environ.get('JOB_RUN_ID')

    decoded_path = decode_s3_key(source_path)
    parts = decoded_path.replace('s3://', '').split('/', 1)
    source_bucket = parts[0]
    source_key = parts[1] if len(parts) > 1 else ''

    splitter = StreamingConfigSplitter(
        source_bucket=source_bucket,
        source_key=source_key,
        dest_bucket=dest_bucket,
        dest_prefix=dest_prefix,
        tracking_table_name=tracking_table,
        job_run_id=job_run_id
    )

    splitter.process()


if __name__ == '__main__':
    main()
