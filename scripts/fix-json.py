#!/usr/bin/env python3
"""Fix JSON syntax errors in translation files."""

import json
import os
import sys
from pathlib import Path

def fix_json_file(filepath):
    """Fix JSON syntax errors in a file."""
    try:
        # Read the file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Handle empty files - delete them
        if not content or content == '{}':
            filepath.unlink()
            print(f"Removed empty file: {filepath.name}")
            return True
        
        # Try to parse as JSON first
        try:
            data = json.loads(content)
            # Re-write with proper formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except json.JSONDecodeError:
            # Fix trailing comma issue
            lines = content.split('\n')
            fixed_lines = []
            
            for i, line in enumerate(lines):
                # Check if this is the last property line (has comma before closing brace)
                if i < len(lines) - 1 and line.strip().endswith(','):
                    next_line = lines[i + 1].strip()
                    if next_line == '}' or next_line == ']':
                        # Remove trailing comma
                        fixed_lines.append(line.rstrip(','))
                        continue
                fixed_lines.append(line)
            
            fixed_content = '\n'.join(fixed_lines)
            
            # Try to parse the fixed content
            data = json.loads(fixed_content)
            
            # Write back with proper formatting
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"Fixed: {filepath.name}")
            return True
            
    except Exception as e:
        print(f"Error fixing {filepath.name}: {e}")
        return False

def main():
    # Get the dich-xong directory
    base_dir = Path(__file__).parent.parent / 'dich-xong'
    
    if not base_dir.exists():
        print(f"Directory not found: {base_dir}")
        sys.exit(1)
    
    # Get all JSON files (skip macOS metadata files)
    json_files = [f for f in base_dir.glob('*.json') if not f.name.startswith('._')]
    
    print(f"Found {len(json_files)} JSON files")
    
    fixed_count = 0
    error_count = 0
    
    for json_file in json_files:
        if fix_json_file(json_file):
            fixed_count += 1
        else:
            error_count += 1
    
    print(f"\nSummary:")
    print(f"  Fixed: {fixed_count}")
    print(f"  Errors: {error_count}")

if __name__ == '__main__':
    main()
