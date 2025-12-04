# Project Overview

This is a helper tool for "Where Winds Meet" locale development. It uses GitHub Actions to automate the process of unpacking, patching, and repacking game asset files (likely for translation). The core logic is handled by a binary named `yanyun` and several Python scripts.

# Key Files

*   `.github/workflows/unpack.yml`: GitHub Action to unpack `words_map` files.
*   `.github/workflows/pack.yml`: GitHub Action to pack `words_map` files.
*   `bin/yanyun`: A binary that seems to be the core tool for packing and unpacking.
*   `scripts/merge-text.py`: A Python script to merge patched text files (in JSON format) with the original text files.
*   `scripts/trans-vi.py`: A Python script to translate text from Chinese to Vietnamese using the OpenRouter API.

# Building and Running

The project is not meant to be built or run locally in a traditional sense. Instead, it's designed to be used through GitHub Actions.

## Unpacking

1.  Go to the "Actions" tab in the GitHub repository.
2.  Select the "Unpack words_map file" workflow.
3.  Provide the URL to the `words_map` file.
4.  Run the workflow. A new release will be created with the unpacked files.

## Packing

1.  Go to the "Actions" tab in the GitHub repository.
2.  Select the "Pack words_map files" workflow.
3.  Provide the URL to the original `words_map` file and the patched zip file.
4.  Run the workflow. A new release will be created with the packed file.

## Translating

1.  Run the `trans-vi.py` script locally.
2.  It requires an OpenRouter API key to be set as an environment variable `OR_API_KEY`.
3.  Usage: `python scripts/trans-vi.py <source_folder> <output_folder>`

# Development Conventions

*   The project relies heavily on GitHub Actions for its main functionality.
*   Python scripts are used for text manipulation and translation.
*   The core logic for packing and unpacking is in the `yanyun` binary.
*   The scripts seem to be written for Python 3.
