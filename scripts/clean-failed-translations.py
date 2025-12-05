import os
import json
import re
import sys

def contains_chinese(text):
    """Check if text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def clean_failed_translations(directory):
    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist.")
        return

    files = [f for f in os.listdir(directory) if f.endswith(".json")]
    print(f"Scanning {len(files)} files in '{directory}'...")

    deleted_count = 0
    for filename in files:
        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            should_delete = False
            
            # Try parsing as JSON first
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    for value in data.values():
                        if isinstance(value, str) and contains_chinese(value):
                            should_delete = True
                            break
                elif isinstance(data, list):
                     for item in data:
                        if isinstance(item, str) and contains_chinese(item):
                            should_delete = True
                            break
            except json.JSONDecodeError:
                # If invalid JSON, it's a failed translation/write
                print(f"File {filename} is invalid JSON (incomplete or malformed).")
                should_delete = True

            if should_delete:
                if contains_chinese(content):
                    print(f"Deleting {filename} (contains Chinese)")
                else:
                    print(f"Deleting {filename} (invalid JSON)")
                
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
