import re
from datetime import datetime
from collections import defaultdict
import os

# Function to extract the date from a chat line
def extract_date(line):
    date_match = re.match(r'\[(\d{2})/(\d{2})/(\d{4}), (\d{1,2}):(\d{2}):(\d{2})\s*([APap][Mm])\]', line)
    if date_match:
        day, month, year = date_match.group(1), date_match.group(2), date_match.group(3)
        try:
            return datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y")
        except ValueError:
            print(f"Warning: Invalid date format in line: {line.strip()}")
    return None

# Function to split the chat into yearly folders and monthly files
def split_chat_by_year_and_month(input_file):
    monthly_chats = defaultdict(list)

    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            print(f"Total lines read: {len(lines)}")  # Debug print
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

    base_dir = os.path.dirname(input_file)  # Get the existing "Mechanical" folder

    for month, chats in monthly_chats.items():
        year, month_num = month.split('-')
        year_folder = os.path.join(base_dir, year)  # Folder for each year

        os.makedirs(year_folder, exist_ok=True)  # Ensure the folder exists

        output_file = os.path.join(year_folder, f'{month_num}.txt')  # Month files (01.txt, 02.txt, etc.)

        with open(output_file, 'w', encoding='utf-8') as file:
            file.writelines(chats)

        print(f'Created file: {output_file}')

    print(f"Total years created: {len(set(m.split('-')[0] for m in monthly_chats))}")
    print(f"Total files created: {len(monthly_chats)}")

if __name__ == "__main__":
    input_file = r'C:\Users\fares\ChatUTM-Data\utm_data\whatsapp_groups\iss-yemen\ysag\Mechanical\FullChatYSAGMechanical.txt'  # Use raw string
    split_chat_by_year_and_month(input_file)
