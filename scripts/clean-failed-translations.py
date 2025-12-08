import os
import json
import re
import sys

# Default source directory for key count validation
DEFAULT_SOURCE_DIR = "./output/words_map/text"

def contains_chinese(text):
    """Check if text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def is_technical_string(text):
    """Check if string is technical/system data (allowed to have Chinese)."""
    if not isinstance(text, str):
        return False
    if re.search(r'[\u4e00-\u9fff]*表[》\]]', text):
        return True
    if re.search(r'\w+_\w+.*=', text):
        return True
    special_chars = sum(1 for c in text if c in '_=<>[]{}()《》')
    if len(text) > 0 and special_chars / len(text) > 0.15:
        return True
    return False

def read_json(path):
    """Read JSON with multiple encoding fallbacks."""
    for enc in ['utf-8', 'gb18030', 'gbk', 'latin-1']:
        try:
            with open(path, 'r', encoding=enc) as f:
                return json.load(f)
        except:
            continue
    return None

def get_source_key_count(filename, source_dir):
    """Get expected key count from source file."""
    # Extract file ID (e.g., p254950038_01075.json -> 01075)
    match = re.search(r'_(\d+)\.json$', filename)
    if not match:
        return None
    
    file_id = match.group(1)
    source_file = os.path.join(source_dir, f"entry_{file_id}.json")
    
    if not os.path.exists(source_file):
        return None
    
    data = read_json(source_file)
    return len(data) if data else None

def clean_failed_translations(directory, source_dir=None):
    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist.")
        return

    source_dir = source_dir or DEFAULT_SOURCE_DIR
    if not os.path.exists(source_dir):
        print(f"Warning: Source dir '{source_dir}' not found. Skipping key count check.")
        source_dir = None

    files = [f for f in os.listdir(directory) if f.endswith(".json") and not f.startswith("._")]
    print(f"Scanning {len(files)} files in '{directory}'...")

    deleted_count = 0
    for filename in files:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            should_delete = False
            delete_reason = ""
            
            # Try parsing as JSON first
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    # Check for Chinese characters (skip technical strings)
                    for value in data.values():
                        if isinstance(value, str) and contains_chinese(value) and not is_technical_string(value):
                            should_delete = True
                            delete_reason = "contains Chinese"
                            break
                    
                    # Check key count matches source
                    if not should_delete and source_dir:
                        expected_keys = get_source_key_count(filename, source_dir)
                        if expected_keys is not None:
                            actual_keys = len(data)
                            if actual_keys < expected_keys:
                                should_delete = True
                                delete_reason = f"incomplete ({actual_keys}/{expected_keys} keys)"
                                
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, str) and contains_chinese(item):
                            should_delete = True
                            delete_reason = "contains Chinese"
                            break
            except json.JSONDecodeError:
                should_delete = True
                delete_reason = "invalid JSON"

            if should_delete:
                print(f"Deleting {filename} ({delete_reason})")
                os.remove(filepath)
                deleted_count += 1

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"Finished. Deleted {deleted_count} files.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/clean-failed-translations.py <directory>")
        sys.exit(1)
    
    clean_failed_translations(sys.argv[1])
