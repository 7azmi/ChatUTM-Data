# combined_processor.py
import os
import re
import csv
import google.generativeai as genai
from colorama import Fore, Style, init
from pathlib import Path
from dotenv import load_dotenv
import logging

# Initialize colorama and logging
init(autoreset=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
load_dotenv()

# Load multiple Gemini API keys
GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5"),
    os.getenv("GEMINI_API_KEY_6"),
]
# Filter out any None values
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

MESSAGES_PER_CHUNK = 400  # Number of messages per chunk
CHAT_FOLDER = "iss-yemen/ysag/computing/2025/"  # Replace with your folder path
OUTPUT_CSV_FILE = "computing-lecturer-review.csv"
CSV_HEADERS = [
    'Name', 'Courses', 'Contact', 'Review Summary',
    'Key Points', 'Context', 'Date',
]

SYSTEM_PROMPT = """
STRICTLY transform WhatsApp lecturer reviews into RAW markdown text (no code blocks). ONLY output if:
1. Lecturer name is clearly identified
2. Contains actual review content

Format (include ONLY available information):

### Lecturer Information
- **Name**: [Full name - REQUIRED]
- **Courses**: [If mentioned]
- **Contact**: [If provided]

### Review Summary
[Combined English summary]

### Key Points
[Bullet points of mentioned attributes]

### Context
[Relevant info from attachments]

### Date
[YYYY-MM-DD]

RULES:
1. NEVER use markdown code blocks (```)
2. Output must begin directly with ###
3. Include ALL sections with available info
4. Skip ENTIRE review if name is missing
5. Only use actual mentioned information
6. Combine duplicate comments naturally
7. Preserve critical negative/positive remarks
8. Date must be from message metadata
"""

# Supported image extensions
IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg',
    '.png', '.webp',
    '.gif', '.bmp',
    '.tiff', '.svg'
}

# Round-robin API key selection
current_key_index = 0

# --- API Handler Logic ---

def get_next_api_key():
    """Gets the next API key in a round-robin fashion."""
    global current_key_index
    if not GEMINI_API_KEYS:
        raise ValueError("No Gemini API keys configured.")
    api_key = GEMINI_API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(GEMINI_API_KEYS)
    return api_key

def call_gemini_api(chat_text, media_files=[]):
    """Calls the Gemini API with text and optional media."""
    global current_key_index
    api_key = None
    try:
        api_key = get_next_api_key()
        genai.configure(api_key=api_key)
        # Use a model that supports multimodal input if media is present
        model_name = "gemini-2.5-flash-preview-04-17" # Or gemini-pro-vision if needed, check availability and pricing
        model = genai.GenerativeModel(model_name)

        logging.info(f"Calling Gemini with {len(media_files)} media files using key index {current_key_index-1}") # Log key index used
        # print(f"DEBUG: Media files being sent: {media_files}") # DEBUG

        if media_files:
            media_parts = []
            for media_file in media_files:
                try:
                    p = Path(media_file)
                    if not p.exists():
                         logging.warning(f"Media file not found, skipping: {media_file}")
                         continue
                    # Basic MIME type detection based on extension
                    suffix = p.suffix.lower()
                    if suffix in ['.jpg', '.jpeg']:
                        mime_type = 'image/jpeg'
                    elif suffix == '.png':
                        mime_type = 'image/png'
                    elif suffix == '.webp':
                         mime_type = 'image/webp'
                    elif suffix == '.gif':
                         mime_type = 'image/gif'
                    elif suffix == '.bmp':
                         mime_type = 'image/bmp'
                    else:
                         # Fallback or skip unsupported types
                         logging.warning(f"Unsupported image type {suffix} for file {media_file}, skipping.")
                         continue

                    media_parts.append({'mime_type': mime_type, 'data': p.read_bytes()})
                except Exception as e:
                    logging.error(f"Error reading media file {media_file}: {e}")
                    continue # Skip this file

            if not media_parts: # If all media failed or were skipped
                 logging.warning("No valid media parts to send, calling API with text only.")
                 response = model.generate_content([SYSTEM_PROMPT, chat_text])
            else:
                 # Combine system prompt, text, and media
                 response = model.generate_content([SYSTEM_PROMPT, chat_text] + media_parts)
        else:
            # Text-only call
            response = model.generate_content([SYSTEM_PROMPT, chat_text]) # Pass as list for consistency

        return response.text.strip()

    except Exception as e:
        key_info = f"(Key Index {current_key_index -1})" if api_key else "(No Key Acquired)"
        logging.error(f"{Fore.RED}API Error {key_info}: {e}")
        # print(f"DEBUG: Error occurred with key index {current_key_index - 1}") # DEBUG
        # Potentially retry logic or specific error handling could go here
        return "" # Return empty string on failure

