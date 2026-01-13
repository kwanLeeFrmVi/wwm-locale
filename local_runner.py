#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import zipfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
BIN_YANYUN = "./bin/yanyun"
SCRIPT_MERGE = "./scripts/merge-text.py"
SCRIPT_TRANS = "./scripts/trans-local.py"
SCRIPT_EXTRACT = "./scripts/extract-missing-keys.py"
WORKS_DIR = os.path.abspath("./works")
OUTPUT_DIR = os.path.abspath("./output")

# Language Resources
LANG = {
    "en": {
        "menu_title": "=== WWM Locale Tool ===",
        "menu_unpack": "1. Unpack words_map (Base + Diff)",
        "menu_unpack_single": "2. Unpack single file",
        "menu_pack": "3. Pack words_map",
        "menu_translate": "4. Translate text",
        "menu_extract": "5. Extract missing keys from entries.json",
        "menu_lang": "6. Đổi ngôn ngữ (Tiếng Việt)",
        "menu_exit": "0. Exit",
        "prompt_choice": "Choose an option: ",
        "prompt_words_map": "Enter path or URL to words_map file: ",
        "prompt_patched_zip": "Enter path or URL to patched zip file or directory: ",
        "prompt_source_dir": "Enter source directory (containing .json files): ",
        "prompt_output_dir": "Enter output directory: ",
        "msg_unpacking": "Unpacking...",
        "msg_packing": "Packing...",
        "msg_translating": "Translating...",
        "msg_done": "Done!",
        "msg_error": "Error: {}",
        "msg_file_not_found": "File/Directory not found: {}",
        "msg_invalid_choice": "Invalid choice.",
        "msg_press_enter": "Press Enter to continue...",
    },
    "vi": {
        "menu_title": "=== Công cụ Việt hóa WWM ===",
        "menu_unpack": "1. Giải nén words_map (Base + Diff)",
        "menu_unpack_single": "2. Giải nén file đơn",
        "menu_pack": "3. Đóng gói words_map",
        "menu_translate": "4. Dịch văn bản",
        "menu_extract": "5. Trích xuất key thiếu từ entries.json",
        "menu_lang": "6. Switch Language (English)",
        "menu_exit": "0. Thoát",
        "prompt_choice": "Chọn một tùy chọn: ",
        "prompt_words_map": "Nhập đường dẫn hoặc URL đến file words_map: ",
        "prompt_patched_zip": "Nhập đường dẫn hoặc URL đến file zip hoặc thư mục đã sửa: ",
        "prompt_source_dir": "Nhập thư mục nguồn (chứa các file .json): ",
        "prompt_output_dir": "Nhập thư mục đầu ra: ",
        "msg_unpacking": "Đang giải nén...",
        "msg_packing": "Đang đóng gói...",
        "msg_translating": "Đang dịch...",
        "msg_done": "Hoàn tất!",
        "msg_error": "Lỗi: {}",
        "msg_file_not_found": "Không tìm thấy file/thư mục: {}",
        "msg_invalid_choice": "Lựa chọn không hợp lệ.",
        "msg_press_enter": "Nhấn Enter để tiếp tục...",
    }
}

current_lang = "en"

def t(key):
    return LANG[current_lang].get(key, key)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def ensure_executable(path):
    if os.path.exists(path):
        st = os.stat(path)
        os.chmod(path, st.st_mode | 0o111)

