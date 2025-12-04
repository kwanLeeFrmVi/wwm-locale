# Description: Script to translate text from file using OpenRouter/Gemini with streaming
# Enhanced version for local usage

import os
import re
import sys
import concurrent.futures
from datetime import datetime

import time
from halo import Halo
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

system_description = """Bạn là dịch thuật truyện kiếm hiệp Trung Quốc cho trò chơi Where Winds Meets.
Sử dụng từ Hán Việt thông dụng khi chuyển từng câu từ tiếng Trung sang tiếng Việt, giữ nguyên tên riêng/chiêu thức/binh khí theo phong cách kiếm hiệp.
Dịch sát nghĩa, không lược bỏ chi tiết, bảo tồn sắc thái kiếm hiệp và cảm xúc nhân vật.
Phản hồi duy nhất bằng JSON hợp lệ, không kèm theo giải thích hoặc đánh dấu ```.
"""

# Read OS env for api key and base url
auth_api_key = os.getenv("OR_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
openai_model = os.getenv("OPENAI_MODEL", "google/gemini-pro-1.5-flash-001")

if not auth_api_key:
    print("Error: OR_API_KEY not found in environment variables.")
    print("Please check your .env file.")
    sys.exit(1)

def replace_filename_pattern(filename, out_prefix):
    pattern = r"^(.+?)_(\d+)\.json$"
    match = re.match(pattern, filename)

    if match:
        number = match.group(2)
        return f"p{out_prefix}_{number}.json"

    return filename


def translate_text(spinner, input_file, output_file):
    # current started time
    started_at = os.times()

    # Path to output file (assuming same directory as input, with 'translated_' prefix)
    output_file = output_file or os.path.join(
        os.path.dirname(input_file), "translated_" + os.path.basename(input_file)
    )

    # Check if input file exists
    if not os.path.exists(input_file):
        spinner.fail(f"Input file {input_file} does not exist.")
        return -1

    # Read content from input file
    with open(input_file, "r", encoding="utf-8") as f:
        content_to_translate = f.read().strip()

    if not content_to_translate:
        spinner.warn(f"Input file {input_file} is empty.")
        return 0

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Initialize OpenAI client
    client = OpenAI(
        base_url=openai_base_url,
        api_key=auth_api_key,
    )

    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            # Create chat completion with streaming
            completion = client.chat.completions.create(
                extra_headers={
                    "X-Title": "WWM Locale Tool",  # Optional. Site title for rankings on openrouter.ai.
                },
                model=openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_description,
                    },
                    {"role": "user", "content": content_to_translate},
                ],
                stream=True,  # Enable streaming
            )
            break # Success, exit retry loop
        except Exception as e:
            if attempt < max_retries - 1:
                spinner.warn(f"Network error: {e}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2 # Exponential backoff
            else:
                spinner.fail(f"Network error: {e}")
                return -1

    translated_text = ""
    try:
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content:
                resp_content = chunk.choices[0].delta.content

                translated_text += resp_content
                # Update spinner with latest content
                if hasattr(spinner, 'update_text'):
                    spinner.update_text(translated_text)
                elif hasattr(spinner, 'text'):
                     spinner.text = " > {}...".format(
                        resp_content.replace("\n", "").strip()[:35]
                    )
    except Exception as e:
        spinner.fail(f"Streaming error: {e}")
        return -1

    processed_at = os.times()

    # Write the full translated text to output file
    with open(output_file, "w", encoding="utf-8") as f:
        # remove leading and trailing ```
        translated_text = translated_text.strip()
        i1 = translated_text.find("{")
        i2 = translated_text.rfind("}")
        if i1 != -1 and i2 != -1:
            translated_text = translated_text[i1 : i2 + 1]

        f.write(translated_text)

    return processed_at[4] - started_at[4]


def process_file(idx, filename, input_file, output_file, total_files):
    # Create a new spinner for each thread (or just print since spinner isn't thread-safe)
    # Using print for thread safety
    print(f"[{idx + 1}/{total_files}] Translating {filename}...")
    
    # We need to pass a dummy spinner or modify translate_text to not use spinner
    # For simplicity, we'll create a dummy object with .text, .fail, .warn methods
    class DummySpinner:
        def __init__(self): self.text = ""
        def fail(self, msg): print(f"\r✖ {msg}")
        def warn(self, msg): print(f"\r⚠ {msg}")
        def info(self, msg): print(f"\rℹ {msg}")
        def succeed(self, msg): print(f"\r✔ {msg}")
        def update_text(self, text):
            # Print streaming update on the same line
            # Truncate to avoid messing up terminal
            preview = text.replace("\n", " ").strip()[-40:]
            print(f"\r⠙ {filename}: ...{preview}", end="", flush=True)
    
    spinner = DummySpinner()
    processed_time = translate_text(spinner, input_file, output_file)
    
    if processed_time != -1:
        # Read the first few characters of the translated file for preview
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Try to parse JSON to get values
                import json
                try:
                    data = json.loads(content)
                    # Assuming the structure is key-value, get the first value or the whole dict
                    if isinstance(data, dict):
                        # Get the first string value found
                        values = [str(v) for v in data.values() if isinstance(v, str)]
                        if values:
                            preview = values[0]
                        else:
                            preview = str(data)
                    else:
                        preview = str(data)
                except:
                    preview = content.replace("\n", " ").strip()
                
                preview = preview[:60] + "..." if len(preview) > 60 else preview
        except:
            preview = "..."
            
        print(f"✔ [{idx + 1}/{total_files}] {filename} -> {preview} ({processed_time:.2f}s)")
    else:
        print(f"⚠ [{idx + 1}/{total_files}] Translation failed for {filename}.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python trans-local.py <source folder> <output folder>")
        sys.exit(1)

    missing_folder = sys.argv[1]
    output_folder = sys.argv[2]

    # Collect the streamed response
    spinner = Halo(text="Processing", spinner="dots")
    spinner.start()

    if not os.path.exists(missing_folder):
        spinner.fail(f"Source folder '{missing_folder}' does not exist.")
        sys.exit(1)

    # list files in missing folder
    files = sorted(os.listdir(missing_folder))
    
    # Filter only json files and ignore hidden/metadata files
    json_files = [f for f in files if f.endswith(".json") and not f.startswith("._")]
    
    if not json_files:
        spinner.warn(f"No JSON files found in '{missing_folder}'.")
        sys.exit(0)

    now = datetime.now()
    run_at = (
        f"{now.strftime('%y')}"  # Year in 2 digits
        f"{now.strftime('%V')}"  # Week of year (ISO)
        f"{now.strftime('%u')}"  # Day of week (1-7)
        f"{now.strftime('%H')}"  # Hour 24h
        f"{now.strftime('%M')}"  # Minute
    )



    # Process files in parallel
    worker_count = int(os.getenv("WORKER_COUNT", "5"))
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = []
        for idx, filename in enumerate(json_files):
            new_filename = replace_filename_pattern(filename, run_at)
            input_file = os.path.join(missing_folder, filename)

            if new_filename == filename:
                output_file = os.path.join(output_folder, f"t{run_at}_{filename}")
            else:
                output_file = os.path.join(output_folder, new_filename)

            # Check if output file already exists (Resume capability)
            # The original script generates filenames like p{run_at}_{number}.json
            # We need to check if ANY file with the same ID exists in the output folder to avoid re-translating.
            
            # Extract ID from filename (e.g., entry_00123.json -> 00123)
            match = re.match(r"^.+?_(\d+)\.json$", filename)
            if match:
                file_id = match.group(1)
                # Look for any file ending with _{file_id}.json in output_folder
                # This covers both p{run_at}_{id}.json and t{run_at}_{filename}
                existing_files = [f for f in os.listdir(output_folder) if f.endswith(f"_{file_id}.json")]
                if existing_files:
                     spinner.info(f"[{idx + 1}/{len(json_files)}] Skipping {filename} (already translated as {existing_files[0]})")
                     continue
            
            # Fallback check for exact filename match if pattern doesn't match
            # For non-numbered files, the output is t{run_at}_{filename}
            # We should check if ANY file ending with _{filename} exists
            else:
                existing_files = [f for f in os.listdir(output_folder) if f.endswith(f"_{filename}")]
                if existing_files:
                    spinner.info(f"[{idx + 1}/{len(json_files)}] Skipping {filename} (already translated as {existing_files[0]})")
                    continue

            futures.append(executor.submit(process_file, idx, filename, input_file, output_file, len(json_files)))

        # Wait for all futures to complete
        for future in concurrent.futures.as_completed(futures):
            pass

    spinner.succeed("All tasks completed.")


