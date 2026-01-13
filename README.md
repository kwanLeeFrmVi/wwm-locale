# Where Winds Meet Locale Tool

The helper tool for [Where Winds Meet](https://wherewindsmeet.com) locale development.

**A comprehensive Vietnamese localization toolkit** combining Rust-based game file manipulation with AI-powered translation workflows.

## Features

- 🔓 **Unpack/Pack**: Extract and repack game locale files (`words_map` format with zstd compression)
- 🤖 **AI Translation**: Automated translation using OpenRouter/Gemini API with context-aware prompts
- 🎯 **Smart Merging**: Handle base + diff file combinations with proper override logic
- 📝 **Missing Key Detection**: Automatically identify and extract untranslated content
- 🌐 **Bilingual UI**: Interactive menu in English and Vietnamese
- 🔄 **Translation Memory**: In-memory deduplication for efficient batch processing

## Quick Start (Local Usage)

### Prerequisites

- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- Python 3.9+
- (Optional) Rust toolchain for rebuilding binaries

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/wwm-locale.git
   cd wwm-locale
   ```

2. **Configure API credentials:**
   ```bash
   cp .env.template .env
   # Edit .env and add your API key
   ```

   Example `.env` configuration:
   ```bash
   OR_API_KEY=sk-or-v1-xxxxxxxx
   OPENAI_BASE_URL=https://openrouter.ai/api/v1
   OPENAI_MODEL=google/gemini-pro-1.5-flash-001
   WORKER_COUNT=5
   ```

3. **Get game files:**
   - Navigate to: `<GameInstall>/Package/HD/oversea/locale/`
   - Copy `translate_words_map_en` and `translate_words_map_en_diff`
   - Place both files in `archive/` folder

### Running the Tool

**Interactive mode (recommended):**
```bash
uv run local_runner.py
```

**Menu options:**
1. **Unpack words_map (Base + Diff)** - Extract and merge game files
2. **Unpack single file** - Quick extraction of one file
3. **Pack words_map** - Repack translated files for game
4. **Translate text** - AI-powered batch translation
5. **Extract missing keys** - Find untranslated content
6. **Switch Language** - Toggle EN/VI interface

## Complete Workflow

### Step-by-Step Translation Pipeline

1. **Extract game files:**
   ```bash
   uv run local_runner.py
   # Choose: 1. Unpack words_map (Base + Diff)
   # Input: archive/translate_words_map_en
   # Input: archive/translate_words_map_en_diff
   ```
   - Creates merged view in `output/words_map/text/`
   - Auto-extracts missing keys to `missing_*.json`

2. **Translate content:**
   ```bash
   # Choose: 4. Translate text
   # Source: output/words_map/text/ (default)
   # Output: ./dich-xong (default)
   ```
   - Translates Chinese → Vietnamese
   - Uses translation memory for duplicates
   - Processes ~8000 JSON files concurrently

3. **Review and edit:**
   - Check `dich-xong/` folder for translations
   - Manual review for quality assurance
   - Follow `TRANSLATION_HEURISTICS.md` guidelines

4. **Pack for game:**
   ```bash
   # Choose: 3. Pack words_map
   # Patch source: ./dich-xong (default)
   ```
   - Outputs: `output/translate_words_map_en`
   - Outputs: `output/translate_words_map_en_diff`

5. **Install to game:**
   ```bash
   cp output/translate_words_map_en "<GameInstall>/Package/HD/oversea/locale/"
   cp output/translate_words_map_en_diff "<GameInstall>/Package/HD/oversea/locale/"
   ```

## Advanced Usage

### Direct Script Execution

```bash
# Translate specific directory
uv run scripts/trans-local.py <source_dir> <output_dir>

# Remove English residue
uv run scripts/remove_english_lines.py

# Extract missing keys
uv run scripts/extract-missing-keys.py <entries.json> <dich-xong> <output-folder>

# Merge translations
uv run scripts/merge-text.py <base_dir> <patch_dir>
```

### Rebuild Rust Binary

```bash
cd wwm_utils
cargo build --release
# Binary: wwm_utils/target/release/wwm_utils
# Copy to: bin/yanyun
```

## GitHub Actions (Cloud Workflow)

For automated processing without local setup:

1. **Fork this repository**
2. **Visit Actions page**
   
   <img width="515" height="297" alt="Screenshot 2025-11-26 at 15 09 43" src="https://github.com/user-attachments/assets/072f730c-96be-4d18-882d-2c13b8d8b11d" />

3. **Pick workflow you need**, after run success open Release page
   
   <img width="383" height="441" alt="Screenshot 2025-11-26 at 15 09 59" src="https://github.com/user-attachments/assets/aa4249e0-d8f7-494f-91e0-0bc0137ac96f" />
   <img width="771" height="697" alt="Screenshot 2025-11-26 at 15 15 27" src="https://github.com/user-attachments/assets/63c8371f-2608-4950-a186-452e447730d4" />
   
   <img width="867" height="602" alt="Screenshot 2025-11-26 at 15 16 25" src="https://github.com/user-attachments/assets/c8f04543-a393-4d1e-b8a9-ab19eff3dd73" />

### Workflow Requirements

**For unpack:**
- Require direct URL for download words_map file (no diff)

**For re-pack:**
- Require direct URL for download words_map file (no diff)
- Zip changed (patched) text same unpack folder (e.g., `00001.json` in `text` folder)

## Project Structure

```
wwm-locale/
├── archive/              # Original game files (base + diff)
├── bin/                  # Pre-compiled yanyun binary
├── dich-xong/           # Vietnamese translations (~8000 JSON files)
├── missing-keys/        # Extracted untranslated keys
├── output/              # Processed files and final packed results
├── scripts/             # Python translation utilities
├── works/               # Temporary workspace for pack/unpack
├── wwm_utils/           # Rust source for pack/unpack binary
├── local_runner.py      # Interactive CLI (main entry point)
└── TRANSLATION_HEURISTICS.md  # Vietnamese translation guidelines
```

## Translation Quality

This project uses specialized translation rules for martial arts context:

- ✅ Natural Vietnamese (not word-by-word Hán-Việt)
- ✅ Preserve proper nouns (names, places, techniques)
- ✅ Reverse adjective-noun order (Chinese → Vietnamese grammar)
- ✅ Context-aware martial arts terminology
- ❌ No Chinese characters in final output

See [TRANSLATION_HEURISTICS.md](TRANSLATION_HEURISTICS.md) for detailed guidelines.

## Troubleshooting

**Missing API key error:**
- Ensure `.env` file exists with valid `OR_API_KEY`

**yanyun binary permission denied:**
- Script auto-fixes with `chmod +x`, but you can manually run: `chmod +x bin/yanyun`

**JSON encoding errors:**
- Scripts use multiple encoding fallbacks (utf-8, gb18030, gbk, latin-1)

**Empty diff file warning:**
- Some games ship with 1KB placeholder `_diff` files - this is normal

## Credits

- Base tool by [dest1yo](https://github.com/dest1yo)
- More information from ResHax@`wq223`
- Vietnamese localization workflow design
- Translation rules based on classical Chinese linguistics

## License

See repository license for details.
