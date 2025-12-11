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

def get_system_prompt():
    """Read system prompt from local file or return default."""
    prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
    if os.path.exists(prompt_path):
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Warning: Failed to read system_prompt.txt: {e}")
            
    # Fallback prompt if file not found
    return """Bạn là một dịch giả chuyên nghiệp cho tựa game Kiếm Hiệp "Where Winds Meets" (Yến Vân Thập Lục Thanh).
Nhiệm vụ của bạn là dịch văn bản từ tiếng Trung sang tiếng Việt, đảm bảo văn phong tự nhiên, dễ hiểu cho người đọc, phù hợp với bối cảnh cổ trang nhưng không lạm dụng từ Hán-Việt.
Quy tắc dịch thuật:
1. **Văn phong**: Dịch nghĩa sang tiếng Việt thuần Việt, tự nhiên, trôi chảy cho các câu thoại, mô tả. Tránh dịch word-by-word (âm Hán-Việt) gây khó hiểu.
   - Ví dụ: "用强只怕激得病更重" -> Dịch là "Dùng sức mạnh chỉ sợ làm bệnh nặng thêm" (KHÔNG dịch là "Dụng cường chỉ phạ kích đắc bệnh cánh trọng").
2. **Thuật ngữ & Tên riêng**: Giữ nguyên âm Hán-Việt cho:
   - Tên người, Tên địa danh.
   - Tên chiêu thức, võ công, vũ khí.
   - Các thuật ngữ tu tiên, kiếm hiệp đặc thù.
3. **Tuyệt đối KHÔNG để lại ký tự tiếng Trung**: Nếu không dịch được nghĩa, hãy phiên âm Hán-Việt, nhưng ưu tiên dịch nghĩa nếu có thể.
4. **Định dạng**: Chỉ trả về JSON hợp lệ. Không bao gồm markdown hay giải thích thêm.
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

def is_technical_string(text):
    """Check if string is technical/system data that shouldn't be translated."""
    if not isinstance(text, str):
        return False
    # Database table patterns
    if re.search(r'[\u4e00-\u9fff]*表[》\]]', text):  # ends with 表》 or 表]
        return True
    # Contains code-like patterns with underscores and equals
    if re.search(r'\w+_\w+.*=', text):
        return True
    # Mostly special characters/code
    special_chars = sum(1 for c in text if c in '_=<>[]{}()《》')
    if len(text) > 0 and special_chars / len(text) > 0.15:
        return True
    return False

