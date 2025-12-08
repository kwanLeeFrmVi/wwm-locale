#!/usr/bin/env python3
"""
Wipe ./dich-xong then copy JSON shards from ./output/words_map/text
into ./dich-xong as p<timestamp>_<fileID>.json (fileID from entry_XXXXX).
"""

import re
import shutil
import time
from pathlib import Path


def main():
    src = Path("./output/words_map/text")
    dst = Path("./dich-xong")

    if not src.exists():
        raise SystemExit(f"Source missing: {src}")

    dst.mkdir(exist_ok=True)

    # Remove existing json files
    for f in dst.glob("*.json"):
        f.unlink()

    ts = int(time.time())
    pattern = re.compile(r"entry_(\d+)\.json$")

    for f in sorted(src.glob("entry_*.json")):
        m = pattern.search(f.name)
        if not m:
            continue
        file_id = m.group(1)
        target = dst / f"p{ts}_{file_id}.json"
        shutil.copy2(f, target)

    print(f"Copied to {dst} with prefix p{ts}_")


if __name__ == "__main__":
    main()
