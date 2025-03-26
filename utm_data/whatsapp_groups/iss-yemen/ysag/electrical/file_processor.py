# file_processor.py
import os
from colorama import Fore
from data_parser import split_messages, chunk_messages, prepare_media_attachments
from api_handler import call_gemini_api


def process_single_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(Fore.RED + f"Error reading file {file_path}: {e}")
        return

    messages = split_messages(content)
    if not messages:
        print(Fore.YELLOW + f"No valid messages found in {file_path}")
        return

    print(f"Processing {file_path} ({len(messages)} messages)")

    all_reviews = []

    for i, chunk in enumerate(chunk_messages(messages)):
        print(f"  Processing chunk {i + 1}...")
        media_files = prepare_media_attachments(chunk, file_path)
        markdown_response = call_gemini_api('\n'.join(chunk), media_files)

        if not markdown_response or "NOTHING" in markdown_response:
            continue

        # Add separator between chunks if multiple reviews found
        if all_reviews:
            all_reviews.append("\n---\n")
        all_reviews.append(markdown_response.strip())

    if not all_reviews:
        print(Fore.YELLOW + f"No lecturer reviews found in {file_path}")
        return

    # Write final output
    md_file_path = file_path.replace(".txt", ".md")
    try:
        with open(md_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_reviews))
        print(Fore.GREEN + f"Saved reviews to {md_file_path}")
    except Exception as e:
        print(Fore.RED + f"Error writing markdown file: {e}")