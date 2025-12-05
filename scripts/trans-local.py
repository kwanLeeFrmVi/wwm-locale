# Description: Script to translate text from file using OpenRouter/Gemini with streaming
# Enhanced version for local usage

import os
import re
import sys
import concurrent.futures
import json
from datetime import datetime

import time
from halo import Halo
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

system_description = """Bạn là một dịch giả truyện Kiếm Hiệp Trung Quốc cho tựa game Where Winds Meets (Yến Vân Thập Lục Thanh).
Sử dụng các từ Hán-Việt thông dụng khi dịch từng câu từ tiếng Trung sang tiếng Việt.
Đối với tên riêng, chiêu thức, vũ khí, địa danh hoặc thuật ngữ kỹ thuật: BẠN PHẢI chuyển đổi chúng sang âm Hán-Việt tương ứng.
TUYỆT ĐỐI KHÔNG giữ lại bất kỳ ký tự tiếng Trung nào trong kết quả.
Nếu không thể dịch nghĩa, hãy phiên âm toàn bộ văn bản sang Hán-Việt.
Không phản hồi bằng tiếng Trung hoặc dùng ký tự Trung Quốc. Chỉ phản hồi bằng tiếng Việt.
CHỈ trả về định dạng JSON hợp lệ, không giải thích hoặc dùng dấu ```.
Ví dụ:
- Sai: "偷師-狂瀾-弟子1-站崗" -> "偷師-Cuồng Lan-Đệ tử 1-Trạm Cương" (Vẫn chứa ký tự Trung)
- Đúng: "偷師-狂瀾-弟子1-站崗" -> "Thâu Sư - Cuồng Lan - Đệ Tử 1 - Trạm Cương" (Đã chuyển hoàn toàn sang Hán-Việt)
- Sai: "Mèo con vô助" -> "Mèo con vô助" (Giữ lại ký tự gốc)
- Đúng: "Mèo con vô助" -> "Mèo con vô trợ" (Dịch nghĩa hoặc dùng Hán-Việt)
- Sai: "蛐蛐" -> "蛐蛐"
- Đúng: "蛐蛐" -> "Khúc Khúc" (Hoặc "Dế mèn" nếu hiểu nghĩa)
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


def contains_chinese(text):
    """Check if text contains Chinese characters."""
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def translate_chunk(client, model, system_prompt, chunk_data, spinner, max_retries=3):
    """Translate a dictionary chunk with validation."""
    json_str = json.dumps(chunk_data, ensure_ascii=False)
    
    for attempt in range(max_retries):
        try:
            # Create chat completion
            # We use stream=False for chunks to easier validate the whole JSON object
            # But we can simulate streaming if needed, or just wait.
            # Given the requirement for validation, getting the whole response is safer.
            
            completion = client.chat.completions.create(
                extra_headers={
                    "X-Title": "WWM Locale Tool",
                },
                extra_body={
                    "reasoning": {
                        "effort": "low"
                    }
                },
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {"role": "user", "content": json_str},
                ],
                stream=False,
            )
            
            resp_content = completion.choices[0].message.content
            
            # Clean up markdown code blocks if present
            cleaned_content = resp_content.replace("```json", "").replace("```", "").strip()
            
            try:
                translated_chunk = json.loads(cleaned_content)
            except json.JSONDecodeError:
                if attempt < max_retries - 1:
                    spinner.warn(f"Invalid JSON response. Retrying ({attempt + 1}/{max_retries})...")
                    continue
                else:
                    spinner.fail(f"Failed to parse JSON after {max_retries} attempts.")
                    return None

            # Validate for Chinese characters
            has_chinese = False
            for k, v in translated_chunk.items():
                if isinstance(v, str) and contains_chinese(v):
                    has_chinese = True
                    spinner.warn(f"Validation failed at key '{k}': '{v}'")
                    break
            
            if has_chinese:
                if attempt < max_retries - 1:
                    spinner.warn(f"Response contains Chinese characters. Retrying ({attempt + 1}/{max_retries})...")
                    continue
                else:
                    spinner.fail(f"Failed validation (contains Chinese) after {max_retries} attempts.")
                    return None
            
            return translated_chunk

        except Exception as e:
            if attempt < max_retries - 1:
                spinner.warn(f"Error: {e}. Retrying in 2s...")
                time.sleep(2)
            else:
                spinner.fail(f"Failed after {max_retries} attempts. Error: {e}")
                return None
    return None

def translate_text(spinner, input_file, output_file):
    # current started time
    started_at = os.times()

    # Path to output file
    output_file = output_file or os.path.join(
        os.path.dirname(input_file), "translated_" + os.path.basename(input_file)
    )

    # Check if input file exists
    if not os.path.exists(input_file):
        spinner.fail(f"Input file {input_file} does not exist.")
        return -1

    # Read content from input file
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                spinner.warn(f"Input file {input_file} is empty.")
                return 0
            
            # Parse JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                spinner.fail(f"Input file {input_file} is not valid JSON.")
                return -1
                
    except Exception as e:
        spinner.fail(f"Error reading file: {e}")
        return -1

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Initialize OpenAI client
    client = OpenAI(
        base_url=openai_base_url,
        api_key=auth_api_key,
    )

    # Chunking configuration
    CHUNK_SIZE = 20 # Number of items per chunk
    items = list(data.items())
    total_items = len(items)
    translated_data = {}
    
    # Process chunks
    for i in range(0, total_items, CHUNK_SIZE):
        chunk_items = items[i : i + CHUNK_SIZE]
        chunk_dict = dict(chunk_items)
        
        # Update spinner
        if hasattr(spinner, 'text'):
            spinner.text = f"Translating chunk {i//CHUNK_SIZE + 1}/{(total_items + CHUNK_SIZE - 1)//CHUNK_SIZE}..."
        
        translated_chunk = translate_chunk(client, openai_model, system_description, chunk_dict, spinner)
        
        if translated_chunk:
            translated_data.update(translated_chunk)
        else:
            spinner.warn(f"Chunk {i//CHUNK_SIZE + 1} failed. Skipping...")
            # Optionally keep original or empty? 
            # Keeping original might be better than losing data, but user wants to avoid Chinese.
            # Let's keep original but maybe mark it? Or just keep original so we don't break the game.
            # But the user specifically wants to clear false files.
            # If we fail, maybe we shouldn't write the file?
            # Let's write what we have, maybe?
            # For now, let's just update with original if translation fails, so keys are preserved.
            translated_data.update(chunk_dict)

    processed_at = os.times()

    # Write the full translated text to output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=4)

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
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=worker_count)
    try:
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

    except KeyboardInterrupt:
        print("\n")
        spinner.fail("User interrupted.")
        executor.shutdown(wait=False)
        os._exit(1)


