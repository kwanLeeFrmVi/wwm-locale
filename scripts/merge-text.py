##
# Copyright (c) 2025 und3fy.dev. All rights reserved.
# Created by und3fined <me@und3fy.dev> on 2025 Nov 26.
##

import json
import math
import os
import sys


def read_json_file(filepath):
    """Read JSON with multiple encoding fallbacks."""
    encodings = ['utf-8', 'gb18030', 'gbk', 'latin-1']
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return json.load(f)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    # Last resort: read as binary and decode with errors='replace'
    with open(filepath, 'rb') as f:
        content = f.read().decode('utf-8', errors='replace')
    return json.loads(content)


def merge_text_files(base_dir, patch_dir, save_missing=False):
    merged_data = {}

    text_dir = os.path.join(base_dir, "text")
    output_file = os.path.join(base_dir, "entries.json")

    # merge original data first
    for filename in os.listdir(text_dir):
        if filename.endswith(".json") and not filename.startswith("."):
            orig_filepath = os.path.join(text_dir, filename)
            data = read_json_file(orig_filepath)
            
            merged_data.update(data)

    # track all keys from base for missing detection
    base_keys = set(merged_data.keys())
    patched_keys = set()

    # apply patches
    for filename in os.listdir(patch_dir):
        if filename.endswith(".json") and not filename.startswith(".") and filename != "missing.json":
            try:
                patch_filepath = os.path.join(patch_dir, filename)
                patch_data = read_json_file(patch_filepath)
                
                # check if key exists in merged_data then update, else skip
                for key, value in patch_data.items():
                    patched_keys.add(key)
                    if key in merged_data:
                        if isinstance(value, str):
                            merged_data[key] = value
                        elif isinstance(value, list) and len(value) > 0:
                            merged_data[key] = value[-1]
                        elif isinstance(value, dict) and len(value) > 0:
                            last_key = list(value.keys())[-1]
                            merged_data[key] = value[last_key]
                
                del patch_data  # reset for next iteration

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from `{filename}`: {e}")

    # save original output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)

    # sync merged values back into per-file text shards so packer picks them up
    for filename in os.listdir(text_dir):
        if filename.endswith(".json") and not filename.startswith("."):
            shard_path = os.path.join(text_dir, filename)
            shard_data = read_json_file(shard_path)

            updated = False
            for key in list(shard_data.keys()):
                if key in merged_data and shard_data[key] != merged_data[key]:
                    shard_data[key] = merged_data[key]
                    updated = True

            if updated:
                with open(shard_path, "w", encoding="utf-8") as f:
                    json.dump(shard_data, f, ensure_ascii=False, indent=2)

    # save missing keys if --miss flag is set
    if save_missing:
        missing_dir = os.path.join(base_dir, "missing")
        os.makedirs(missing_dir, exist_ok=True)

        missing_keys = base_keys - patched_keys
        missing_data = {key: merged_data[key] for key in missing_keys}

        entries_per_file = 265
        # use ceil to handle remainder
        missing_count = math.ceil(len(missing_data) / entries_per_file)

        # convert to list for easier pagination
        missing_items = list(missing_data.items())

        # create paginated files
        for page in range(missing_count):
            start_idx = page * entries_per_file
            end_idx = start_idx + entries_per_file
            page_data = dict(missing_items[start_idx:end_idx])

            missing_file = os.path.join(missing_dir, f"missing_{page + 1:05d}.json")
            with open(missing_file, "w", encoding="utf-8") as f:
                json.dump(page_data, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(missing_data)} missing entries to {missing_count} files.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python merge-text.py <base_dir> <patch_dir> [--miss]")
        sys.exit(1)

    base_dir = sys.argv[1]
    patch_dir = sys.argv[2]
    save_missing = "--miss" in sys.argv

    merge_text_files(base_dir, patch_dir, save_missing)
    print(f"Merged text files {patch_dir} into {base_dir}/entries.json")
