#!/usr/bin/env python3
"""
Remove ONLY English lines from JSON files.
A line is English if it contains NO Vietnamese diacritics at all.
"""

import json
import re
from pathlib import Path

def has_vietnamese_diacritics(text):
    """
    Check if text contains ANY Vietnamese diacritics.
    If it has diacritics, it's Vietnamese. If not, it's English.
    """
    if not isinstance(text, str):
        return False

    # Vietnamese diacritics pattern - complete set
    vietnamese_pattern = r'[àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]'
    vietnamese_pattern += r'|[ÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ]'

    return bool(re.search(vietnamese_pattern, text))

def process_json_file(filepath):
    """Remove entries WITHOUT Vietnamese diacritics (English only)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return 0

        original_count = len(data)

        # Keep ONLY entries with Vietnamese diacritics
        cleaned_data = {
            key: value for key, value in data.items()
            if has_vietnamese_diacritics(value)
        }

        removed_count = original_count - len(cleaned_data)

        # Only write if we removed something
        if removed_count > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=2)

        return removed_count

    except Exception as e:
        print(f"❌ Error: {filepath.name}: {e}")
        return 0

def main():
    base_dir = Path("/Volumes/Fanxiang/wwm-locale/dich-xong")

    if not base_dir.exists():
        print(f"❌ Directory not found: {base_dir}")
        return

    # Find only real JSON files
    json_files = [f for f in base_dir.glob("*.json") if not f.name.startswith("._")]
    total_files = len(json_files)

    print(f"🔍 Found {total_files} JSON files")
    print("🚀 Removing lines WITHOUT Vietnamese diacritics...\n")

    total_removed = 0
    files_modified = 0

    for i, filepath in enumerate(json_files, 1):
        removed = process_json_file(filepath)
        if removed > 0:
            total_removed += removed
            files_modified += 1

        if i % 500 == 0:
            print(f"📊 {i}/{total_files} files | {total_removed} English entries removed")

    print(f"\n✅ Complete!")
    print(f"📁 Files checked: {total_files}")
    print(f"📝 Files modified: {files_modified}")
    print(f"🗑️  Entries without diacritics removed: {total_removed}")

if __name__ == "__main__":
    main()
