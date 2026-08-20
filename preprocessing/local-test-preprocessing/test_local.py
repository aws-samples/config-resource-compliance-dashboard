"""
Local test script — processes a gzipped Config file from the local filesystem
instead of S3. Writes output files to a local directory for inspection.

Usage:
    python test_local.py <input_file.json.gz> <output_directory>
"""

import gzip
import json
import os
import re
import sys
import uuid
from decimal import Decimal

import ijson


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj == int(obj):
                return int(obj)
            return float(obj)
        return super().default(obj)

BATCH_SIZE = 500

SOURCE_SNAPSHOT_PATTERN = re.compile(
    r'^(?P<account_id>\d+)_Config_(?P<region>[\w-]+)_(?P<type>ConfigSnapshot)_(?P<timestamp>\d{8}T\d{6}Z)_(?P<uuid>[\w-]+)\.json\.gz$'
)
SOURCE_HISTORY_PATTERN = re.compile(
    r'^(?P<account_id>\d+)_Config_(?P<region>[\w-]+)_(?P<type>ConfigHistory)_(?P<resource_type>[^_]+(?:_[^_]+)*)_(?P<timestamp>\d{8}T\d{6}Z)_(?P<end_timestamp>\d{8}T\d{6}Z)_(?P<sequence>\d+)\.json\.gz$'
)


def parse_source_filename(path):
    filename = os.path.basename(path)
    match = SOURCE_SNAPSHOT_PATTERN.match(filename)
    if match:
        return match.groupdict()
    match = SOURCE_HISTORY_PATTERN.match(filename)
    if match:
        return match.groupdict()
    return None


def build_output_filename(account_id, region, config_type, timestamp, sequence_number):
    seq = sequence_number % 100000
    random_part = uuid.uuid4().hex[:12]
    return f"{account_id}_Config_{region}_{config_type}_{timestamp}_{seq:05d}_{random_part}.json.gz"


def process_local_file(input_path, output_dir):
    """Stream a local gzipped Config file and write batched split files to output_dir."""
    os.makedirs(output_dir, exist_ok=True)

    source_meta = parse_source_filename(input_path)
    if not source_meta:
        print(f"ERROR: Input filename does not match expected pattern.")
        print(f"Expected: {{AccountId}}_Config_{{Region}}_ConfigSnapshot_{{Timestamp}}_{{UUID}}.json.gz")
        print(f"Got: {os.path.basename(input_path)}")
        sys.exit(1)

    print(f"Input: {input_path}")
    print(f"Output dir: {output_dir}")
    print(f"Input size: {os.path.getsize(input_path) / (1024*1024):.1f} MB (compressed)")
    print(f"Batch size: {BATCH_SIZE} items per file")
    print(f"Source: account={source_meta['account_id']}, region={source_meta['region']}, "
          f"timestamp={source_meta['timestamp']}")

    file_version = "1.0"
    config_snapshot_id = ""
    item_count = 0
    file_count = 0
    error_count = 0
    batch = []

    with gzip.open(input_path, 'rb') as stream:
        parser = ijson.parse(stream)

        in_items_array = False
        builder = None
        depth = 0

        for prefix, event, value in parser:
            if prefix == 'fileVersion':
                file_version = value
            elif prefix == 'configSnapshotId':
                config_snapshot_id = value
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
                                write_batch(batch, file_count + 1, file_version,
                                            config_snapshot_id, output_dir, source_meta)
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
            write_batch(batch, file_count + 1, file_version,
                        config_snapshot_id, output_dir, source_meta)
            file_count += 1
        except Exception as e:
            error_count += len(batch)
            print(f"Error writing final batch: {e}")

    print(f"\nDone:")
    print(f"  Items processed: {item_count}")
    print(f"  Files written: {file_count}")
    print(f"  Items with errors: {error_count}")
    print(f"  Output dir: {output_dir}")


def write_batch(batch, batch_number, file_version, config_snapshot_id, output_dir, source_meta):
    """
    Write a batch of items as a single gzipped JSON file.

    Output naming convention:
        {accountId}_Config_{region}_{type}_{timestamp}_{sequence}_{random}.json.gz
    """
    output = {
        "fileVersion": file_version,
        "configSnapshotId": config_snapshot_id,
        "configurationItems": batch
    }

    filename = build_output_filename(
        account_id=source_meta['account_id'],
        region=source_meta['region'],
        config_type=source_meta['type'],
        timestamp=source_meta['timestamp'],
        sequence_number=batch_number
    )

    output_path = os.path.join(output_dir, filename)
    json_bytes = json.dumps(output, cls=DecimalEncoder).encode('utf-8')

    with gzip.open(output_path, 'wb') as out_file:
        out_file.write(json_bytes)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python test_local.py <input_file.json.gz> <output_directory>")
        sys.exit(1)

    process_local_file(sys.argv[1], sys.argv[2])
