#!/usr/bin/env python3
"""Validate translated files contain all keys from entry files. Translate missing keys via LLM."""

import os
import sys
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# LLM config
auth_api_key = os.getenv("OR_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
openai_model = os.getenv("OPENAI_MODEL", "google/gemini-2.0-flash-001")

def get_system_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "Translate Chinese to Vietnamese. Return JSON only."

def translate_missing_keys(missing_data: dict, max_retries: int = 3) -> dict:
    """Translate missing keys using LLM."""
    if not missing_data:
        return {}
    
    client = OpenAI(base_url=openai_base_url, api_key=auth_api_key)
    system_prompt = get_system_prompt()
    json_str = json.dumps(missing_data, ensure_ascii=False)
    
    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model=openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json_str},
                ],
            )
            
            resp = completion.choices[0].message.content
            cleaned = resp.replace("```json", "").replace("```", "").strip()
            
            if not cleaned.startswith("{"):
                print(f"  ⚠ LLM returned non-JSON, retry {attempt+1}/{max_retries}")
                continue
            
            translated = json.loads(cleaned)
            if len(translated) == len(missing_data):
                return translated
            else:
                print(f"  ⚠ Key count mismatch ({len(translated)}/{len(missing_data)}), retry {attempt+1}/{max_retries}")
        except Exception as e:
            print(f"  ⚠ Error: {e}, retry {attempt+1}/{max_retries}")
    
    # Fallback: return original if translation fails
    print(f"  ✖ Translation failed, keeping original text")
    return missing_data

def find_translated_file(entry_id: str, dich_xong_dir: str) -> str | None:
    """Find translated file for given entry ID."""
    for f in os.listdir(dich_xong_dir):
        if f.endswith(f"_{entry_id}.json"):
            return os.path.join(dich_xong_dir, f)
    return None

def validate_and_update(entry_file: str, translated_file: str, dry_run: bool = False) -> dict:
    """Validate translated file has all keys from entry. Return stats."""
    with open(entry_file, "r", encoding="utf-8") as f:
        entry_data = json.load(f)
    
    with open(translated_file, "r", encoding="utf-8") as f:
        trans_data = json.load(f)
    
    entry_keys = set(entry_data.keys())
    trans_keys = set(trans_data.keys())
    
    missing = entry_keys - trans_keys
    extra = trans_keys - entry_keys
    
    stats = {
        "entry_keys": len(entry_keys),
        "trans_keys": len(trans_keys),
        "missing": len(missing),
        "extra": len(extra),
        "updated": False
    }
    
    if missing:
        # Build dict of missing keys to translate
        missing_data = {k: entry_data[k] for k in missing}
        
        if not dry_run:
            print(f"  → Translating {len(missing)} missing keys...")
            translated_missing = translate_missing_keys(missing_data)
            
            # Add translated keys to trans_data
            for key in missing:
                trans_data[key] = translated_missing.get(key, entry_data[key])
            
            with open(translated_file, "w", encoding="utf-8") as f:
                json.dump(trans_data, f, ensure_ascii=False, indent=2)
            stats["updated"] = True
    
    return stats, missing, extra

def main():
    if len(sys.argv) < 3:
        print("Usage: python validate-translations.py <entry_dir> <dich_xong_dir> [--dry-run]")
        print("  --dry-run: Only report, don't update files")
        sys.exit(1)
    
    entry_dir = sys.argv[1]
    dich_xong_dir = sys.argv[2]
    dry_run = "--dry-run" in sys.argv
    
    if not os.path.isdir(entry_dir):
        print(f"Error: Entry dir not found: {entry_dir}")
        sys.exit(1)
    
    if not os.path.isdir(dich_xong_dir):
        print(f"Error: Dich-xong dir not found: {dich_xong_dir}")
        sys.exit(1)
    
    # Find all entry files
    entry_files = sorted([f for f in os.listdir(entry_dir) if f.startswith("entry_") and f.endswith(".json")])
    
    total = len(entry_files)
    issues = 0
    updated = 0
    not_found = 0
    
    print(f"Validating {total} entry files...")
    if dry_run:
        print("(DRY RUN - no files will be modified)")
    print()
    
    for entry_file in entry_files:
        # Extract ID: entry_00638.json -> 00638
        match = re.match(r"entry_(\d+)\.json", entry_file)
        if not match:
            continue
        
        entry_id = match.group(1)
        entry_path = os.path.join(entry_dir, entry_file)
        trans_path = find_translated_file(entry_id, dich_xong_dir)
        
        if not trans_path:
            print(f"⚠ {entry_file}: No translated file found")
            not_found += 1
            continue
        
        stats, missing, extra = validate_and_update(entry_path, trans_path, dry_run)
        
        if stats["missing"] > 0 or stats["extra"] > 0:
            issues += 1
            trans_name = os.path.basename(trans_path)
            print(f"✖ {entry_file} -> {trans_name}")
            print(f"  Entry: {stats['entry_keys']} keys, Trans: {stats['trans_keys']} keys")
            if stats["missing"] > 0:
                print(f"  Missing: {stats['missing']} keys")
                if stats["missing"] <= 5:
                    for k in missing:
                        print(f"    - {k}")
            if stats["extra"] > 0:
                print(f"  Extra: {stats['extra']} keys")
            if stats["updated"]:
                print(f"  ✔ Updated!")
                updated += 1
            print()
    
    print("=" * 50)
    print(f"Total: {total}, Issues: {issues}, Not found: {not_found}, Updated: {updated}")

if __name__ == "__main__":
    main()
