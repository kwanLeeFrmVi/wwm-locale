#!/usr/bin/env python3
"""Extract missing keys from entries.json that don't exist in dich-xong folder."""
import json
import sys
import os
from pathlib import Path

def main():
    if len(sys.argv) != 4:
        print("Usage: python extract-missing-keys.py <entries.json> <dich-xong-folder> <output-folder>")
        sys.exit(1)
    
    entries_path = sys.argv[1]
    dich_xong_folder = sys.argv[2]
    output_folder = sys.argv[3]
    
    # Load entries.json
    print(f"Loading {entries_path}...")
    with open(entries_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    
    print(f"Total keys in entries.json: {len(entries)}")
    
    # Load all keys from dich-xong
    print(f"Loading existing translations from {dich_xong_folder}...")
    dich_xong_keys = set()
    dich_xong_path = Path(dich_xong_folder)
    
    for json_file in dich_xong_path.glob("*.json"):
        if json_file.name.startswith('._'):
            continue
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dich_xong_keys.update(data.keys())
        except Exception as e:
            print(f"Warning: Failed to load {json_file}: {e}")
    
    print(f"Total keys in dich-xong: {len(dich_xong_keys)}")
    
    # Find missing keys
    entries_keys = set(entries.keys())
    missing_keys = entries_keys - dich_xong_keys
    
    print(f"Missing keys: {len(missing_keys)}")
    
    if not missing_keys:
        print("No missing keys found!")
        return
    
    # Extract missing entries
    missing_entries = {k: entries[k] for k in missing_keys}
    
    # Split into chunks of 265 keys (matching existing file size)
    chunk_size = 265
    chunks = []
    missing_list = sorted(missing_keys)
    
    for i in range(0, len(missing_list), chunk_size):
        chunk_keys = missing_list[i:i + chunk_size]
        chunk_data = {k: missing_entries[k] for k in chunk_keys}
        chunks.append(chunk_data)
    
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    # Write chunks to files
    print(f"\nWriting {len(chunks)} files to {output_folder}...")
    for idx, chunk in enumerate(chunks, start=1):
        output_file = os.path.join(output_folder, f"missing_{idx:05d}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)
        print(f"  Written: missing_{idx:05d}.json ({len(chunk)} keys)")
    
    print(f"\nDone! Extracted {len(missing_keys)} missing keys into {len(chunks)} files.")
    print(f"You can now translate these files using option 4.")

if __name__ == "__main__":
    main()
