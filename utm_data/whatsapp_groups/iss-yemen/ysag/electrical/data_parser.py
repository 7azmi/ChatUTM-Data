# data_parser.py
import re
import os
from colorama import Fore, init
from config import MESSAGES_PER_CHUNK

# Initialize colorama
init()


def split_messages(file_content):
    """Split chat content into individual messages using WhatsApp format regex"""
    # Enhanced WhatsApp format pattern
    pattern = r'(?:‎|^)\[\d{1,2}/\d{1,2}/\d{2,4},?\s\d{1,2}:\d{2}:\d{2}\s?(?:[AP]M)?\s?\][^\n]+?:.+?(?=\[\d{1,2}/\d{1,2}/\d{2,4},|\Z)'
    messages = re.findall(pattern, file_content, flags=re.DOTALL | re.MULTILINE)
    return [msg.strip() for msg in messages if msg.strip()]


def chunk_messages(messages):
    """Split messages into chunks of MESSAGES_PER_CHUNK"""
    for i in range(0, len(messages), MESSAGES_PER_CHUNK):
        yield messages[i:i + MESSAGES_PER_CHUNK]


def prepare_media_attachments(chunk, file_path):
    """Identify and prepare image attachments for Gemini API with detailed logging"""
    media_files = []
    base_dir = os.path.dirname(file_path)
    # Supported image extensions (can be expanded as needed)
    IMAGE_EXTENSIONS = {
        '.jpg', '.jpeg',
        '.png', '.webp',
        '.gif', '.bmp',
        '.tiff', '.svg'
    }

    for msg in chunk:
        # Check for attachment markers
        if '<attached:' in msg or '‎<attached:' in msg:
            try:
                # Extract filename
                filename_match = re.search(r'(?:‎)?<attached:\s*([^>]+)>', msg)
                if not filename_match:
                    continue

                filename = filename_match.group(1).strip()
                # Clean filename while preserving Arabic characters
                filename = re.sub(r'[^\w\-\.\s\u0600-\u06FF]', '', filename)
                full_path = os.path.join(base_dir, filename)

                # Check if file exists first
                if not os.path.exists(full_path):
                    print(f"{Fore.YELLOW}Attachment not found: {filename}{Fore.RESET}")
                    continue

                # Get file extension and check if it's an image
                _, ext = os.path.splitext(filename)
                ext = ext.lower()

                if ext in IMAGE_EXTENSIONS:
                    media_files.append(full_path)
                    print(f"{Fore.GREEN}Found image attachment: {filename}{Fore.RESET}")
                else:
                    print(f"{Fore.YELLOW}Skipping non-image ({ext}): {filename}{Fore.RESET}")

            except Exception as e:
                print(
                    f"{Fore.RED}Error processing attachment: {filename if 'filename' in locals() else 'unknown'} - {str(e)}{Fore.RESET}")
                continue

    return media_files


def main():
    """Test the message parsing and attachment detection"""
    file_path = "mediafiles/2025/03.txt"

    try:
        # Read the entire file to catch attachments
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()

        # Get first 30 lines for display
        with open(file_path, 'r', encoding='utf-8') as file:
            first_30_lines = ''.join([next(file) for _ in range(30)])

        print(f"{Fore.GREEN}Read WhatsApp chat file{Fore.RESET}")

        print(f"{Fore.CYAN}\n=== First 30 Lines ==={Fore.RESET}")
        print(first_30_lines)

        print(f"{Fore.GREEN}\nTesting message splitting...{Fore.RESET}")
        messages = split_messages(file_content)
        print(f"Found {len(messages)} messages total")

        # Show first 5 messages
        for i, msg in enumerate(messages[:5], 1):
            print(f"{i}. {msg[:100]}...")

        print(f"\n{Fore.GREEN}Testing chunking...{Fore.RESET}")
        chunks = list(chunk_messages(messages))
        print(f"Created {len(chunks)} chunks with {MESSAGES_PER_CHUNK} messages each")

        print(f"\n{Fore.GREEN}Testing attachment detection...{Fore.RESET}")
        # Check all chunks for attachments
        found_attachments = False
        for i, chunk in enumerate(chunks, 1):
            attachments = prepare_media_attachments(chunk, file_path)
            if attachments:
                print(f"{Fore.GREEN}Chunk {i} attachments:{Fore.RESET} {attachments}")
                found_attachments = True

        if not found_attachments:
            print(f"{Fore.YELLOW}No attachments found in any chunks{Fore.RESET}")

    except FileNotFoundError:
        print(f"{Fore.RED}Error: File not found at {file_path}{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}An error occurred: {e}{Fore.RESET}")


if __name__ == "__main__":
    main()