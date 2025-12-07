import os

def check_encoding(directory):
    print(f"Checking files in {directory}...")
    gb18030_files = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    f.read()
            except UnicodeDecodeError:
                print(f"Found GB18030/Non-UTF8 file: {filename}")
                gb18030_files.append(filename)
    
    if not gb18030_files:
        print("No GB18030 files found (all are valid UTF-8).")

if __name__ == "__main__":
    check_encoding("/Volumes/Fanxiang/wwm-locale/dich-xong")
