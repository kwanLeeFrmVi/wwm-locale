import json
import sys

def check_keys(filepath):
    print(f"Checking keys in {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"Loaded {len(data)} entries.")
        
        non_int_keys = []
        for key in data.keys():
            if not key.isdigit():
                non_int_keys.append(key)
                
        if non_int_keys:
            print(f"Found {len(non_int_keys)} non-integer keys!")
            print(f"First 10 non-integer keys: {non_int_keys[:10]}")
        else:
            print("All keys are valid integers.")
            
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    check_keys("./output/words_map/entries.json")
