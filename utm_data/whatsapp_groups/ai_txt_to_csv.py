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

MESSAGES_PER_CHUNK = 300  # Number of messages per chunk (Kept your adjusted value)
CHAT_FOLDER = "iss-yemen/ysag/computing/2024/"  # Replace with your folder path
OUTPUT_CSV_FILE = "computing-lecturer-review.csv"
# Removed 'Source File' from headers
CSV_HEADERS = [
    'Name', 'Courses', 'Contact', 'Review Summary',
    'Key Points', 'Context', 'Date', 'Source File'
]

SYSTEM_PROMPT = """
ATTENTION: YOUR PRIMARY DIRECTIVE IS TO EXTRACT LECTURER REVIEWS. FAILURE TO ADHERE TO THE FOLLOWING RULES WILL RESULT IN YOUR OUTPUT BEING DISCARDED.

Identify *all* distinct lecturer reviews within the provided WhatsApp messages.
For *each* identified review that CLEARLY names a lecturer and CONTAINS actual review content,
transform it into RAW markdown text (NO code blocks whatsoever).

Format for EACH review (you MUST include ALL sections, fill with available information):

### Lecturer Information
- **Name**: [Full name - REQUIRED. ABSOLUTELY MUST be present.]
- **Courses**: [If mentioned in the messages. State "N/A" or leave blank if not.]
- **Contact**: [If provided. State "N/A" or leave blank if not.]

### Review Summary
[A concise, combined English summary of the review comments for this specific lecturer within this chunk.]

### Key Points
[Bullet points (-) summarizing specific positive or negative attributes mentioned. Be concise.]

### Context
[Any relevant additional information from surrounding messages or attachments that clarifies the review, e.g., module name, specific incident.]

### Date
[YYYY-MM-DD - Extract this from the timestamp of the message(s) containing the review. MUST be in YYYY-MM-DD format.]

ABSOLUTE RULES (NO EXCEPTIONS):
1. Your ENTIRE output MUST be raw markdown. NEVER use markdown code blocks (```).
2. Each valid review block MUST begin EXACTLY with "### Lecturer Information".
3. You MUST include ALL the section headers (### Lecturer Information, ### Review Summary, ### Key Points, ### Context, ### Date) for EVERY review you output, even if the content under a header is empty.
4. If you CANNOT clearly identify a lecturer's name or the message lacks actual review content, you MUST SKIP THAT REVIEW ENTIRELY. Do NOT output a block for it.
5. Only include information that is EXPLICITLY mentioned in the provided text/images. Do NOT invent information.
6. If multiple comments in the chunk refer to the SAME lecturer, combine them naturally into a SINGLE review block for that lecturer.
7. You MUST preserve the sentiment (positive/negative) and specific details of critical remarks.
8. The 'Date' field MUST contain the date extracted from the message timestamp in YYYY-MM-DD format.
9. If, after reviewing the entire chunk, you find NO valid reviews that meet the criteria (clearly named lecturer + review content), your ENTIRE output MUST be ONLY the single word "NOTHING".

COMPLY OR FACE IMMEDIATE DISCARD.
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

        logging.info(f"Calling Gemini with {len(media_files)} media files using key index {current_key_index-1}")

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

            # Combine system prompt, text, and media
            # Only send media_parts if there are any valid ones
            content_parts = [SYSTEM_PROMPT, chat_text]
            if media_parts:
                 content_parts.extend(media_parts)

            response = model.generate_content(content_parts)
        else:
            # Text-only call
            response = model.generate_content([SYSTEM_PROMPT, chat_text]) # Pass as list for consistency

        # Access text content safely, handling potential errors
        try:
             # Check if response has text attribute and is not empty
             if hasattr(response, 'text') and response.text is not None:
                 return response.text.strip()
             else:
                 logging.warning("API returned a response object with no text content.")
                 # Optionally log the full response object for debugging
                 # logging.debug(f"API response object: {response}")
                 return ""
        except Exception as e:
             logging.error(f"Error accessing API response text: {e}")
             # Optionally log the full response object for debugging
             # logging.debug(f"API response object: {response}")
             return ""


    except Exception as e:
        key_info = f"(Key Index {current_key_index -1})" if api_key else "(No Key Acquired)"
        logging.error(f"{Fore.RED}API Error {key_info}: {e}")
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
    # Determine the media folder path based on the chat file path
    # Assumes media folder is sibling to the chat file's parent directory, named "mediafiles"
    # Example: chat file is in /path/to/computing/2025/chat.txt
    # Media folder is expected to be /path/to/computing/mediafiles/
    chat_dir = os.path.dirname(file_path)         # /path/to/computing/2025
    parent_of_chat_dir = os.path.dirname(chat_dir) # /path/to/computing
    media_dir = os.path.join(parent_of_chat_dir, "mediafiles") # /path/to/computing/mediafiles

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
                # filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename) # Example of more restrictive cleaning if needed

                full_path = os.path.join(media_dir, filename) # Use the corrected media_dir

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
                    # Log skipping other file types
                    if ext not in ['.vcf', '.pdf', '.mp4', '.xlsx', '.doc', '.docx', '.txt', '.webp']: # Added .webp as it might be common sticker type
                         logging.info(f"{Fore.YELLOW}Skipping non-image or unsupported attachment ({ext}): {filename}{Fore.RESET}")


            except Exception as e:
                fname_log = filename if 'filename' in locals() else 'unknown attachment'
                logging.error(f"{Fore.RED}Error processing attachment line: {fname_log} - {str(e)}{Fore.RESET}")
                continue

    return media_files

# --- Markdown Parsing Logic ---

def _parse_single_review_block(markdown_block):
    """Parses a single AI's markdown review block into a dictionary."""
    # Must start with the expected header for a valid block
    if not markdown_block or not markdown_block.strip().startswith("### Lecturer Information"):
        return None # Not a valid single review block format

    data = {header: None for header in CSV_HEADERS} # Use updated headers

    # Split by major sections within this block
    # Use a non-greedy match for the section header pattern
    sections = re.split(r'\n### ', markdown_block.strip())

    # The first section is the Lecturer Information header + content
    # Ensure there's content after the header line
    parts_first = sections[0].split('\n', 1)
    if len(parts_first) < 2 or parts_first[0].strip() != "### Lecturer Information":
         # Malformed first section, skip this block
         # logging.debug(f"Skipping block: Malformed first section. Content start: {markdown_block[:100]}...")
         return None

    header_line = parts_first[0].strip() # Should be "### Lecturer Information"
    content = parts_first[1].strip()

    # Parse bullet points within Lecturer Info
    name_match = re.search(r'-\s*\*\*Name\*\*:\s*(.*)', content, re.IGNORECASE)
    courses_match = re.search(r'-\s*\*\*Courses\*\*:\s*(.*)', content, re.IGNORECASE)
    contact_match = re.search(r'-\s*\*\*Contact\*\*:\s*(.*)', content, re.IGNORECASE)
    if name_match: data['Name'] = name_match.group(1).strip()
    if courses_match: data['Courses'] = courses_match.group(1).strip()
    if contact_match: data['Contact'] = contact_match.group(1).strip()

    # Process subsequent sections
    for section in sections[1:]:
        if not section.strip():
            continue

        # Split each subsequent section into its header and content
        parts = section.split('\n', 1)
        if len(parts) < 2: # Ensure there's both a header and potential content
             continue # Skip malformed sections
        header_line = parts[0].strip() # e.g., "Review Summary"
        content = parts[1].strip() if len(parts) > 1 else ""

        # Match headers exactly from the prompt
        if header_line == "Review Summary":
            data['Review Summary'] = content
        elif header_line == "Key Points":
             # Collect all bullet points (lines starting with * or -), preserving newlines within the cell
             points = re.findall(r'^\s*[-*]\s+(.*)', content, re.MULTILINE)
             data['Key Points'] = "\n".join(p.strip() for p in points) if points else content # Fallback to raw content if no bullets
        elif header_line == "Context":
            data['Context'] = content
        elif header_line == "Date":
             # Basic date format validation
             date_str = content.strip()
             if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                data['Date'] = date_str
             else:
                logging.warning(f"Invalid date format found in review block: '{date_str}'. Expected YYYY-MM-DD.")
                data['Date'] = date_str # Keep the raw value for inspection


    # Final validation: Name is mandatory as per rules
    if not data.get('Name'):
        # This check is crucial for filtering out invalid blocks
        # logging.debug(f"Skipping potential review block due to missing Name field. Block content: {markdown_block[:200]}...") # Optional: for debugging
        return None

    # Source file is NOT added here anymore

    return data


