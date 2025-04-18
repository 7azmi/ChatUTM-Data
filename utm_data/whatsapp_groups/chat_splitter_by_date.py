import pathlib
import re
from datetime import datetime
from collections import defaultdict
import os
import shutil
import sys # Import sys to handle potential encoding errors

# --- Configuration ---
# Update this path to the location of your chat file
# Make sure the media files you want to move are in the SAME directory
input_file_path = 'iss-yemen/ysag/computing/_chat.txt'
# ---------------------
# Regex for extracting date/time for different formats
# iOS format: [DD/MM/YYYY, HH:MM:SS AM/PM]
ios_date_pattern = re.compile(r'^\[(\d{2})/(\d{2})/(\d{4}), (\d{1,2}):(\d{2}):(\d{2})\s*([APap][Mm])\]')
# Android format: DD/MM/YY, HH:MM AM/PM -or- DD/MM/YYYY, HH:MM AM/PM
android_date_pattern_yy = re.compile(r'^(\d{1,2}/\d{1,2}/\d{2}), (\d{1,2}:\d{2})\s*([APap][Mm])')
android_date_pattern_yyyy = re.compile(r'^(\d{1,2}/\d{1,2}/\d{4}), (\d{1,2}:\d{2})\s*([APap][Mm])')

# Regex for extracting date from media/file names (e.g., 00001234-PHOTO-YYYY-MM-DD-HH-MM-SS.jpg)
# This looks for -YYYY-MM-DD within the filename
media_date_pattern = re.compile(r'-(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})')

# Function to extract the date from a chat line
def extract_date_and_month(line):
    """
    Attempts to extract the date and determine the YYYY-MM string from a chat line.
    Tries iOS format first, then Android (YY or YYYY).
    Returns (datetime_object, 'YYYY-MM_string') if successful, otherwise (None, None).
    """
    # Try iOS format
    match = ios_date_pattern.match(line)
    if match:
        try:
            # Note: iOS seconds are present, but we only need date for month/year splitting
            dt_str = f"{match.group(1)}/{match.group(2)}/{match.group(3)}"
            date_obj = datetime.strptime(dt_str, "%d/%m/%Y")
            return (date_obj, date_obj.strftime('%Y-%m'))
        except ValueError:
            print(f"Warning: Invalid iOS date format in line: {line.strip()}", file=sys.stderr)
            return (None, None)

    # Try Android format (YYYY)
    match = android_date_pattern_yyyy.match(line)
    if match:
        try:
            dt_str = match.group(1)
            date_obj = datetime.strptime(dt_str, '%d/%m/%Y')
            return (date_obj, date_obj.strftime('%Y-%m'))
        except ValueError:
             # If YYYY fails, maybe it's YY? This could happen if the regex isn't perfect.
             # Let's let the YY pattern handle it next.
            pass # Don't print warning yet, might match YY

    # Try Android format (YY) - Only if YYYY didn't match or failed
    match = android_date_pattern_yy.match(line)
    if match:
        try:
            dt_str = match.group(1)
            # Use a modern approach that handles 2-digit years relative to the current century
            # default is often years 69-99 -> 19xx, years 00-68 -> 20xx
            date_obj = datetime.strptime(dt_str, '%d/%m/%y')
            return (date_obj, date_obj.strftime('%Y-%m'))
        except ValueError:
             print(f"Warning: Invalid Android (YY) date format in line: {line.strip()}", file=sys.stderr)
             return (None, None)

    # No date format matched
    return (None, None)

