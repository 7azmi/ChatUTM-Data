import re
from datetime import datetime
from collections import defaultdict
import os

# Function to extract the date from a chat line
def extract_date(line):
    # Updated regex to allow 2 or 4 digit years in the date
    date_match = re.match(r'(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2})\s*([APap][Mm])', line)
    if date_match:
        date_str = date_match.group(1)
        # Determine if the year is 2 or 4 digits by checking the last part of the date
        parts = date_str.split('/')
        year = parts[-1]
        try:
            if len(year) == 4:
                # Assuming day/month/year format
                return datetime.strptime(date_str, '%d/%m/%Y')
            else:
                return datetime.strptime(date_str, '%d/%m/%y')
        except ValueError:
            print(f"Warning: Invalid date format in line: {line.strip()}")
    return None

# Function to split the chat into monthly files
def split_chat_by_month(input_file):
    monthly_chats = defaultdict(list)

    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            print(f"Total lines read: {len(lines)}")
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return
    except PermissionError:
        print(f"Error: Permission denied for '{input_file}'. Check file access.")
        return

    current_date = None
    current_month = None
    buffer = []

    for line in lines:
        date = extract_date(line)
        if date:
            # When a new date is found, write out the buffered lines for the previous month
            if buffer and current_month:
                monthly_chats[current_month].extend(buffer)
                buffer = []

            current_date = date
            current_month = current_date.strftime('%Y-%m')
            buffer.append(line)
        else:
            if current_date:
                buffer.append(line)

    # Append any remaining lines
    if buffer and current_month:
        monthly_chats[current_month].extend(buffer)

    if not monthly_chats:
        print("No valid chat lines with dates found.")
        return

    total_lines = 0
    base_dir = os.path.dirname(input_file)  # Files will be saved in the same folder as the input file

    for month, chats in monthly_chats.items():
        year, month_num = month.split('-')
        output_dir = os.path.join(base_dir, year)
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, f'{month_num}.txt')
        with open(output_file, 'w', encoding='utf-8') as file:
            file.writelines(chats)
        print(f'Created file: {output_file}')

        total_lines += len(chats)

    print(f"Total lines across all files: {total_lines}")

if __name__ == "__main__":
    # Update this path to the location of your chat file
    input_file = r'C:\Users\fares\ChatUTM-Data\utm_data\whatsapp_groups\iss-yemen\ysag\Biomedical\FullChatBiomedical.txt'
    split_chat_by_month(input_file)
