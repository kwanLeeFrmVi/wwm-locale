
import os
import json
import re

import sys

# Default directory if not provided
DEFAULT_TEXT_DIR = "/Volumes/Fanxiang/wwm-locale/dich-xong"

# Regex for common Chinese characters
CHINESE_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fff]')

def contains_chinese(text):
    if isinstance(text, str):
        return bool(CHINESE_CHAR_PATTERN.search(text))
    return False

def verify_files(directory):
    if not os.path.isdir(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return

    files = [f for f in os.listdir(directory) if f.endswith('.json') and not f.startswith('._')]
    files.sort()
    
    total_files = len(files)
    valid_files = 0
    invalid_json_files = []
    files_with_chinese = []
    
    print(f"Verifying {total_files} files in {directory}...")
    
    for filename in files:
        filepath = os.path.join(directory, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            has_chinese = False
            # Check all values in the JSON object
            # Assuming the JSON is a simple key-value map or nested map
            def check_recursive(obj):
                nonlocal has_chinese
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        check_recursive(value)
                elif isinstance(obj, list):
                    for item in obj:
                        check_recursive(item)
                elif isinstance(obj, str):
                    if contains_chinese(obj):
                        has_chinese = True
                        return

            check_recursive(data)
            
            if has_chinese:
                files_with_chinese.append(filename)
                # print(f"FAIL: {filename} contains Chinese characters.")
            else:
                valid_files += 1
                
        except json.JSONDecodeError:
            invalid_json_files.append(filename)
            print(f"ERROR: {filename} is not valid JSON.")
        except Exception as e:
            print(f"ERROR: Could not read {filename}: {e}")

    print("\n" + "="*30)
    print("VERIFICATION SUMMARY")
    print("="*30)
    print(f"Directory: {directory}")
    print(f"Total Files Checked: {total_files}")
    print(f"Fully Translated (Valid): {valid_files}")
    print(f"Invalid JSON: {len(invalid_json_files)}")
    print(f"Files with Chinese: {len(files_with_chinese)}")
    
    if invalid_json_files:
        print("\nFiles with Invalid JSON:")
        for f in invalid_json_files[:20]:
            print(f"  - {f}")
        if len(invalid_json_files) > 20:
            print(f"  ... and {len(invalid_json_files) - 20} more.")

    if files_with_chinese:
        print("\nFiles containing Chinese characters:")
        for f in files_with_chinese[:20]:
            print(f"  - {f}")
        if len(files_with_chinese) > 20:
            print(f"  ... and {len(files_with_chinese) - 20} more.")
            
        with open("invalid_files.txt", "w") as f:
            for filename in files_with_chinese:
                f.write(filename + "\n")
        print(f"\nList of {len(files_with_chinese)} files with Chinese characters saved to 'invalid_files.txt'.")
            
    if valid_files == total_files and total_files > 0:
        print("\nSUCCESS: All files are fully translated and valid.")
    elif total_files == 0:
        print("\nWARNING: No JSON files found in the directory.")
    else:
        print("\nFAILURE: Some files need attention.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = DEFAULT_TEXT_DIR
        
    verify_files(target_dir)
