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

# Global translation memory
GLOBAL_TRANSLATION_MAP = {}

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

def load_global_translations(folder, spinner=None):
    """Load all existing translations from output folder into global map."""
    global GLOBAL_TRANSLATION_MAP
    if not os.path.exists(folder): return
    
    files = sorted([f for f in os.listdir(folder) if f.endswith(".json") and not f.startswith("._")])
    if not files: return

    if spinner: 
        spinner.start(f"Loading existing translations from {len(files)} files (deduplication)...")
    
    for f in files:
        try:
            path = os.path.join(folder, f)
            with open(path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                if isinstance(data, dict):
                    # Update global map. Last file wins if duplicates exist.
                    # Filter out empty or whitespace-only keys
                    valid_data = {k: v for k, v in data.items() if v and isinstance(v, str) and v.strip()}
                    GLOBAL_TRANSLATION_MAP.update(valid_data)
        except Exception:
            pass
    
    if spinner: 
        spinner.succeed(f"Loaded {len(GLOBAL_TRANSLATION_MAP)} unique keys from {len(files)} files.")


def translate_chunk(client, model, system_prompt, chunk_data, spinner, max_retries=5):
    """Translate a dictionary chunk with validation."""
    json_str = json.dumps(chunk_data, ensure_ascii=False)
    
    for attempt in range(max_retries):
        try:
            # Create chat completion
            completion = client.chat.completions.create(
                extra_headers={
                    "X-Title": "WWM Locale Tool",
                },
                extra_body={
                    # "reasoning": { "effort": "low" },
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
                # Check for 502/HTML in response content as well
                if "<html>" in cleaned_content or "502 Bad Gateway" in cleaned_content:
                     raise Exception("Server returned 502 Bad Gateway (HTML Response)")

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
                missing_keys = set(chunk_data.keys()) - set(translated_chunk.keys())
                extra_keys = set(translated_chunk.keys()) - set(chunk_data.keys())
                
                if missing_keys:
                    spinner.warn(f"Missing keys: {list(missing_keys)[:3]}...")
                if extra_keys:
                    spinner.warn(f"Extra keys: {list(extra_keys)[:3]}...")
                
                if attempt < max_retries - 1:
                    spinner.warn(f"Key count mismatch ({len(translated_chunk)}/{len(chunk_data)}). Retrying ({attempt + 1}/{max_retries})...")
                    time.sleep(3)
                    continue
                else:
                    # On final failure, fill in missing keys with original values
                    spinner.warn(f"Final attempt failed. Filling missing keys with original values.")
                    for key in missing_keys:
                        translated_chunk[key] = chunk_data[key]
                    return translated_chunk

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
                    time.sleep(5)  # Longer wait for LLM to reset
                    continue
                else:
                    # On final failure, clean up Chinese characters
                    spinner.warn("Final attempt had Chinese. Cleaning up...")
                    cleaned_chunk = {}
                    for k, v in translated_chunk.items():
                        if isinstance(v, str) and contains_chinese(v):
                            # Remove Chinese chars and clean up
                            cleaned = ''.join(c if ord(c) < 0x4E00 or ord(c) > 0x9FFF else ' ' for c in v)
                            cleaned = ' '.join(cleaned.split())  # Clean multiple spaces
                            if cleaned.strip():
                                cleaned_chunk[k] = cleaned
                            else:
                                # If nothing left, keep original
                                cleaned_chunk[k] = chunk_data[k]
                        else:
                            cleaned_chunk[k] = v
                    return cleaned_chunk
            
            return translated_chunk
        except Exception as e:
            import random
            error_msg = str(e)
            # Detect server/connection issues
            is_server_error = any(x in error_msg.lower() for x in [
                "502 bad gateway", "<html>", "connection error", 
                "connection reset", "connection refused", "timeout",
                "remotedisconnected", "connectionerror"
            ])
            
            if is_server_error:
                if "502" in error_msg:
                    error_msg = "502 Bad Gateway (Server Overloaded)"
                elif "connection" in error_msg.lower():
                    error_msg = "Connection error"
                # Exponential backoff with jitter for server issues
                base_wait = 10 * (2 ** attempt)  # 10, 20, 40, 80...
                jitter = random.uniform(0, 5)
                wait_time = min(base_wait + jitter, 120)  # cap at 2 minutes
            else:
                wait_time = 5 * (attempt + 1)

            if attempt < max_retries - 1:
                spinner.warn(f"Error: {error_msg}. Retrying in {wait_time:.0f}s...")
                time.sleep(wait_time)
            else:
                spinner.fail(f"Failed after {max_retries} attempts. Error: {error_msg}")
                return None
    return None

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
    # check keys using global map + local file check
    # We want to minimize API calls
    
    spinner = DummySpinner(filename)
    
    # 1. Read source
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            source_data = json.load(f)
    except Exception as e:
        print(f"✖ Error reading {filename}: {e}")
        return

    if not source_data:
        print(f"✔ [{idx + 1}/{total_files}] {filename} (Empty source)")
        return

    # 2. Identify missing keys
    missing_data = {}
    reused_count = 0
    
    for k, v in source_data.items():
        # Skip empty values (from 0xFF markers)
        if not v or not isinstance(v, str) or not v.strip():
            continue
        # Check global map
        if k in GLOBAL_TRANSLATION_MAP:
            reused_count += 1
        else:
            # truly missing
            missing_data[k] = v
            
    # 3. If no missing keys, we are done
    if not missing_data:
        print(f"✔ [{idx + 1}/{total_files}] {filename} (Skipped - All {reused_count} keys already exist)")
        return

    # 4. Translate missing keys
    missing_count = len(missing_data)
    missing_preview = list(missing_data.keys())[:3]
    print(f"[{idx + 1}/{total_files}] {filename}: Reusing {reused_count} keys, Translating {missing_count} NEW keys ({missing_preview})...")
    
    # Initialize OpenAI client
    client = OpenAI(
        base_url=openai_base_url,
        api_key=auth_api_key,
    )
    
    current_system_prompt = get_system_prompt()
    started_at = time.time()
    
    translated_chunk = translate_chunk(client, openai_model, current_system_prompt, missing_data, spinner)
    
    # 5. Write ONLY the translated keys (Delta update)
    data_to_save = {}
    if translated_chunk:
        data_to_save = translated_chunk
    else:
        print(f"⚠ [{idx + 1}/{total_files}] Translation failed for {filename}. partial save.")
        # If fail, save original missing strings so they are at least in the file?
        # Or just save nothing?
        # Let's save the original missing data as fallback
        data_to_save = missing_data

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)

    duration = time.time() - started_at
    print(f"✔ [{idx + 1}/{total_files}] {filename} finished in {duration:.2f}s")


def process_entries_chunk(idx, chunk_data, output_file, total_chunks, run_at):
    """Process a chunk from entries.json."""
    spinner = DummySpinner(f"chunk_{idx + 1}")
    
    if not chunk_data:
        print(f"✔ [{idx + 1}/{total_chunks}] Chunk empty, skipping")
        return
    
    # Filter out already translated keys
    missing_data = {}
    reused_count = 0
    
    for k, v in chunk_data.items():
        if k in GLOBAL_TRANSLATION_MAP:
            reused_count += 1
        else:
            missing_data[k] = v
    
    if not missing_data:
        print(f"✔ [{idx + 1}/{total_chunks}] chunk_{idx + 1} (Skipped - All {reused_count} keys exist)")
        return
    
    print(f"[{idx + 1}/{total_chunks}] chunk_{idx + 1}: Reusing {reused_count}, Translating {len(missing_data)} NEW keys...")
    
    # Initialize OpenAI client
    client = OpenAI(
        base_url=openai_base_url,
        api_key=auth_api_key,
    )
    
    current_system_prompt = get_system_prompt()
    started_at = time.time()
    
    translated_chunk = translate_chunk(client, openai_model, current_system_prompt, missing_data, spinner)
    
    if translated_chunk:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(translated_chunk, f, ensure_ascii=False, indent=2)
    else:
        print(f"⚠ [{idx + 1}/{total_chunks}] Translation failed for chunk_{idx + 1}")
        # Save original as fallback
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(missing_data, f, ensure_ascii=False, indent=2)
    
    duration = time.time() - started_at
    print(f"✔ [{idx + 1}/{total_chunks}] chunk_{idx + 1} finished in {duration:.2f}s")


def process_entries_file(entries_path, output_folder, chunk_size=265):
    """Stream process entries.json in chunks."""
    spinner = Halo(text="Processing entries.json", spinner="dots")
    
    # Load entries.json
    spinner.start("Loading entries.json...")
    try:
        with open(entries_path, 'r', encoding='utf-8') as f:
            all_entries = json.load(f)
    except Exception as e:
        spinner.fail(f"Failed to read {entries_path}: {e}")
        return
    
    # Filter out empty values
    valid_entries = {k: v for k, v in all_entries.items() 
                     if v and isinstance(v, str) and v.strip()}
    
    spinner.succeed(f"Loaded {len(valid_entries)} valid entries (filtered {len(all_entries) - len(valid_entries)} empty)")
    
    # Load existing translations
    load_global_translations(output_folder, spinner)
    
    # Filter out already translated
    missing_entries = {k: v for k, v in valid_entries.items() if k not in GLOBAL_TRANSLATION_MAP}
    
    if not missing_entries:
        spinner.succeed("All entries already translated!")
        return
    
    spinner.info(f"Need to translate {len(missing_entries)} entries")
    
    # Chunk the data
    entries_list = list(missing_entries.items())
    chunks = []
    for i in range(0, len(entries_list), chunk_size):
        chunk = dict(entries_list[i:i + chunk_size])
        chunks.append(chunk)
    
    spinner.info(f"Split into {len(chunks)} chunks of ~{chunk_size} keys each")
    
    now = datetime.now()
    run_at = (
        f"{now.strftime('%y')}"
        f"{now.strftime('%V')}"
        f"{now.strftime('%u')}"
        f"{now.strftime('%H')}"
        f"{now.strftime('%M')}"
    )
    
    os.makedirs(output_folder, exist_ok=True)
    
    # Process chunks in parallel
    default_workers = os.cpu_count() or 1
    worker_count = int(os.getenv("WORKER_COUNT", str(default_workers)))
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=worker_count)
    
    try:
        futures = []
        for idx, chunk_data in enumerate(chunks):
            output_file = os.path.join(output_folder, f"e{run_at}_{idx + 1:05d}.json")
            futures.append(executor.submit(process_entries_chunk, idx, chunk_data, output_file, len(chunks), run_at))
        
        for future in concurrent.futures.as_completed(futures):
            pass
        
        spinner.succeed("All chunks completed.")
    
    except KeyboardInterrupt:
        print("\n")
        spinner.fail("User interrupted.")
        executor.shutdown(wait=False)
        os._exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python trans-local.py <source folder OR entries.json> <output folder>")
        sys.exit(1)

    source_input = sys.argv[1]
    output_folder = sys.argv[2]

    # Detect mode: file (entries.json) or folder
    if os.path.isfile(source_input) and source_input.endswith(".json"):
        # Stream mode: process entries.json in chunks
        print(f"📂 Stream mode: Processing {source_input}")
        process_entries_file(source_input, output_folder)
    elif os.path.isdir(source_input):
        # Original folder mode
        missing_folder = source_input
        
        spinner = Halo(text="Processing", spinner="dots")
        
        files = sorted(os.listdir(missing_folder))
        json_files = [f for f in files if f.endswith(".json") and not f.startswith("._")]
        
        if not json_files:
            spinner.warn(f"No JSON files found in '{missing_folder}'.")
            sys.exit(0)

        load_global_translations(output_folder, spinner)
        spinner.start()

        now = datetime.now()
        run_at = (
            f"{now.strftime('%y')}"
            f"{now.strftime('%V')}"
            f"{now.strftime('%u')}"
            f"{now.strftime('%H')}"
            f"{now.strftime('%M')}"
        )

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

                futures.append(executor.submit(process_file, idx, filename, input_file, output_file, len(json_files)))

            for future in concurrent.futures.as_completed(futures):
                pass

            spinner.succeed("All tasks completed.")

        except KeyboardInterrupt:
            print("\n")
            spinner.fail("User interrupted.")
            executor.shutdown(wait=False)
            os._exit(1)
    else:
        print(f"Error: '{source_input}' is not a valid folder or .json file.")
        sys.exit(1)
