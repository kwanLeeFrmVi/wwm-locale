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
                    # Allow partial failure? For now strict.
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
        # Empty source, just touch output if not exists
        if not os.path.exists(output_file):
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
        return

    # 2. Prepare final data
    final_data = {}
    
    # Load existing output if present (Resume)
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
                if isinstance(existing, dict):
                    final_data.update(existing)
        except:
            pass

    # 3. Identify missing keys
    missing_data = {}
    
    for k, v in source_data.items():
        if k in final_data:
            continue # Already translated in this file
            
        # Check global map
        if k in GLOBAL_TRANSLATION_MAP:
            # Reuse translation from another file
            final_data[k] = GLOBAL_TRANSLATION_MAP[k]
        else:
            # truly missing
            missing_data[k] = v
            
    # 4. If no missing keys, we are done
    if not missing_data:
        # Save file to ensure it exists with all content
        # with open(output_file, "w", encoding="utf-8") as f:
        #     json.dump(final_data, f, ensure_ascii=False, indent=2)
        print(f"✔ [{idx + 1}/{total_files}] {filename} (Skipped - All keys already exist)")
        return

    # 5. Translate missing keys
    print(f"[{idx + 1}/{total_files}] Translating {filename} ({len(missing_data)} new keys)...")
    
    # Initialize OpenAI client
    client = OpenAI(
        base_url=openai_base_url,
        api_key=auth_api_key,
    )
    
    current_system_prompt = get_system_prompt()
    started_at = time.time()
    
    translated_chunk = translate_chunk(client, openai_model, current_system_prompt, missing_data, spinner)
    
    if translated_chunk:
        final_data.update(translated_chunk)
        # Verify length
        # (Optional)
    else:
        print(f"⚠ [{idx + 1}/{total_files}] Translation failed for {filename}. partial save.")
        # We can trigger failure or just save whatever we have (original values for missing?)
        # For now, let's keep missing as original or just don't update?
        # User prompt implies "Translate text". If fail, maybe keep original?
        # Let's keep original for failed keys to avoid data loss in output
        for k, v in missing_data.items():
            if k not in final_data:
                final_data[k] = v

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    duration = time.time() - started_at
    print(f"✔ [{idx + 1}/{total_files}] {filename} finished in {duration:.2f}s")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python trans-local.py <source folder> <output folder>")
        sys.exit(1)

    missing_folder = sys.argv[1]
    output_folder = sys.argv[2]

    # Collect the streamed response
    spinner = Halo(text="Processing", spinner="dots")
    
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

    # Load global translations FIRST
    load_global_translations(output_folder, spinner)
    spinner.start()

    now = datetime.now()
    run_at = (
        f"{now.strftime('%y')}"  # Year in 2 digits
        f"{now.strftime('%V')}"  # Week of year (ISO)
        f"{now.strftime('%u')}"  # Day of week (1-7)
        f"{now.strftime('%H')}"  # Hour 24h
        f"{now.strftime('%M')}"  # Minute
    )

    # Process files in parallel
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

        # Wait for all futures to complete
        for future in concurrent.futures.as_completed(futures):
            pass

        spinner.succeed("All tasks completed.")

    except KeyboardInterrupt:
        print("\n")
        spinner.fail("User interrupted.")
        executor.shutdown(wait=False)
        os._exit(1)