def parse_multiple_markdown_reviews(markdown_text, source_file):
    """Parses the AI's markdown response, extracting multiple review blocks."""
    parsed_reviews = []
    if not markdown_text or markdown_text.strip().upper() == "NOTHING":
        # logging.info("API response explicitly returned 'NOTHING' or was empty.") # Optional: more verbose logging
        return parsed_reviews # Return empty list if no text or explicitly "NOTHING"

    # Split the response text into potential review blocks.
    # Each valid review block should start with "### Lecturer Information".
    # Use a regex lookahead to split *before* the start of the next block, keeping the delimiter in the result.
    # This regex splits on '\n' followed by '### Lecturer Information', but includes the '### Lecturer Information' in the resulting split part.
    # We strip leading/trailing whitespace first.
    text_to_split = markdown_text.strip()

    # Find all starting points of review blocks
    # This regex finds the exact start marker, including the ###
    review_starts = list(re.finditer(r'### Lecturer Information', text_to_split))

    if not review_starts:
        # No review blocks found in the response matching the start marker
        logging.warning(f"{Fore.YELLOW}API response received but no review blocks starting with '### Lecturer Information' were found.{Style.RESET_ALL}")
        # Optionally log the raw response here for debugging
        # logging.debug(f"Raw response that failed multi-parsing: {markdown_text}")
        return parsed_reviews # Return empty list

    # Iterate through the found start points to extract blocks
    for i, start_match in enumerate(review_starts):
        start_index = start_match.start()
        # Find the end index: either the start of the next review block or the end of the text
        end_index = text_to_split.find('### Lecturer Information', start_index + 1)
        if end_index == -1: # If no more review blocks, the current block goes to the end
            end_index = len(text_to_split)

        # Extract the potential review block text
        review_block_text = text_to_split[start_index:end_index].strip()

        # Parse the extracted block - Pass the source_file here for potential logging within _parse_single_review_block
        parsed_review = _parse_single_review_block(review_block_text) # _parse_single_review_block no longer needs source_file

        if parsed_review:
            # Add the Source File here, after successful parsing
            parsed_review['Source File'] = os.path.basename(source_file)
            parsed_reviews.append(parsed_review)
        else:
            # Log if a block that looked like a review start didn't parse correctly (e.g., missing name)
            # This is already handled by _parse_single_review_block's return None,
            # but we could add a specific log here if needed.
            pass

    if not parsed_reviews and review_starts: # If blocks were found but none were valid
         logging.warning(f"{Fore.YELLOW}API response contained {len(review_starts)} potential blocks, but none were successfully parsed as valid reviews (e.g., missing names).{Style.RESET_ALL}")
         # Optionally log the raw response here if *no* reviews were parsed at all
         # logging.debug(f"Raw response that yielded no valid reviews: {markdown_text}")


    return parsed_reviews


