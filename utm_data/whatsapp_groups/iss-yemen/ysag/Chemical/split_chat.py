import re
import os
from collections import defaultdict
from datetime import datetime

def extract_date(line):
    date_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{2}), (\d{1,2}:\d{2})\s?[AP]M', line)
    if date_match:
        date_str = date_match.group(1)
        try:
            return datetime.strptime(date_str, '%m/%d/%y')
        except ValueError:
            print(f"Warning: Invalid date format in line: {line.strip()}")
    return None

def split_chat_by_month(input_file):
    monthly_chats = defaultdict(list)

    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            print(f"Total lines read: {len(lines)}")
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return

    current_month = None
    buffer = []

    for line in lines:
        date = extract_date(line)
        if date:
            if buffer and current_month:
                monthly_chats[current_month].extend(buffer)
                buffer = []

            current_month = date.strftime('%Y-%m')
            buffer.append(line)
        else:
            if current_month:
                buffer.append(line)

    if buffer and current_month:
        monthly_chats[current_month].extend(buffer)

    total_lines = 0

    # Extract directory of the input file
    output_base_dir = os.path.dirname(input_file)

    for month, chats in monthly_chats.items():
        year, month_num = month.split('-')
        
        # Set the output directory relative to input file
        output_dir = os.path.join(output_base_dir, year)
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, f'{month_num}.txt')
        with open(output_file, 'w', encoding='utf-8') as file:
            file.writelines(chats)

        print(f'Created file: {output_file}')
        total_lines += len(chats)

    print(f"Total lines across all files: {total_lines}")

if __name__ == "__main__":
    input_file = r'C:\Users\fares\ChatUTM-Data\utm_data\whatsapp_groups\iss-yemen\ysag\Chemical\chemical.txt'
    split_chat_by_month(input_file)