# --- Data Parser Logic ---

def split_messages(file_content):
    """Split chat content into individual messages using WhatsApp format regex"""
    # Pattern accounts for optional AM/PM and potential missing seconds/space variations
    # Matches [date, time] user: message format, including multiline messages.
    # Uses lookahead `(?=...)` to avoid consuming the start of the next message.
    # Handles potential invisible characters like ‎ (U+200E LEFT-TO-RIGHT MARK) often found in exports
    pattern = r'(?:[\u200E\u200F]?\[\d{1,2}/\d{1,2}/\d{2,4},?\s\d{1,2}:\d{2}(?::\d{2})?\s?[AP]?M?\]\s.*?:\s.*?(?=\n?[\u200E\u200F]?\[\d{1,2}/\d{1,2}/\d{2,4},?\s\d{1,2}:\d{2}|\Z))'
    messages = re.findall(pattern, file_content, flags=re.DOTALL | re.MULTILINE)
    cleaned_messages = [msg.strip() for msg in messages if msg.strip()]
    logging.info(f"Split content into {len(cleaned_messages)} messages.")
    return cleaned_messages


def chunk_messages(messages):
    """Split messages into chunks"""
    for i in range(0, len(messages), MESSAGES_PER_CHUNK):
        yield messages[i:i + MESSAGES_PER_CHUNK]

def prepare_media_attachments(chunk, file_path):
    """Identify and prepare *image* attachments for Gemini API."""
    media_files = []
    base_dir = os.path.dirname(file_path)

    for msg in chunk:
        # Check for attachment markers (including the invisible char)
        if '<attached:' in msg or '\u200e<attached:' in msg:
            try:
                # Extract filename: handle potential whitespace variations and invisible chars
                filename_match = re.search(r'[\u200e]?<attached:\s*([^>]+)>', msg)
                if not filename_match:
                    logging.warning(f"Could not extract filename from attachment marker in message: {msg[:50]}...")
                    continue

                filename = filename_match.group(1).strip()
                # Basic cleaning - remove potentially problematic chars BUT keep unicode letters/numbers/spaces/dots/hyphens
                # This is a safer approach than removing *all* non-alphanumeric
                # filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename) # Example of more restrictive cleaning if needed

                full_path = os.path.join(base_dir, filename)

                if not os.path.exists(full_path):
                    logging.warning(f"{Fore.YELLOW}Attachment not found: {filename} (looked in {full_path}){Fore.RESET}")
                    continue

                # Get file extension and check if it's a supported image
                _, ext = os.path.splitext(filename)
                ext = ext.lower()

                if ext in IMAGE_EXTENSIONS:
                    media_files.append(full_path)
                    logging.info(f"{Fore.GREEN}Found image attachment: {filename}{Fore.RESET}")
                else:
                    logging.info(f"{Fore.YELLOW}Skipping non-image or unsupported attachment ({ext}): {filename}{Fore.RESET}")

            except Exception as e:
                fname_log = filename if 'filename' in locals() else 'unknown attachment'
                logging.error(f"{Fore.RED}Error processing attachment line: {fname_log} - {str(e)}{Fore.RESET}")
                continue

    return media_files

# --- Markdown Parsing Logic ---

def parse_markdown_review(markdown_text, source_file):
    """Parses the AI's markdown response into a dictionary for CSV."""
    if not markdown_text or not markdown_text.strip().startswith("###"):
        return None # Not a valid review format

    data = {header: None for header in CSV_HEADERS}
    data['Source File'] = os.path.basename(source_file) # Add source file info

    # Split by major sections
    sections = re.split(r'\n### ', markdown_text.strip())
    if not sections[0].startswith('### '): # Handle the first section correctly
         sections[0] = '### ' + sections[0]

    for section in sections:
        if not section.strip():
            continue

        # Ensure we split only once at the first newline to get header vs content
        parts = section.split('\n', 1)
        header_line = parts[0].strip()
        content = parts[1].strip() if len(parts) > 1 else ""

        if header_line.startswith("### Lecturer Information"):
            # Parse bullet points within Lecturer Info
            name_match = re.search(r'-\s*\*\*Name\*\*:\s*(.*)', content, re.IGNORECASE)
            courses_match = re.search(r'-\s*\*\*Courses\*\*:\s*(.*)', content, re.IGNORECASE)
            contact_match = re.search(r'-\s*\*\*Contact\*\*:\s*(.*)', content, re.IGNORECASE)
            if name_match: data['Name'] = name_match.group(1).strip()
            if courses_match: data['Courses'] = courses_match.group(1).strip()
            if contact_match: data['Contact'] = contact_match.group(1).strip()

        elif header_line.startswith("### Review Summary"):
            data['Review Summary'] = content

        elif header_line.startswith("### Key Points"):
             # Collect all bullet points (lines starting with * or -), preserving newlines within the cell
             points = re.findall(r'^\s*[-*]\s+(.*)', content, re.MULTILINE)
             data['Key Points'] = "\n".join(p.strip() for p in points) if points else content # Fallback to raw content if no bullets

        elif header_line.startswith("### Context"):
            data['Context'] = content

        elif header_line.startswith("### Date"):
            data['Date'] = content # Assuming AI provides it correctly formatted

    # Final validation: Name is mandatory as per rules
    if not data.get('Name'):
        logging.warning(f"Skipping review due to missing Name field. Raw content: {markdown_text[:100]}...")
        return None

    return data