# Function to split the chat text and move media files
def split_chat(input_file):
    """
    Splits the main chat text file by month/year and moves associated media files
    to a single 'mediafiles' subdirectory.
    """
    monthly_chats = defaultdict(list)
    base_dir = os.path.dirname(input_file)
    input_filename = os.path.basename(input_file)

    # Define the single destination directory for media files
    mediafiles_dir = os.path.join(base_dir, 'mediafiles')

    print(f"Processing chat file: {input_file}")
    print(f"Base directory: {base_dir}")
    print(f"Media files will be moved to: {mediafiles_dir}")

    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            print(f"Total lines read from chat file: {len(lines)}")
    except FileNotFoundError:
        print(f"Error: Chat file '{input_file}' not found.")
        return
    except PermissionError:
        print(f"Error: Permission denied for '{input_file}'. Check file access.")
        return
    except Exception as e:
         print(f"An unexpected error occurred while reading chat file: {e}")
         return


    current_month = None
    buffer = []
    lines_with_date = 0

    # --- Pass 1: Process chat text and determine month boundaries ---
    print("\n--- Starting text file splitting ---")
    for i, line in enumerate(lines):
        date_obj, month_str = extract_date_and_month(line)

        if date_obj:
            lines_with_date += 1
            # When a new date is found, process the buffered lines for the previous month
            if buffer and current_month:
                monthly_chats[current_month].extend(buffer)
                buffer = [] # Start new buffer

            current_month = month_str
            buffer.append(line)
        else:
            # This line is not a date marker. Append to buffer if we are inside a message block.
            if current_month: # Only append if we've found at least one date marker
                 buffer.append(line)
            else:
                 # Handle lines before the first date marker (e.g., header)
                 pass # Do nothing until the first date is found

    # Append any remaining lines in the buffer
    if buffer and current_month:
        monthly_chats[current_month].extend(buffer)
        buffer = [] # Clear buffer

    if not monthly_chats:
        print("No valid chat lines with detectable dates found. Text splitting skipped.")
    else:
        # --- Write out the monthly chat files ---
        print("\n--- Writing monthly chat files ---")
        total_lines_written = 0
        # Sort months chronologically for ordered output files
        for month in sorted(monthly_chats.keys()):
            chats = monthly_chats[month]
            year, month_num = month.split('-')
            output_dir = os.path.join(base_dir, year)
            os.makedirs(output_dir, exist_ok=True) # Create Year folder

            output_file = os.path.join(output_dir, f'{month_num}.txt') # Create Month file name
            try:
                with open(output_file, 'w', encoding='utf-8') as file:
                    file.writelines(chats)
                print(f'Created text file: {output_file} ({len(chats)} lines)')
                total_lines_written += len(chats)
            except PermissionError:
                print(f"Error: Permission denied writing to '{output_file}'.")
            except Exception as e:
                 print(f"An unexpected error occurred writing '{output_file}': {e}")

        print(f"\nText splitting complete. Total lines written across all files: {total_lines_written}")
        print(f"Total unique months found: {len(monthly_chats)}")

    # --- Pass 2: Process media files in the same directory ---
    print("\n--- Starting media file processing ---")
    media_files_moved = 0
    media_files_skipped = 0
    try:
        items_in_dir = os.listdir(base_dir)
    except PermissionError:
         print(f"Error: Permission denied listing files in '{base_dir}'. Cannot process media.")
         items_in_dir = [] # Skip media processing

    # Ensure the media files directory exists before moving anything
    try:
        os.makedirs(mediafiles_dir, exist_ok=True)
        print(f"Ensured '{mediafiles_dir}' directory exists.")
    except PermissionError:
        print(f"Error: Permission denied creating or accessing '{mediafiles_dir}'. Cannot move media files.")
        # If we can't create the directory, we shouldn't try to move files into it.
        items_in_dir = [] # Skip media processing loop

    for item_name in items_in_dir:
        item_path = os.path.join(base_dir, item_name)

        # Skip the chat input file itself
        if item_name == input_filename:
            continue

        # Skip directories (we only care about moving files)
        if os.path.isdir(item_path):
            # Also skip the newly created mediafiles_dir itself if we encounter it
            if item_path == mediafiles_dir:
                 continue
            # print(f"Skipped directory: '{item_name}'") # Uncomment for detailed logging
            continue


        # Try to identify files that look like WhatsApp media based on the date pattern
        # We still use the pattern to *identify* relevant files, even though we don't use the date for the folder name anymore.
        match = media_date_pattern.search(item_name)

        if match:
            # Define the destination path within the single mediafiles_dir
            dest_path = os.path.join(mediafiles_dir, item_name)

            # Check if the file is already in the mediafiles directory to avoid errors
            if os.path.dirname(item_path) == mediafiles_dir:
                 # print(f"Skipped file (already in mediafiles dir): '{item_name}'") # Uncomment for detailed logging
                 media_files_skipped += 1
                 continue # Skip moving it if it's already there

            try:
                # Move the file
                # Note: shutil.move will overwrite if the destination exists,
                # which is usually fine for file splitting.
                shutil.move(item_path, dest_path)
                print(f"Moved media file: '{item_name}' to '{mediafiles_dir}'")
                media_files_moved += 1
            except FileNotFoundError:
                # This is less likely now unless the file is removed between listdir and move
                print(f"Warning: Source file not found during move: '{item_path}'")
                media_files_skipped += 1
            except PermissionError:
                print(f"Error: Permission denied moving '{item_name}' to '{mediafiles_dir}'.")
                media_files_skipped += 1
            except Exception as e:
                print(f"An unexpected error occurred moving '{item_name}': {e}")
                media_files_skipped += 1
        else:
            # Files that don't match the media date pattern are skipped
            # print(f"Skipped file (no media date pattern found): '{item_name}'") # Uncomment for detailed logging
            media_files_skipped += 1

    print("\nMedia file processing complete.")
    print(f"Total media files moved to '{mediafiles_dir}': {media_files_moved}")
    print(f"Total files skipped (chat file, directories, already in media dir, non-matching names, errors): {media_files_skipped}")


if __name__ == "__main__":
    # Check if the input file path is set
    if not input_file_path or not os.path.exists(input_file_path):
        print(f"Error: Input file path is not valid or file not found: {input_file_path}")
        sys.exit(1) # Exit the script

    split_chat(input_file_path)