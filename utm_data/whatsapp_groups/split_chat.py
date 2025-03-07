import re
import os
from collections import defaultdict
from datetime import datetime


# Function to extract the date from a chat line
def extract_date(line):
    # Use regex to find the date pattern in the line
    date_match = re.match(r'\[(\d{2}/\d{2}/\d{4}), \d{1,2}:\d{2}:\d{2}\s*[AP]M\]', line)
    if date_match:
        date_str = date_match.group(1)
        try:
            return datetime.strptime(date_str, '%d/%m/%Y')
        except ValueError:
            print(f"Warning: Invalid date format in line: {line.strip()}")
    return None


# Function to split the chat into monthly files
def split_chat_by_month(input_file):
    # Dictionary to store chat lines grouped by month
    monthly_chats = defaultdict(list)

    # Read the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            print(f"Total lines read: {len(lines)}")  # Debug print
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return

    current_date = None
    current_month = None
    buffer = []  # Buffer to store multi-line messages

    for line in lines:
        date = extract_date(line)
        if date:
            # If a new date is found, flush the buffer to the correct month
            if buffer and current_month:
                monthly_chats[current_month].extend(buffer)
                buffer = []

            # Update the current date and month
            current_date = date
            current_month = current_date.strftime('%Y-%m')
            buffer.append(line)  # Start a new buffer with the current line
        else:
            # If no date is found, it's a continuation of the previous message
            if current_date:
                buffer.append(line)

    # Flush any remaining buffer
    if buffer and current_month:
        monthly_chats[current_month].extend(buffer)

    # Write each month's chat to a separate file in the {yyyy}/{mm}.txt structure
    if not monthly_chats:
        print("No valid chat lines with dates found.")
        return

    total_lines = 0  # Counter for total lines across all files

    for month, chats in monthly_chats.items():
        year, month_num = month.split('-')
        output_dir = os.path.join(year)  # Create directory for the year
        os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist

        output_file = os.path.join(output_dir, f'{month_num}.txt')
        with open(output_file, 'w', encoding='utf-8') as file:
            file.writelines(chats)
        print(f'Created file: {output_file}')

        # Update the total line count
        total_lines += len(chats)

    # Print the total number of lines across all files
    print(f"Total lines across all files: {total_lines}")


# Main function
if __name__ == "__main__":
    input_file = '../_chat.txt'  # Replace with your actual file name
    split_chat_by_month(input_file)