# --- File Processing and Main Logic ---

def write_to_csv(data_list, filename):
    """Writes the list of review dictionaries to a CSV file, appending if it exists."""
    if not data_list:
        logging.info("No reviews found to write to CSV.")
        return

    logging.info(f"Writing {len(data_list)} reviews to {filename}...")
    try:
        file_exists = os.path.exists(filename)

        # Use 'a' mode for append
        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)

            # Write header only if the file did not exist before opening in 'a' mode
            if not file_exists:
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

    # No longer need to collect all_parsed_reviews here if appending to file per chunk/file
    # However, the original logic collected all then wrote once at the end.
    # Let's stick to the original logic's structure (collect then write) for simplicity,
    # only changing the *write* mode to append. If you want to write per chunk/file,
    # that's a different modification.
    # Sticking to collect-all-then-write-once-appending:
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

            file_processed_reviews_count = 0 # Track reviews found in this file
            for i, chunk in enumerate(chunk_messages(messages)):
                logging.info(f"  Processing chunk {i + 1}...")
                media_files = prepare_media_attachments(chunk, file_path)
                markdown_response = call_gemini_api('\n'.join(chunk), media_files)

                # Pass the response to the multi-parser
                parsed_reviews_in_chunk = parse_multiple_markdown_reviews(markdown_response, file_path) # source_file needed for adding to dict

                if parsed_reviews_in_chunk:
                    # Add ALL reviews found in this chunk to the main list
                    all_parsed_reviews.extend(parsed_reviews_in_chunk)
                    logging.info(f"{Fore.CYAN}  Chunk {i+1}: Successfully parsed {len(parsed_reviews_in_chunk)} review(s).{Style.RESET_ALL}")
                    file_processed_reviews_count += len(parsed_reviews_in_chunk)
                else:
                     logging.info(f"  Chunk {i+1}: No valid reviews parsed from API response.")


            if file_processed_reviews_count == 0:
                 logging.info(f"{Fore.YELLOW}No lecturer reviews extracted from {file_name}{Style.RESET_ALL}")
            else:
                 logging.info(f"{Fore.GREEN}Finished processing {file_name}. Found {file_processed_reviews_count} total reviews.{Style.RESET_ALL}")


    # After processing all files, write the consolidated CSV (appending mode)
    write_to_csv(all_parsed_reviews, OUTPUT_CSV_FILE)


if __name__ == "__main__":
    logging.info("Starting WhatsApp review processing...")
    process_folder(CHAT_FOLDER)
    logging.info("Processing complete.")