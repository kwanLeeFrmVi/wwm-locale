#!/usr/bin/env python3
"""
Remove untranslated English dialogue lines from JSON files in dich-xong/

Targets:
1. Lines starting with "But..." in English dialogue
2. Full English sentences in dialogue
3. Mixed English-Vietnamese lines with English dialogue starters
"""

import json
import re
from pathlib import Path

def has_english_dialogue(value: str) -> bool:
    """
    Check if the value contains untranslated English dialogue.

    Returns True if:
    - Starts with "But " followed by English words
    - Contains full English sentences (capitalized English words in sequence)
    - Has English dialogue patterns like "I/you/we/they/he/she" with verbs
    - Contains common English sentence structures
    """
    if not isinstance(value, str):
        return False

    # Quick check: if string has >40% ASCII letters and contains English markers, it's likely English
    ascii_letters = sum(1 for c in value if c.isascii() and c.isalpha())
    total_chars = len([c for c in value if not c.isspace()])

    if total_chars > 20 and ascii_letters / total_chars > 0.6:
        # Check for common English words
        english_markers = [
            r'\b(the|this|that|these|those|you|your|my|his|her|their)\b',
            r'\b(is|are|was|were|been|have|has|had)\b',
            r'\b(will|would|should|could|can|may|might|must)\b',
            r'\b(don\'t|doesn\'t|didn\'t|won\'t|can\'t|isn\'t|aren\'t)\b',
            r'\b(only|just|very|too|enough|people|know|think)\b',
        ]

        marker_count = sum(1 for pattern in english_markers if re.search(pattern, value, re.IGNORECASE))
        if marker_count >= 2:  # If 2+ English markers found
            return True

    # Pattern 1: Starts with "But " (not part of Vietnamese)
    if re.match(r'^But\s+[a-z]', value):
        return True

    # Pattern 2: Starts with other English sentence starters
    if re.match(r'^(Hmph\.|Well,|So,|And\s+|The\s+|You\s+|Your\s+|Wicked\s+)', value):
        return True

    # Pattern 3: Full English sentence patterns
    # Look for sequences of English words with common dialogue markers
    english_sentence_patterns = [
        r'\bBut\s+just\s+this\s+once\b',
        r'\bNo\s+more\s+dangerous\s+stunts\b',
        r'\bIf\s+anything\s+happened\b',
        r'\bthe\s+more\s+[a-z]+\s+the\s+more\b',
        r'\bUntil\s+I\s+saw\s+you\b',
        r'\bI\s+resolved\s+to\b',
        r'\bthe\s+guards\s+at\s+the\b',
        r'\bstill\s+gambling\b',
        r'\bI\s+kicked\s+the\s+habit\b',
        r'\bWanna\s+join\s+us\b',
        r'\bmust\'ve\s+stolen\b',
        r'\bWhat\s+about\s+you\b',
        r'\bshe\s+did\s+lose\b',
        r'don\'t\s+climb\s+that\s+tree',
        r'It\'s\s+too\s+tall',
        r'you\s+won\'t\s+get\s+down',
        # Additional patterns for conversational English
        r'\bYour\s+[a-z]+\'s\s+[a-z]+\s+is\b',  # "Your storybook's plot is"
        r'\bYou\s+think\s+[a-z]+\s+(isn\'t|is|are)\b',  # "You think your fiancé isn't"
        r'\ba\s+bit\s+too\s+cliché\b',
        r'don\'t\s+you\s+think\?',
        r'\bisn\'t\s+good\s+enough\b',
        r'\bfar\s+from\s+as\s+refined\b',
        r'\bPlanner\s+doesn\'t\s+set\b',
        r'\bWicked\s+plays\s+only\s+lead\b',
        r'\bpeople\s+astray\b',
        r'\bDon\'t\s+choose\s+this\s+one\b',
        r'\bdo\s+you\s+know\s+your\b',
        r'\bfiancé\'s\s+current\s+post\b',
        r'Don\'t\s+worry\b',  # "Don't worry" standalone phrase
    ]

    for pattern in english_sentence_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            return True

    # Pattern 4: Check for "Ta/Ngươi hear/see/..." mixed errors
    if re.search(r'\b(Ta|Ngươi|ta|ngươi)\s+(hear|see|know|think|feel)\b', value):
        return True

    return False

def clean_json_file(file_path: Path) -> tuple[int, int]:
    """
    Remove entries with English dialogue from a JSON file.

    Returns: (total_keys, removed_keys)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return 0, 0

        original_count = len(data)
        keys_to_remove = []

        for key, value in data.items():
            if has_english_dialogue(value):
                keys_to_remove.append(key)
                print(f"  Removing from {file_path.name}: {key[:20]}... -> {value[:80]}...")

        # Remove the keys
        for key in keys_to_remove:
            del data[key]

        # Write back if changes were made
        if keys_to_remove:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        return original_count, len(keys_to_remove)

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0, 0

def main():
    dich_xong_dir = Path(__file__).parent.parent / "dich-xong"

    if not dich_xong_dir.exists():
        print(f"Error: Directory not found: {dich_xong_dir}")
        return

    print(f"Scanning {dich_xong_dir} for JSON files with English dialogue...")
    print("=" * 70)

    json_files = sorted(dich_xong_dir.glob("*.json"))
    total_files = 0
    total_keys_removed = 0
    files_modified = []

    for json_file in json_files:
        original_count, removed_count = clean_json_file(json_file)

        if removed_count > 0:
            total_files += 1
            total_keys_removed += removed_count
            files_modified.append((json_file.name, removed_count))

    print("=" * 70)
    print(f"\nSummary:")
    print(f"  Files scanned: {len(json_files)}")
    print(f"  Files modified: {total_files}")
    print(f"  Total keys removed: {total_keys_removed}")

    if files_modified:
        print(f"\nModified files:")
        for filename, count in files_modified:
            print(f"  - {filename}: {count} key(s) removed")

    print("\nDone!")

if __name__ == "__main__":
    main()
