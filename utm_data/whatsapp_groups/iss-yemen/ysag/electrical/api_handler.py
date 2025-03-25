# api_handler.py
import google.generativeai as genai
from colorama import Fore
from pathlib import Path
import os
from config import GEMINI_API_KEYS, SYSTEM_PROMPT

# Round-robin API key selection
current_key_index = 0


def get_next_api_key():
    global current_key_index
    api_key = GEMINI_API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(GEMINI_API_KEYS)
    return api_key


def call_gemini_api(chat_text, media_files=[]):
    print(media_files)
    global current_key_index
    try:
        api_key = get_next_api_key()
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel("gemini-2.0-flash")

        if media_files:
            # Prepare media content for multi-modal processing
            media_parts = []
            for media_file in media_files:
                mime_type = f"image/{Path(media_file).suffix[1:]}" if media_file.lower().endswith(
                    ('.jpg', '.jpeg', '.png')) else "application/octet-stream"
                media_parts.append({
                    'mime_type': mime_type,
                    'data': Path(media_file).read_bytes()
                })

            # Combine text and media
            response = model.generate_content(
                [SYSTEM_PROMPT, chat_text] + media_parts
            )
        else:
            response = model.generate_content(SYSTEM_PROMPT + "\n\n" + chat_text)

        return response.text.strip()
    except Exception as e:
        print(Fore.RED + f"API Error (Key {current_key_index + 1}): {e}")
        return ""