def run_command(command, shell=False):
    try:
        subprocess.run(command, shell=shell, check=True, stdin=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(t("msg_error").format(e))
        return False
    return True

def download_file(url, dest):
    # Simple curl wrapper
    cmd = ["curl", "-L", url, "-o", dest]
    return run_command(cmd)

def force_move(src, dst_dir):
    filename = os.path.basename(src)
    # Ignore junk
    if filename == "__MACOSX" or filename.startswith("._") or filename == ".DS_Store":
        return

    dst = os.path.join(dst_dir, filename)
    if os.path.exists(dst):
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        else:
            os.remove(dst)
    shutil.move(src, dst)

def prepare_workspace():
    os.makedirs(WORKS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_workspace():
    if os.path.exists(WORKS_DIR):
        shutil.rmtree(WORKS_DIR, ignore_errors=True)
    prepare_workspace()

def task_unpack_single():
    """Unpack a single words_map file directly to output/"""
    file_input = input(f"{t('prompt_words_map')}: ").strip().strip("'\"")
    if not file_input: return
    
    if file_input.startswith("http"):
        local_path = os.path.join(WORKS_DIR, "temp_map")
        if not download_file(file_input, local_path): return
        file_input = local_path
    
    if not os.path.exists(file_input):
        print(t("msg_file_not_found").format(file_input))
        return
    
    print(f"Unpacking: {file_input}")
    ensure_executable(BIN_YANYUN)
    if not run_command([BIN_YANYUN, file_input]): return
    
    basename = os.path.basename(file_input)
    stem = os.path.splitext(basename)[0]
    unpacked_path = os.path.join(OUTPUT_DIR, stem)
    
    print(t("msg_done"))
    print(f"Output directory: {unpacked_path}")


def task_unpack():
    clean_workspace()
    
    # 1. Base Map
    base_input = input(f"{t('prompt_words_map')} (Base): ").strip().strip("'\"")
    if not base_input: return
    
    local_base = os.path.join(WORKS_DIR, "base")
    if base_input.startswith("http"):
        if not download_file(base_input, os.path.join(WORKS_DIR, "base_map")): return
        base_input = os.path.join(WORKS_DIR, "base_map")
    
    if not os.path.exists(base_input):
        print(t("msg_file_not_found").format(base_input))
        return

    print(f"Unpacking Base: {base_input}")
    os.makedirs(local_base, exist_ok=True)
    shutil.copy(base_input, os.path.join(local_base, "words_map")) # Helper for unpack_map logic if needed, but we pass path directly
    
    ensure_executable(BIN_YANYUN)
    if not run_command([BIN_YANYUN, base_input]): return
    
    # yanyun outputs to "output/<basename>", need to move to works/base
    # The tool uses the basename of input file. 
    # To avoid confusion, let's look at where it outputted.
    # Actually yanyun outputs to `./output/` relative to CWD.
    basename = os.path.basename(base_input)
    # yanyun binary uses hardcoded "output" dir in CWD
    
    # Wait, yanyun binary behavior:
    # "let output_dir = Path::new(OUTPUT_DIR).join(file_stem);"
    # OUTPUT_DIR is "output".
    # So if input is ".../translate_words_map_en", output is "./output/translate_words_map_en"
    
    stem = os.path.splitext(basename)[0]
    unpacked_path = os.path.join(OUTPUT_DIR, stem) # ./output/translate_words_map_en
    
    if os.path.exists(unpacked_path):
        if os.path.exists(local_base): 
            shutil.rmtree(local_base, ignore_errors=True)
        shutil.move(unpacked_path, local_base)
    else:
        print(t("msg_error").format(f"Unpacked directory not found: {unpacked_path}"))
        return

    # 2. Diff Map (Optional)
    diff_input = input(f"{t('prompt_words_map')} (Diff) [Optional]: ").strip().strip("'\"")
    has_diff = False
    
    if diff_input:
        local_diff = os.path.join(WORKS_DIR, "diff")
        if diff_input.startswith("http"):
             if not download_file(diff_input, os.path.join(WORKS_DIR, "diff_map")): return
             diff_input = os.path.join(WORKS_DIR, "diff_map")
        
        if os.path.exists(diff_input):
            print(f"Unpacking Diff: {diff_input}")
            if run_command([BIN_YANYUN, diff_input]):
                diff_basename = os.path.basename(diff_input)
                diff_stem = os.path.splitext(diff_basename)[0]
                diff_unpacked_path = os.path.join(OUTPUT_DIR, diff_stem)
                
                if os.path.exists(diff_unpacked_path):
                    if os.path.exists(local_diff): 
                        shutil.rmtree(local_diff, ignore_errors=True)
                    shutil.move(diff_unpacked_path, local_diff)
                    has_diff = True
                else:
                     print(t("msg_error").format(f"Unpacked directory not found: {diff_unpacked_path}"))
        else:
             print(t("msg_file_not_found").format(diff_input))

    # 3. Create Merged View
    # Copy base text -> works/words_map/text
    # Copy diff text -> works/words_map/text (overwrite)
    print("Creating merged text view...")
    
    merged_view_dir = os.path.join(OUTPUT_DIR, "words_map") # Output to ./output/words_map
    os.makedirs(merged_view_dir, exist_ok=True)
    
    base_text = os.path.join(local_base, "text")
    merged_text = os.path.join(merged_view_dir, "text")
    
    if os.path.exists(base_text):
        shutil.copytree(base_text, merged_text, dirs_exist_ok=True)
        
    if has_diff:
        diff_text = os.path.join(WORKS_DIR, "diff", "text")
        if os.path.exists(diff_text):
            # shutil.copytree with dirs_exist_ok=True overwrites
            shutil.copytree(diff_text, merged_text, dirs_exist_ok=True)
    
    # Also merge entries.json files
    import json
    base_entries_path = os.path.join(local_base, "entries.json")
    merged_entries = {}
    if os.path.exists(base_entries_path):
        with open(base_entries_path, 'r', encoding='utf-8') as f:
            merged_entries = json.load(f)
    
    if has_diff:
        diff_entries_path = os.path.join(WORKS_DIR, "diff", "entries.json")
        if os.path.exists(diff_entries_path):
            with open(diff_entries_path, 'r', encoding='utf-8') as f:
                diff_entries = json.load(f)
                # Only update if diff value is non-empty (skip 0xFF markers that became "")
                for key, value in diff_entries.items():
                    if value:  # Skip empty strings
                        merged_entries[key] = value
    
    merged_entries_path = os.path.join(merged_view_dir, "entries.json")
    with open(merged_entries_path, 'w', encoding='utf-8') as f:
        json.dump(merged_entries, f, ensure_ascii=False, indent=2)
    
    # Extract keys from entries.json that are missing in text/ dir
    print("Checking for keys missing in text/ directory...")
    text_keys = set()
    for json_file in Path(merged_text).glob("*.json"):
        if not json_file.name.startswith("._"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    text_keys.update(json.load(f).keys())
            except Exception:
                pass
    
    missing_keys = set(merged_entries.keys()) - text_keys
    if missing_keys:
        print(f"Found {len(missing_keys)} keys in entries.json not present in text/ directory")
        print("Extracting missing keys (split into chunks)...")
        missing_data = {k: merged_entries[k] for k in missing_keys}
        
        # Split into chunks of 265 keys (matching existing file size)
        chunk_size = 265
        missing_list = sorted(missing_keys)
        chunk_count = 0
        
        for i in range(0, len(missing_list), chunk_size):
            chunk_keys = missing_list[i:i + chunk_size]
            chunk_data = {k: missing_data[k] for k in chunk_keys}
            chunk_count += 1
            
            missing_file = os.path.join(merged_text, f"missing_{chunk_count:05d}.json")
            with open(missing_file, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, ensure_ascii=False, indent=2)
        
        print(f"Extracted {len(missing_keys)} missing keys into {chunk_count} files (missing_00001.json - missing_{chunk_count:05d}.json)")
    
    # Copy tables from base (needed for packing)
    base_tables = os.path.join(local_base, "tables")
    merged_tables = os.path.join(merged_view_dir, "tables")
    if os.path.exists(base_tables):
        if os.path.exists(merged_tables):
            shutil.rmtree(merged_tables, ignore_errors=True)
        shutil.copytree(base_tables, merged_tables)
            
    print(t("msg_done"))
    print(f"Merged text directory: {merged_text}")
    print("You can now translate this directory.")


def task_pack():
    # clean_workspace() # Don't clean, we need the unpacked Base/Diff in ./works/base and ./works/diff
    
    # Check if we have previous unpacked state
    local_base = os.path.join(WORKS_DIR, "base")
    local_diff = os.path.join(WORKS_DIR, "diff")
    
    if not os.path.exists(local_base):
        print(t("msg_error").format("Base directory not found in workspace. Please Unpack first."))
        return
        
    patch_source = input(f"{t('prompt_patched_zip')} (default: ./dich-xong): ").strip().strip("'\"")
    if not patch_source:
        patch_source = "./dich-xong"
        
    if not os.path.exists(patch_source):
        print(t("msg_file_not_found").format(patch_source))
        return

    # Prepare patch source (unzip if needed)
    final_patch_source = patch_source
    temp_extract_dir = None
    
    if os.path.isfile(patch_source) and patch_source.endswith(".zip"):
        temp_extract_dir = os.path.join(WORKS_DIR, "temp_patch")
        print("Unzipping patch...")
        with zipfile.ZipFile(patch_source, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)
        final_patch_source = temp_extract_dir

    print(t("msg_packing"))
    ensure_executable(BIN_YANYUN)

    # 1. Update Base
    print("Updating & Packing Base...")
    # scripts/merge-text.py <target> <source>
    if not run_command([sys.executable, SCRIPT_MERGE, local_base, final_patch_source]): return
    
    # Cleanup metadata
    subprocess.run(["find", local_base, "-name", "._*", "-delete"], stderr=subprocess.DEVNULL)
    
    # Pack Base
    if not run_command([BIN_YANYUN, local_base]): return
    
    # Move Base Output
    # The tool outputs merged file to <input_dir>/merged/words_map
    base_packed = os.path.join(local_base, "merged", os.path.basename(local_base)) # "base"
    # Actually yanyun uses the folder name as filename. 
    # If we renamed folder to 'base', it outputs 'base'.
    # Check what yanyun does: "let file_name = dir_path.file_stem()..."
    # Yes, it uses folder name.
    
    # To get correct filename "translate_words_map_en", rename 'base' folder?
    # Or just rename the result.
    base_result_src = os.path.join(local_base, "merged", "base")
    if not os.path.exists(base_result_src):
         # Try looking for other files if name mismatch
         merged_dir = os.path.join(local_base, "merged")
         if os.path.exists(merged_dir):
             files = os.listdir(merged_dir)
             if files: base_result_src = os.path.join(merged_dir, files[0])
    
    final_base_dst = os.path.join(OUTPUT_DIR, "translate_words_map_en")
    shutil.move(base_result_src, final_base_dst)
    
    # 2. Update Diff (if exists)
    if os.path.exists(local_diff):
        print("Updating & Packing Diff...")
        if not run_command([sys.executable, SCRIPT_MERGE, local_diff, final_patch_source]): return
        
        subprocess.run(["find", local_diff, "-name", "._*", "-delete"], stderr=subprocess.DEVNULL)
        if not run_command([BIN_YANYUN, local_diff]): return
        
        # Diff packed
        diff_result_src = os.path.join(local_diff, "merged", "diff")
        if not os.path.exists(diff_result_src):
             merged_dir = os.path.join(local_diff, "merged")
             if os.path.exists(merged_dir):
                 files = os.listdir(merged_dir)
                 if files: diff_result_src = os.path.join(merged_dir, files[0])
        
        final_diff_dst = os.path.join(OUTPUT_DIR, "translate_words_map_en_diff")
        shutil.move(diff_result_src, final_diff_dst)

    if temp_extract_dir:
        shutil.rmtree(temp_extract_dir)

    print(t("msg_done"))
    print(f"Base Output: {final_base_dst}")
    if os.path.exists(local_diff):
        print(f"Diff Output: {os.path.join(OUTPUT_DIR, 'translate_words_map_en_diff')}")


def task_translate():
    default_dir = os.path.join(OUTPUT_DIR, "words_map", "text")
    prompt = f"{t('prompt_source_dir')} [{default_dir}]: "
    
    source_dir = input(prompt).strip().strip('\"')
    if not source_dir:
        source_dir = default_dir
        
    if not os.path.exists(source_dir):
        print(t("msg_file_not_found").format(source_dir))
        return

    default_out = "./dich-xong"
    prompt_out = f"{t('prompt_output_dir')} [{default_out}]: "
    output_dir = input(prompt_out).strip().strip('\"')
    if not output_dir:
        output_dir = default_out

    print(t("msg_translating"))
    
    # python scripts/trans-local.py <source> <output>
    cmd = [sys.executable, SCRIPT_TRANS, source_dir, output_dir]
    run_command(cmd)
    
    print(t("msg_done"))


def task_extract_missing():
    default_entries = os.path.join(OUTPUT_DIR, "words_map", "entries.json")
    prompt_entries = f"Enter path to entries.json [{default_entries}]: "
    
    entries_path = input(prompt_entries).strip().strip('\"')
    if not entries_path:
        entries_path = default_entries
    
    if not os.path.exists(entries_path):
        print(t("msg_file_not_found").format(entries_path))
        return
    
    default_dich_xong = "./dich-xong"
    prompt_dich_xong = f"Enter path to dich-xong folder [{default_dich_xong}]: "
    
    dich_xong_path = input(prompt_dich_xong).strip().strip('\"')
    if not dich_xong_path:
        dich_xong_path = default_dich_xong
    
    if not os.path.exists(dich_xong_path):
        print(t("msg_file_not_found").format(dich_xong_path))
        return
    
    default_output = "./missing-keys"
    prompt_output = f"Enter output folder for missing keys [{default_output}]: "
    
    output_path = input(prompt_output).strip().strip('\"')
    if not output_path:
        output_path = default_output
    
    print("Extracting missing keys...")
    cmd = [sys.executable, SCRIPT_EXTRACT, entries_path, dich_xong_path, output_path]
    run_command(cmd)
    
    print(t("msg_done"))
    print(f"\nNext step: Run option 4 to translate the extracted files in '{output_path}'")


def main():
    global current_lang
    while True:
        print("\n" + t("menu_title"))
        print(t("menu_unpack"))
        print(t("menu_unpack_single"))
        print(t("menu_pack"))
        print(t("menu_translate"))
        print(t("menu_extract"))
        print(t("menu_lang"))
        print(t("menu_exit"))
        
        choice = input(t("prompt_choice"))
        
        if choice == "1":
            task_unpack()
        elif choice == "2":
            task_unpack_single()
        elif choice == "3":
            task_pack()
        elif choice == "4":
            task_translate()
        elif choice == "5":
            task_extract_missing()
        elif choice == "6":
            current_lang = "vi" if current_lang == "en" else "en"
            clear_screen()
        elif choice == "0":
            break
        else:
            print(t("msg_invalid_choice"))
        
        input(t("msg_press_enter"))
        clear_screen()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye!")