def translate_chunk(client, model, system_prompt, chunk_data, spinner, max_retries=5):
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
                    # "reasoning": {
                    #     "effort": "low"
                    # },
                    # "provider": {
                    #     "order": ["siliconflow/fp8", "atlas-cloud/fp8", "gmicloud/fp8"]
                    # }
                },
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {"role": "user", "content": json_str},
                ],
                stream=True
            )
            
            resp_content = ""
            for chunk in completion:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    resp_content += delta
                    if hasattr(spinner, 'update_text'):
                        spinner.update_text(resp_content)
            
            # Clean up markdown code blocks if present
            cleaned_content = resp_content.replace("```json", "").replace("```", "").strip()
            
            # Detect if LLM output explanation instead of JSON
            if not cleaned_content.startswith("{"):
                if attempt < max_retries - 1:
                    spinner.warn(f"Response is not JSON (starts with text). Retrying ({attempt + 1}/{max_retries})...")
                    continue
                else:
                    spinner.fail(f"Failed: LLM returned explanation instead of JSON.")
                    return None
            
            try:
                translated_chunk = json.loads(cleaned_content)
            except json.JSONDecodeError:
                if attempt < max_retries - 1:
                    spinner.warn(f"Invalid JSON response. Retrying ({attempt + 1}/{max_retries})...")
                    continue
                else:
                    spinner.fail(f"Failed to parse JSON after {max_retries} attempts.")
                    return None

            # Validate key count matches input
            if len(translated_chunk) != len(chunk_data):
                if attempt < max_retries - 1:
                    spinner.warn(f"Key count mismatch ({len(translated_chunk)}/{len(chunk_data)}). Retrying ({attempt + 1}/{max_retries})...")
                    continue
                else:
                    spinner.fail(f"Failed: output has {len(translated_chunk)} keys, expected {len(chunk_data)}.")
                    return None

            # Validate for Chinese characters (skip technical strings)
            has_chinese = False
            for k, v in translated_chunk.items():
                if isinstance(v, str) and contains_chinese(v) and not is_technical_string(v):
                    has_chinese = True
                    spinner.warn(f"Validation failed at key '{k}': '{v[:80]}...'")
                    break
            
            if has_chinese:
                if attempt < max_retries - 1:
                    spinner.warn(f"Response contains Chinese characters. Retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(2)
                    continue
                else:
                    spinner.fail(f"Failed validation (contains Chinese) after {max_retries} attempts.")
                    return None
            
            return translated_chunk

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 5 * (attempt + 1)
                spinner.warn(f"Error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
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

    # Translate the whole file at once
    if hasattr(spinner, 'text'):
        spinner.text = f"Translating {os.path.basename(input_file)}..."

    
    # Get the latest system prompt
    current_system_prompt = get_system_prompt()
    translated_data = translate_chunk(client, openai_model, current_system_prompt, data, spinner)

    if not translated_data:
        spinner.warn(f"Translation failed for {os.path.basename(input_file)}. Keeping original data.")
        translated_data = data
    
    processed_at = os.times()

    # Write the full translated text to output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=2)

    return processed_at[4] - started_at[4]


class DummySpinner:
    """Thread-safe spinner replacement for parallel execution."""
    def __init__(self, filename=""):
        self.text = ""
        self.filename = filename
    def fail(self, msg): print(f"\r✖ {msg}")
    def warn(self, msg): print(f"\r⚠ {msg}")
    def info(self, msg): print(f"\rℹ {msg}")
    def succeed(self, msg): print(f"\r✔ {msg}")
    def update_text(self, text):
        preview = text.replace("\n", " ").strip()[-100:]
        print(f"\r⠙ {self.filename}: ...{preview}", end="", flush=True)


def process_file(idx, filename, input_file, output_file, total_files):
    # Create a new spinner for each thread (or just print since spinner isn't thread-safe)
    print(f"[{idx + 1}/{total_files}] Translating {filename}...")
    
    spinner = DummySpinner(filename)
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
    # Process files in parallel
    # Default to CPU count, fallback to 1 if undetermined
    default_workers = os.cpu_count() or 1
    worker_count = int(os.getenv("WORKER_COUNT", str(default_workers)))
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
            # Enhanced: Check if ALL keys from source file exist in translated files
            
            # Extract ID from filename (e.g., entry_00123.json -> 00123)
            match = re.match(r"^.+?_(\d+)\.json$", filename)
            if match:
                file_id = match.group(1)
                # Look for any file ending with _{file_id}.json in output_folder
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder, exist_ok=True)
                existing_files = [f for f in os.listdir(output_folder) if f.endswith(f"_{file_id}.json") and not f.startswith("._")]
                
                if existing_files:
                    # Load source file to get all keys
                    try:
                        with open(input_file, "r", encoding="utf-8") as f:
                            source_data = json.load(f)
                            source_keys = set(source_data.keys())
                        
                        # Check if all keys exist in any of the existing translated files
                        all_keys_found = False
                        target_file = None
                        translated_data = None
                        translated_keys = set()
                        
                        for existing_file in existing_files:
                            try:
                                existing_path = os.path.join(output_folder, existing_file)
                                with open(existing_path, "r", encoding="utf-8") as f:
                                    translated_data = json.load(f)
                                    translated_keys = set(translated_data.keys())
                                    
                                    if source_keys.issubset(translated_keys):
                                        all_keys_found = True
                                        spinner.info(f"[{idx + 1}/{len(json_files)}] Skipping {filename} (all {len(source_keys)} keys exist in {existing_file})")
                                        break
                                    else:
                                        # Found partial translation - we'll use this file
                                        target_file = existing_path
                                        break
                            except:
                                continue
                        
                        if all_keys_found:
                            continue
                        
                        # If we have a partial translation, translate only missing keys
                        if target_file and translated_data is not None:
                            missing_keys = source_keys - translated_keys
                            if missing_keys:
                                spinner.warn(f"[{idx + 1}/{len(json_files)}] Found {len(missing_keys)} missing keys in {os.path.basename(target_file)}, translating only those...")
                                
                                # Create a subset with only missing keys
                                missing_data = {k: source_data[k] for k in missing_keys}
                                
                                # Translate missing keys inline
                                client = OpenAI(base_url=openai_base_url, api_key=auth_api_key)
                                current_system_prompt = get_system_prompt()
                                mini_spinner = DummySpinner(filename)
                                
                                translated_missing = translate_chunk(client, openai_model, current_system_prompt, missing_data, mini_spinner)
                                
                                if translated_missing:
                                    # Merge with existing translation
                                    translated_data.update(translated_missing)
                                    
                                    # Write back to the same file
                                    with open(target_file, "w", encoding="utf-8") as f:
                                        json.dump(translated_data, f, ensure_ascii=False, indent=2)
                                    
                                    spinner.succeed(f"[{idx + 1}/{len(json_files)}] Added {len(translated_missing)} keys to {os.path.basename(target_file)}")
                                else:
                                    spinner.warn(f"[{idx + 1}/{len(json_files)}] Failed to translate missing keys for {filename}")
                                
                                continue
                    except Exception as e:
                        spinner.warn(f"[{idx + 1}/{len(json_files)}] Error checking keys for {filename}: {e}")
            
            # Fallback check for exact filename match if pattern doesn't match
            else:
                existing_files = [f for f in os.listdir(output_folder) if f.endswith(f"_{filename}") and not f.startswith("._")]
                if existing_files:
                    # Same key-based check for non-numbered files
                    try:
                        with open(input_file, "r", encoding="utf-8") as f:
                            source_data = json.load(f)
                            source_keys = set(source_data.keys())
                        
                        all_keys_found = False
                        for existing_file in existing_files:
                            try:
                                with open(os.path.join(output_folder, existing_file), "r", encoding="utf-8") as f:
                                    translated_data = json.load(f)
                                    if source_keys.issubset(set(translated_data.keys())):
                                        all_keys_found = True
                                        spinner.info(f"[{idx + 1}/{len(json_files)}] Skipping {filename} (all keys exist in {existing_file})")
                                        break
                            except:
                                continue
                        
                        if all_keys_found:
                            continue
                    except:
                        pass

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


