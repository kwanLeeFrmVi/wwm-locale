# Where Winds Meet Locale tool

The helper tool for [Where Winds Meet](https://wherewindsmeet.com) locale development.

## Usage

1. Fork this repository.
2. Visit Actions page

   <img width="515" height="297" alt="Screenshot 2025-11-26 at 15 09 43" src="https://github.com/user-attachments/assets/072f730c-96be-4d18-882d-2c13b8d8b11d" />

3. Pick workflow you need, after run success open Release page

<img width="383" height="441" alt="Screenshot 2025-11-26 at 15 09 59" src="https://github.com/user-attachments/assets/aa4249e0-d8f7-494f-91e0-0bc0137ac96f" />
<img width="771" height="697" alt="Screenshot 2025-11-26 at 15 15 27" src="https://github.com/user-attachments/assets/63c8371f-2608-4950-a186-452e447730d4" />

<img width="867" height="602" alt="Screenshot 2025-11-26 at 15 16 25" src="https://github.com/user-attachments/assets/c8f04543-a393-4d1e-b8a9-ab19eff3dd73" />

### For unpack

- Require direct url for download words_map file (no diff).

### For re-pack

- Require direct url for download words_map file (no diff).
- Zip changed (patched) text same unpack folder (eg: `00001.json` in `text` folder)

## Local Usage

This tool can now be run locally using `uv` and an interactive terminal script.

### Prerequisites

- [uv](https://github.com/astral-sh/uv) installed.
- Python 3.9+.

### Setup

1. Clone the repository.
2. Copy `.env.template` to `.env` and fill in your API keys:

   ```bash
   cp .env.template .env
   # Edit .env with your OR_API_KEY and OPENAI_BASE_URL
   # Optionally set OPENAI_MODEL (default: google/gemini-pro-1.5-flash-001)
   # Optionally set WORKER_COUNT (default: 5)
   ```

### Running

Run the interactive tool:

```bash
uv run local_runner.py
```

Follow the on-screen menu to:

- **Unpack**: Extract `words_map` files.
- **Pack**: Repack patched text into `words_map`.
- **Translate**: Auto-translate text using AI.
- **Switch Language**: Toggle between English and Vietnamese interface.

## Credits

- Base tool by [dest1yo](https://github.com/dest1yo)
- More information from ResHax@`wq223`