# --- File Processing and Main Logic ---

def write_to_csv(data_list, filename):
    """Writes the list of review dictionaries to a CSV file."""
    if not data_list:
        logging.info("No reviews found to write to CSV.")
        return

    logging.info(f"Writing {len(data_list)} reviews to {filename}...")
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
            writer.writeheader()
            writer.writerows(data_list)
        logging.info(f"{Fore.GREEN}Successfully saved consolidated reviews to {filename}{Style.RESET_ALL}")
    except IOError as e:
        logging.error(f"{Fore.RED}Error writing CSV file {filename}: {e}")
    except Exception as e:
        logging.error(f"{Fore.RED}An unexpected error occurred during CSV writing: {e}")


def process_folder(folder_path):
    """Processes all .txt files in a folder and aggregates results into a CSV."""
    if not GEMINI_API_KEYS:
        logging.error(Fore.RED + "No valid Gemini API keys found in environment variables (GEMINI_API_KEY_1, etc.)!")
        exit(1)
    logging.info(f"Found {len(GEMINI_API_KEYS)} API key(s).")

    if not os.path.exists(folder_path):
        logging.error(Fore.RED + f"Folder not found: {folder_path}")
        return

    all_parsed_reviews = [] # Collect all valid reviews here

    for file_name in sorted(os.listdir(folder_path)): # Sort for consistent processing order
        if file_name.endswith(".txt"):
            file_path = os.path.join(folder_path, file_name)
            logging.info(f"\n--- Processing file: {file_path} ---")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                logging.error(Fore.RED + f"Error reading file {file_path}: {e}")
                continue # Skip to next file

            messages = split_messages(content)
            if not messages:
                logging.warning(Fore.YELLOW + f"No valid messages found in {file_path}")
                continue

            logging.info(f"Processing {len(messages)} messages in chunks of {MESSAGES_PER_CHUNK}...")

            file_has_reviews = False
            for i, chunk in enumerate(chunk_messages(messages)):
                logging.info(f"  Processing chunk {i + 1}...")
                media_files = prepare_media_attachments(chunk, file_path) # Pass full file_path for base dir calculation
                markdown_response = call_gemini_api('\n'.join(chunk), media_files)

                if not markdown_response or "NOTHING" in markdown_response.upper(): # Check for explicit ignore signal
                    logging.info(f"  Chunk {i+1}: No review data returned by API or explicit 'NOTHING'.")
                    continue

                # Attempt to parse the markdown response
                parsed_review = parse_markdown_review(markdown_response, file_path)
                if parsed_review:
                    all_parsed_reviews.append(parsed_review)
                    logging.info(f"{Fore.CYAN}  Chunk {i+1}: Successfully parsed review for '{parsed_review.get('Name', 'Unknown')}'{Style.RESET_ALL}")
                    file_has_reviews = True
                else:
                     logging.warning(f"{Fore.YELLOW}  Chunk {i+1}: API response received but failed parsing or missing required fields.{Style.RESET_ALL}")
                     # Optionally log the raw response here for debugging if parsing fails
                     # logging.debug(f"Raw response for failed parse: {markdown_response}")


            if not file_has_reviews:
                 logging.info(f"{Fore.YELLOW}No lecturer reviews extracted from {file_name}{Style.RESET_ALL}")


    # After processing all files, write the consolidated CSV
    write_to_csv(all_parsed_reviews, OUTPUT_CSV_FILE)


if __name__ == "__main__":
    logging.info("Starting WhatsApp review processing...")
    process_folder(CHAT_FOLDER)
    logging.info("Processing complete.")