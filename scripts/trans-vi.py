# Description: Script to translate text from file using OpenRouter with streaming

import os
import re
import sys
from datetime import datetime

from halo import Halo
from openai import OpenAI

system_description = """You are a translator of the game Where Winds Meets. You master Chinese and Vietnamese languages.
Translate the following Chinese text to Vietnamese accurately, not missing any Chinese word, maintaining the game's tone and context.
Just response as json, do not add any extra explanation like ```
"""

# Read OS env for api key. The key in ENV is: OR_API_KEY
auth_api_key = os.getenv("OR_API_KEY", "sk-or-...")


def replace_filename_pattern(filename, out_prefix):
    pattern = r"^(.+?)_(\d+)\.json$"
    match = re.match(pattern, filename)

    if match:
        number = match.group(2)
        return f"p{out_prefix}_{number}.json"

    return filename


def translate_text(spinner, input_file, output_file):
    # current started time
    started_at = os.times()

    # Path to output file (assuming same directory as input, with 'translated_' prefix)
    output_file = output_file or os.path.join(
        os.path.dirname(input_file), "translated_" + os.path.basename(input_file)
    )

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Input file {input_file} does not exist.")
        return

    # Read content from input file
    with open(input_file, "r", encoding="utf-8") as f:
        content_to_translate = f.read().strip()

    if not content_to_translate:
        print("Input file is empty.")
        return

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Initialize OpenAI client for OpenRouter
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=auth_api_key,
    )

    try:
        # Create chat completion with streaming
        completion = client.chat.completions.create(
            extra_headers={
                "X-Title": "WWM Locale Tool",  # Optional. Site title for rankings on openrouter.ai.
            },
            model="google/gemini-2.5-flash-lite-preview-09-2025",  # "google/gemini-2.0-flash-001",
            messages=[
                {
                    "role": "system",
                    "content": system_description,
                },
                {"role": "user", "content": content_to_translate},
            ],
            stream=True,  # Enable streaming
        )
    except Exception as e:
        spinner.fail(f"Network error: {e}")
        return -1

    translated_text = ""
    try:
        for chunk in completion:
            if chunk.choices[0].delta.content:
                resp_content = chunk.choices[0].delta.content

                translated_text += resp_content
                spinner.text = " > {}...".format(
                    resp_content.replace("\n", "").strip()[:35]
                )
    except Exception as e:
        spinner.fail(f"Streaming error: {e}")
        return -1

    processed_at = os.times()

    # Write the full translated text to output file
    with open(output_file, "w", encoding="utf-8") as f:
        # remove leading and trailing ```
        translated_text = translated_text.strip()
        i1 = translated_text.find("{")
        i2 = translated_text.rfind("}")
        if i1 != -1 and i2 != -1:
            translated_text = translated_text[i1 : i2 + 1]

        f.write(translated_text)

    return processed_at[4] - started_at[4]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python trans-miss.py <source folder> <output folder>")
        sys.exit(1)

    missing_folder = sys.argv[1]
    output_folder = sys.argv[2]

    # Collect the streamed response
    spinner = Halo(text="Processing", spinner="dots")
    spinner.start()

    # list files in missing folder
    files = os.listdir(missing_folder)

    now = datetime.now()
    run_at = (
        f"{now.strftime('%y')}"  # Year in 2 digits
        f"{now.strftime('%V')}"  # Week of year (ISO)
        f"{now.strftime('%u')}"  # Day of week (1-7)
        f"{now.strftime('%H')}"  # Hour 24h
        f"{now.strftime('%M')}"  # Minute
    )

    for idx, filename in enumerate(files):
        if not filename.endswith(".json"):
            continue

        new_filename = replace_filename_pattern(filename, run_at)

        input_file = os.path.join(missing_folder, filename)

        if new_filename == filename:
            output_file = os.path.join(output_folder, f"t{run_at}_{filename}")
        else:
            output_file = os.path.join(output_folder, new_filename)

        spinner.info(f"[{idx + 1}/{len(files)}] Translating {filename}")
        spinner.start("Waiting for response...")
        processed_time = translate_text(spinner, input_file, output_file)
        msg = f"[{idx + 1}/{len(files)}] Translation completed in {processed_time:.2f} seconds."
        spinner.info(msg)
