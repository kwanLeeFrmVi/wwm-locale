import argparse
import json
import os
import shutil
import time


def read_json_file(filepath):
    encodings = ["utf-8", "gb18030", "gbk", "latin-1"]
    for enc in encodings:
        try:
            with open(filepath, "r", encoding=enc) as f:
                return json.load(f)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue

    with open(filepath, "rb") as f:
        content = f.read().decode("utf-8", errors="replace")
    return json.loads(content)


def iter_json_files(directory):
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json"):
            continue
        if name.startswith("._") or name.startswith("."):
            continue
        yield os.path.join(directory, name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", dest="map_path", default="./han_viet_dich-xong.json")
    parser.add_argument("--dir", dest="target_dir", default="./dich-xong")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    if not os.path.exists(args.map_path):
        raise SystemExit(f"map not found: {args.map_path}")
    if not os.path.isdir(args.target_dir):
        raise SystemExit(f"dir not found: {args.target_dir}")

    overrides = read_json_file(args.map_path)
    if not isinstance(overrides, dict):
        raise SystemExit("map must be a JSON object")

    backup_dir = None
    if not args.no_backup and not args.dry_run:
        ts = int(time.time())
        backup_dir = os.path.join(args.target_dir, f"_backup_{ts}")
        os.makedirs(backup_dir, exist_ok=True)

    total_files = 0
    changed_files = 0
    total_updates = 0

    for path in iter_json_files(args.target_dir):
        total_files += 1

        data = read_json_file(path)
        if not isinstance(data, dict):
            continue

        updates = 0
        for k, new_v in overrides.items():
            if k in data and data[k] != new_v:
                data[k] = new_v
                updates += 1

        if updates == 0:
            continue

        changed_files += 1
        total_updates += updates

        if args.dry_run:
            continue

        if backup_dir is not None:
            shutil.copy2(path, os.path.join(backup_dir, os.path.basename(path)))

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(
        json.dumps(
            {
                "map": args.map_path,
                "dir": args.target_dir,
                "total_files": total_files,
                "changed_files": changed_files,
                "total_updates": total_updates,
                "backup_dir": backup_dir,
                "dry_run": args.dry_run,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
