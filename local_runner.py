#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import zipfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
BIN_YANYUN = "./bin/yanyun"
SCRIPT_MERGE = "./scripts/merge-text.py"
SCRIPT_TRANS = "./scripts/trans-local.py"
WORKS_DIR = "./works"
OUTPUT_DIR = "./output"

# Language Resources
LANG = {
    "en": {
        "menu_title": "=== WWM Locale Tool ===",
        "menu_unpack": "1. Unpack words_map",
        "menu_pack": "2. Pack words_map",
        "menu_translate": "3. Translate text",
        "menu_lang": "4. Switch Language (Tiếng Việt)",
        "menu_exit": "0. Exit",
        "prompt_choice": "Choose an option: ",
        "prompt_words_map": "Enter path or URL to words_map file: ",
        "prompt_patched_zip": "Enter path or URL to patched zip file: ",
        "prompt_source_dir": "Enter source directory (containing .json files): ",
        "prompt_output_dir": "Enter output directory: ",
        "msg_unpacking": "Unpacking...",
        "msg_packing": "Packing...",
        "msg_translating": "Translating...",
        "msg_done": "Done!",
        "msg_error": "Error: {}",
        "msg_file_not_found": "File not found: {}",
        "msg_invalid_choice": "Invalid choice.",
        "msg_press_enter": "Press Enter to continue...",
    },
    "vi": {
        "menu_title": "=== Công cụ Việt hóa WWM ===",
        "menu_unpack": "1. Giải nén words_map",
        "menu_pack": "2. Đóng gói words_map",
        "menu_translate": "3. Dịch văn bản",
        "menu_lang": "4. Đổi ngôn ngữ (English)",
        "menu_exit": "0. Thoát",
        "prompt_choice": "Chọn một tùy chọn: ",
        "prompt_words_map": "Nhập đường dẫn hoặc URL đến file words_map: ",
        "prompt_patched_zip": "Nhập đường dẫn hoặc URL đến file zip đã sửa: ",
        "prompt_source_dir": "Nhập thư mục nguồn (chứa các file .json): ",
        "prompt_output_dir": "Nhập thư mục đầu ra: ",
        "msg_unpacking": "Đang giải nén...",
        "msg_packing": "Đang đóng gói...",
        "msg_translating": "Đang dịch...",
        "msg_done": "Hoàn tất!",
        "msg_error": "Lỗi: {}",
        "msg_file_not_found": "Không tìm thấy file: {}",
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
        subprocess.run(command, shell=shell, check=True)
    except subprocess.CalledProcessError as e:
        print(t("msg_error").format(e))
        return False
    return True

def download_file(url, dest):
    # Simple curl wrapper
    cmd = ["curl", "-L", url, "-o", dest]
    return run_command(cmd)

def prepare_workspace():
    os.makedirs(WORKS_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_workspace():
    if os.path.exists(WORKS_DIR):
        shutil.rmtree(WORKS_DIR)
    prepare_workspace()

def task_unpack():
    clean_workspace()
    words_map_input = input(t("prompt_words_map")).strip()
    
    local_words_map = os.path.join(WORKS_DIR, "words_map")
    
    if words_map_input.startswith("http"):
        print("Downloading...")
        if not download_file(words_map_input, local_words_map):
            return
    else:
        # Remove quotes if present
        words_map_input = words_map_input.strip("'\"")
        if not os.path.exists(words_map_input):
            print(t("msg_file_not_found").format(words_map_input))
            return
        shutil.copy(words_map_input, local_words_map)

    print(t("msg_unpacking"))
    ensure_executable(BIN_YANYUN)
    
    # Run yanyun unpack
    # ./bin/yanyun ./works/words_map
    if not run_command([BIN_YANYUN, local_words_map]):
        return

    # Check output
    output_text_dir = os.path.join(OUTPUT_DIR, "words_map", "text")
    if not os.path.exists(output_text_dir) or not os.listdir(output_text_dir):
        print(t("msg_error").format("No files unpacked"))
        return

    # Zip output
    zip_path = os.path.join(OUTPUT_DIR, "unpacked_words_map.zip")
    print(f"Zipping to {zip_path}...")
    
    # cd ./output/words_map ; zip -r ../unpacked_words_map.zip ./text
    # Python zipfile equivalent
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(os.path.join(OUTPUT_DIR, "words_map")):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.join(OUTPUT_DIR, "words_map"))
                zipf.write(file_path, arcname)
    
    print(t("msg_done"))
    print(f"Output: {zip_path}")

def task_pack():
    clean_workspace()
    
    # Input original words_map
    words_map_input = input(t("prompt_words_map")).strip()
    local_words_map = os.path.join(WORKS_DIR, "words_map")
    
    if words_map_input.startswith("http"):
        if not download_file(words_map_input, local_words_map): return
    else:
        words_map_input = words_map_input.strip("'\"")
        if not os.path.exists(words_map_input):
            print(t("msg_file_not_found").format(words_map_input))
            return
        shutil.copy(words_map_input, local_words_map)

    # Input patched zip
    patched_zip_input = input(t("prompt_patched_zip")).strip()
    local_patched_zip = os.path.join(WORKS_DIR, "patched.zip")
    
    if patched_zip_input.startswith("http"):
        if not download_file(patched_zip_input, local_patched_zip): return
    else:
        patched_zip_input = patched_zip_input.strip("'\"")
        if not os.path.exists(patched_zip_input):
            print(t("msg_file_not_found").format(patched_zip_input))
            return
        shutil.copy(patched_zip_input, local_patched_zip)

    print(t("msg_packing"))
    ensure_executable(BIN_YANYUN)

    # 1. Unpack original words_map to ./output/words_map
    # Note: yanyun seems to output to ./output/words_map by default based on workflows
    if not run_command([BIN_YANYUN, local_words_map]): return

    # 2. Unzip patched files
    patch_dir = os.path.join(WORKS_DIR, "patch")
    tmp_dir = os.path.join(WORKS_DIR, "tmp")
    os.makedirs(patch_dir, exist_ok=True)
    os.makedirs(tmp_dir, exist_ok=True)
    
    with zipfile.ZipFile(local_patched_zip, 'r') as zip_ref:
        zip_ref.extractall(tmp_dir)
    
    # Handle potential subfolder in zip
    items = os.listdir(tmp_dir)
    if len(items) == 1 and os.path.isdir(os.path.join(tmp_dir, items[0])):
        src = os.path.join(tmp_dir, items[0])
        for item in os.listdir(src):
            shutil.move(os.path.join(src, item), patch_dir)
    else:
        for item in items:
            shutil.move(os.path.join(tmp_dir, item), patch_dir)
            
    shutil.rmtree(tmp_dir)

    # 3. Merge text
    # python3 ./scripts/merge-text.py ./output/words_map ./works/patch
    output_words_map_dir = os.path.join(OUTPUT_DIR, "words_map")
    if not run_command([sys.executable, SCRIPT_MERGE, output_words_map_dir, patch_dir]): return

    # 4. Pack
    # ./bin/yanyun ./output/words_map
    if not run_command([BIN_YANYUN, output_words_map_dir]): return

    # 5. Check result
    merged_file = os.path.join(output_words_map_dir, "merged", "words_map")
    if not os.path.exists(merged_file):
        print(t("msg_error").format("Merged file not found"))
        return

    # 6. Move to output
    final_output = os.path.join(OUTPUT_DIR, "translate_words_map_en")
    shutil.move(merged_file, final_output)
    
    print(t("msg_done"))
    print(f"Output: {final_output}")


def task_translate():
    source_dir = input(t("prompt_source_dir")).strip().strip("'\"")
    if not os.path.exists(source_dir):
        print(t("msg_file_not_found").format(source_dir))
        return

    output_dir = input(t("prompt_output_dir")).strip().strip("'\"")
    if not output_dir:
        output_dir = os.path.join(source_dir, "translated")

    print(t("msg_translating"))
    
    # python scripts/trans-local.py <source> <output>
    cmd = [sys.executable, SCRIPT_TRANS, source_dir, output_dir]
    run_command(cmd)
    
    print(t("msg_done"))


def main():
    global current_lang
    while True:
        print("\n" + t("menu_title"))
        print(t("menu_unpack"))
        print(t("menu_pack"))
        print(t("menu_translate"))
        print(t("menu_lang"))
        print(t("menu_exit"))
        
        choice = input(t("prompt_choice"))
        
        if choice == "1":
            task_unpack()
        elif choice == "2":
            task_pack()
        elif choice == "3":
            task_translate()
        elif choice == "4":
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
