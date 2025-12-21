# Continue Working Plan

## Objective

Continue iteratively refining game translation strings by processing unstaged `dich-xong/*.json` files.

## Current Status

- Last processed file: `dich-xong/p1765869931_00247.json` (completed).
- Next file to process: `dich-xong/p1765869931_00248.json`.
- There are multiple pending files (e.g., 00250, 00251, 00252, ...).

## Workflow Steps

1. **Identify next file**: Run `git status --porcelain | grep 'dich-xong/' | head -n 1` to find the next unstaged modified translation file.
2. **Analyze changes**: Run `git diff --no-color -- <filename>` to see the changed keys and values.
3. **Update overrides**:
   - Check `han_viet_dich-xong.json` for existing keys.
   - If a key is missing, add a refined "Kiếm Hiệp" style Vietnamese translation override.
   - Ensure proper JSON formatting (escaped newlines `\n`, trailing commas).
4. **Stage files**: Run `git add <filename> han_viet_dich-xong.json`.
5. **Repeat**: Loop until no unstaged `dich-xong/*.json` files remain.

## Notes

- Maintain the "Kiếm Hiệp" tone.
- Be careful with JSON syntax (commas).
- `han_viet_dich-xong.json` must always be valid JSON.
