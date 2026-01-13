# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Where Winds Meet (Yến Vân Thập Lục Thanh) Locale Toolset**

This is a localization toolkit for the game "Where Winds Meet". It combines:
- Rust binary (`wwm_utils`) for unpacking/packing game locale files (words_map format with zstd compression)
- Python scripts for translation workflows using OpenRouter/Gemini API
- Vietnamese translation database in `dich-xong/` directory containing thousands of translated JSON files

## Running Commands

**Always use `uv` to run Python scripts:**
```bash
# Main interactive tool
uv run local_runner.py

# Direct script execution
uv run scripts/trans-local.py
uv run scripts/remove_english_lines.py
```

**Build Rust tools:**
```bash
cd wwm_utils
cargo build --release
# Binary output: wwm_utils/target/release/wwm_utils
```

**The yanyun binary:**
- Pre-compiled Rust binary at `bin/yanyun`
- Used by `local_runner.py` for pack/unpack operations
- Equivalent to `wwm_utils` executable

## Architecture

### Dual-Language System (Rust + Python)

**Rust (`wwm_utils/`):**
- Core binary for game file manipulation
- Unpacks: `words_map` files → JSON files in `text/` directory + `entries.json` index
- Packs: Modified JSON files → new `words_map` file in `merged/` subdirectory
- Uses zstd compression, porter-lib for game format parsing
- Entry point: `src/main.rs` - simple CLI that detects file vs directory
- Core logic: `src/core.rs` - `unpack_map()` and `pack_map()` functions

**Python (scripts/):**
- Translation automation using OpenRouter/Gemini API
- File processing, merging, validation utilities
- Interactive menu system in `local_runner.py`
- Key dependencies: openai, halo (spinners), python-dotenv, pydantic

### Data Flow

```
Game files (words_map)
  ↓ [Rust unpack]
JSON chunks (text/00001.json, 00002.json, ...) + entries.json
  ↓ [Python translate]
Translated JSON (dich-xong/*.json)
  ↓ [Rust pack]
Modified words_map → merged/
```

### Directory Structure

- **`dich-xong/`**: Translated Vietnamese files (production database) - ~2000+ JSON files
- **`works/`**: Temporary working directory for unpacking operations
- **`output/`**: Translation output, missing keys extraction
- **`scripts/`**: Python utilities for translation workflow
- **`wwm_utils/`**: Rust source code for pack/unpack binary
- **`bin/`**: Pre-compiled binary (`yanyun`)

### Key Files

- **`local_runner.py`**: Main interactive CLI with bilingual menu (EN/VI)
- **`scripts/trans-local.py`**: Translation engine using OpenRouter API with system prompt
- **`scripts/remove_english_lines.py`**: Cleans English content from JSON files (>50% Latin chars)
- **`scripts/extract-missing-keys.py`**: Extracts untranslated keys from entries.json
- **`TRANSLATION_HEURISTICS.md`**: Vietnamese translation rules for Classical Chinese (Hán Việt) in martial arts context

## Translation System Specifics

**System Prompt Location:**
- `scripts/system_prompt.txt` (if exists, used by trans-local.py)
- Fallback prompt embedded in trans-local.py focuses on:
  - Natural Vietnamese (not word-by-word Hán-Việt)
  - Preserve proper nouns (names, places, martial arts techniques)
  - Remove all Chinese characters
  - Return valid JSON only

**Translation Memory:**
- Global translation map in-memory during script execution
- Reuses translations for duplicate strings
- Concurrent translation with worker pool (default: 5 workers, configurable via `WORKER_COUNT` env)

**Environment Variables (.env):**
```bash
OR_API_KEY=<your-openrouter-api-key>
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=google/gemini-pro-1.5-flash-001
WORKER_COUNT=5
```

## Common Workflows

**Full translation pipeline:**
1. Download words_map file from game
2. `uv run local_runner.py` → Option 1 (Unpack)
3. `uv run local_runner.py` → Option 4 (Translate)
4. Manual review/editing of translated files
5. `uv run local_runner.py` → Option 3 (Pack)

**Extract missing keys:**
```bash
uv run local_runner.py
# Choose option 5 - creates missing_*.json files
```

**Remove English residue:**
```bash
uv run scripts/remove_english_lines.py
# Processes all dich-xong/*.json files
```

## Important Constraints

**File Naming Convention:**
- JSON chunks use pattern: `p<ID>_<CHUNK>.json` or `t<ID>_<CHUNK>.json`
- Example: `p260311454_00001.json`, `t260252201_00177.json`
- Prefix 'p' and 't' indicate different content types from game

**JSON Structure:**
- Each file is a flat dictionary: `{"key": "translated_value"}`
- Keys are internal game identifiers (keep unchanged)
- Values are translated text (Chinese → Vietnamese)

**Pack/Unpack Behavior:**
- Unpacking creates `text/` directory + `entries.json` index file
- Packing expects directory structure with JSON files, outputs to `merged/` subdirectory
- Some maps have valid `_diff` patch files - tool cannot merge them yet (edit base maps only)

## Translation Quality Rules

Follow `TRANSLATION_HEURISTICS.md` guidelines:
1. Recognize classical Chinese patterns (虛詞: Chi, Hồ, Giả, Dã...)
2. Reverse adjective-noun order (Chinese → Vietnamese grammar)
3. Preserve martial arts terminology (Giang hồ, Hiệp khách, Nội công)
4. Decode false friends (Du hành = player/wanderer, NOT astronaut)

## Notes

- The repository contains both English and Vietnamese documentation/UI
- Git status shows ~1400+ modified JSON files in dich-xong/ - this is the working translation database
- macOS-specific files (._*) are present due to APFS extended attributes - ignore them
- No test suite - validation done through game testing
