import json
import re
import sys

# Default filenames
input_file = 'raw_grep_output.txt'
output_file = 'han_viet_kho_hieu.json'

# Check for command line arguments
if len(sys.argv) > 1:
    input_file = sys.argv[1]
if len(sys.argv) > 2:
    output_file = sys.argv[2]

data = {}

# Regex to capture "id": "text"
# Allowing for potential whitespace variations
pattern = re.compile(r'"(\d+)":\s*"(.*)"')

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            # We only care about the content part, usually after the filename
            # But the filename might contain colons too, so we look for the JSON key-value pattern
            match = pattern.search(line)
            if match:
                key = match.group(1)
                value = match.group(2)
                # Unescape escaped quotes if necessary (simple approach)
                # The text from grep might be literally what's in the file
                data[key] = value

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Successfully processed {len(data)} items from '{input_file}' into '{output_file}'")

except Exception as e:
    print(f"Error: {e}")
