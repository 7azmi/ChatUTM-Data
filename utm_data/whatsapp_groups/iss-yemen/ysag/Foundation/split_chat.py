import re
from datetime import datetime
from collections import defaultdict
import os

# Function to extract the date from a chat line using the new format: m/d/yy, h:mm [am/pm]
def extract_date(line):
    date_match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{2}),\s*(\d{1,2}):(\d{2})\s*([APap][Mm])', line)
    if date_match:
        month, day, year = date_match.group(1), date_match.group(2), date_match.group(3)
        hour, minute, ampm = date_match.group(4), date_match.group(5), date_match.group(6)
        try:
            # Create a datetime object using the extracted values
            return datetime.strptime(f"{month}/{day}/{year} {hour}:{minute} {ampm}", "%m/%d/%y %I:%M %p")
        except ValueError:
            print(f"Warning: Invalid date format in line: {line.strip()}")
    return None

# Function to split the chat into monthly files
def split_chat_by_month(input_file):
    monthly_chats = defaultdict(list)

    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            print(f"Total lines read: {len(lines)}")  # Debug print
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return

    current_date = None
    current_month = None
    buffer = []

    for line in lines:
        date = extract_date(line)
        if date:
            if buffer and current_month:
                monthly_chats[current_month].extend(buffer)
                buffer = []

            current_date = date
            current_month = current_date.strftime('%Y-%m')
            buffer.append(line)
        else:
            if current_date:
                buffer.append(line)

    if buffer and current_month:
        monthly_chats[current_month].extend(buffer)

    if not monthly_chats:
        print("No valid chat lines with dates found.")
        return

    total_lines = 0

    for month, chats in monthly_chats.items():
        year, month_num = month.split('-')
        output_dir = os.path.join(year)
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, f'{month_num}.txt')
        with open(output_file, 'w', encoding='utf-8') as file:
            file.writelines(chats)
        print(f'Created file: {output_file}')

        total_lines += len(chats)

    print(f"Total lines across all files: {total_lines}")

if __name__ == "__main__":
    input_file = r'C:\Users\fares\ChatUTM-Data\utm_data\whatsapp_groups\iss-yemen\ysag\Foundation\FullChatFoundation.txt'  # Replace with your actual file path
    split_chat_by_month(input_file)
