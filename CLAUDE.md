# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Where Winds Meet (Yến Vân Thập Lục Thanh) Locale Toolset**

This is a localization toolkit for the game "Where Winds Meet". It combines:
- Rust binary (`wwm_utils`) for unpacking/packing game locale files (words_map format with zstd compression)
- Python scripts for translation workflows using OpenRouter/Gemini API
- Vietnamese translation database in `dich-xong/` directory containing ~8000 translated JSON files

## Running Commands

**Always use `uv` to run Python scripts:**
```bash
# Main interactive tool (recommended entry point)
uv run local_runner.py

# Direct script execution
uv run scripts/trans-local.py <source_dir> <output_dir>
uv run scripts/remove_english_lines.py
uv run scripts/extract-missing-keys.py <entries.json> <dich-xong-folder> <output-folder>
uv run scripts/merge-text.py <base_dir> <patch_dir>
```

**Build Rust tools:**
```bash
cd wwm_utils
cargo build --release
# Binary output: wwm_utils/target/release/wwm_utils
# Or use pre-compiled: bin/yanyun
```

**The yanyun binary:**
- Pre-compiled Rust binary at `bin/yanyun`
- Used by `local_runner.py` for pack/unpack operations
- Equivalent to `wwm_utils` executable
- Auto-made executable by local_runner.py (chmod +x)

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

- **`archive/`**: Store original game files here (translate_words_map_en + translate_words_map_en_diff)
- **`dich-xong/`**: Translated Vietnamese files (production database) - ~8000 JSON files
- **`works/`**: Temporary working directory for unpacking operations
- **`output/`**: Translation output, missing keys extraction
  - **`output/words_map/`**: Merged view created by Option 1 (base + diff combined)
  - **`output/translate_words_map_en`**: Final packed base file (Option 3 output)
  - **`output/translate_words_map_en_diff`**: Final packed diff file (Option 3 output)
- **`missing-keys/`**: Extracted untranslated keys (Option 5 output)
- **`scripts/`**: Python utilities for translation workflow
- **`wwm_utils/`**: Rust source code for pack/unpack binary
- **`bin/`**: Pre-compiled binary (`yanyun`)

### Key Files

- **`local_runner.py`**: Main interactive CLI with bilingual menu (EN/VI)
- **`scripts/trans-local.py`**: Translation engine using OpenRouter API with system prompt
- **`scripts/merge-text.py`**: Merges patched translations into base/diff directories
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

Alternative configuration (DeepSeek):
```bash
OR_API_KEY=<key>
OPENAI_BASE_URL=https://llm.chutes.ai/v1
OPENAI_MODEL=deepseek-ai/DeepSeek-V3.2
```

## Common Workflows

**Full translation pipeline (from game files):**
1. Get files from game: `<GameInstall>/Package/HD/oversea/locale/`
   - `translate_words_map_en` (base map)
   - `translate_words_map_en_diff` (diff/patch map)
2. Place both files in `archive/` folder
3. `uv run local_runner.py` → Option 1 (Unpack Base + Diff)
   - Creates merged view in `output/words_map/text/`
   - Auto-extracts missing keys to `missing_*.json` files
4. `uv run local_runner.py` → Option 4 (Translate text)
   - Translates files to `dich-xong/` folder
5. Manual review/editing of translated files
6. `uv run local_runner.py` → Option 3 (Pack)
   - Outputs to: `output/translate_words_map_en` and `output/translate_words_map_en_diff`
7. Copy output files back to game locale folder

**Extract missing keys (after partial translation):**
```bash
uv run local_runner.py
# Choose option 5 - creates missing-keys/missing_*.json files
# Then use option 4 to translate the missing-keys folder
```

**Remove English residue:**
```bash
uv run scripts/remove_english_lines.py
# Processes all dich-xong/*.json files
```

**Unpack single file (Option 2):**
- Use for unpacking only one words_map file
- Outputs directly to `output/<filename>/`
- Useful for quick inspection or testing

## Important Constraints

**File Naming Convention:**
- JSON chunks use pattern: `p<ID>_<CHUNK>.json` or `t<ID>_<CHUNK>.json`
- Example: `p260311454_00001.json`, `t260252201_00177.json`
- Prefix 'p' and 't' indicate different content types from game
- Missing keys use pattern: `missing_<CHUNK>.json` (e.g., `missing_00001.json`)

**JSON Structure:**
- Each file is a flat dictionary: `{"key": "translated_value"}`
- Keys are internal game identifiers (keep unchanged)
- Values are translated text (Chinese → Vietnamese)

**Pack/Unpack Behavior:**
- Unpacking creates `text/` directory + `entries.json` index file
- Packing expects directory structure with JSON files, outputs to `merged/` subdirectory
- Base + Diff merging: diff values override base values (empty strings in diff are skipped)
- yanyun binary outputs to hardcoded `./output/` directory relative to CWD

**Workspace Management:**
- `works/base/`: Unpacked base map (maintained for Option 3)
- `works/diff/`: Unpacked diff map (if exists, maintained for Option 3)
- `works/` is preserved between Option 1 and Option 3 to enable packing
- Only Option 1 calls `clean_workspace()` to reset state

## Translation Quality Rules

Follow `TRANSLATION_HEURISTICS.md` guidelines:
1. Recognize classical Chinese patterns (虛詞: Chi, Hồ, Giả, Dã...)
2. Reverse adjective-noun order (Chinese → Vietnamese grammar)
3. Preserve martial arts terminology (Giang hồ, Hiệp khách, Nội công)
4. Decode false friends (Du hành = player/wanderer, NOT astronaut)

**Key Translation Concepts:**
- Avoid word-by-word Hán-Việt translation (makes text incomprehensible)
- Use natural Vietnamese phrasing while preserving proper nouns
- Remove all Chinese characters from final output
- Respect context: martial arts, classical literature, game mechanics

## Notes

- The repository contains both English and Vietnamese documentation/UI
- Git status shows ~8000 JSON files in dich-xong/ - this is the working translation database
- macOS-specific files (._*) are present due to APFS extended attributes - scripts ignore them
- No test suite - validation done through game testing
- GitHub Actions workflows available (`.github/workflows/`) for automated pack/unpack
