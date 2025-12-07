#!/usr/bin/env python3
"""Convert all JSON files in a directory from GB18030 to UTF-8."""

import json
import os
import sys

def convert_to_utf8(directory):
    encodings = ['utf-8', 'gb18030', 'gbk', 'latin-1']
    converted = 0
    
    for filename in os.listdir(directory):
        if not filename.endswith('.json') or filename.startswith('.'):
            continue
        
        filepath = os.path.join(directory, filename)
        
        # Try to read with different encodings
        data = None
        used_encoding = None
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    data = json.load(f)
                used_encoding = enc
                break
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        
        if data is None:
            print(f"Failed to read: {filename}")
            continue
        
        # Write back as UTF-8
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        if used_encoding != 'utf-8':
            print(f"Converted: {filename} ({used_encoding} -> utf-8)")
            converted += 1
    
    print(f"\nConverted {converted} files to UTF-8")

if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else './dich-xong'
    convert_to_utf8(directory)
