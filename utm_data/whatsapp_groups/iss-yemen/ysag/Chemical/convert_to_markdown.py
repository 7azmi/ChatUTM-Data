import os
import csv
import time
import requests
from dotenv import load_dotenv
from io import StringIO

# Load environment variables
load_dotenv('.env')

# DeepSeek API setup
api_key = os.getenv('DEEPSEEK_API_KEY')
if not api_key:
    raise ValueError("DEEPSEEK_API_KEY is missing from .env file")

API_URL = "https://api.deepseek.com/chat/completions"

SYSTEM_PROMPT = """
You are an assistant extracting structured question-answer pairs from WhatsApp chats.

CSV Format:
Timestamp,User,Question/Message,Answer/Response

- Include all clear questions and their respective answers.
- Exclude greetings, announcements, security notifications, media omitted messages, and casual chatter.
- Output should strictly follow CSV format provided above.
"""

def call_deepseek_api(chat_text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": chat_text},
        ],
        "max_tokens": 4096,
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"API Error: {response.status_code} - {response.text}")

def chunk_text(text, max_lines=250, overlap=10):
    lines = text.splitlines()
    chunks = []
    for i in range(0, len(lines), max_lines - overlap):
        chunks.append("\n".join(lines[i:i + max_lines]))
    return chunks

def parse_response_to_csv(api_response):
    csv_rows = []
    reader = csv.reader(StringIO(api_response.strip()))
    for row in reader:
        if len(row) == 4 and row[0] != "Timestamp":
            csv_rows.append(row)
    return csv_rows

def clean_chat_text(text):
    cleaned_lines = []
    for line in text.splitlines():
        if ("security code" in line or "<Media omitted>" in line 
            or line.strip().endswith("changed. Tap to learn more.")
            or "This message was deleted" in line):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)

def process_chat_to_csv(chat_file):
    print(f"Processing {chat_file}")
    with open(chat_file, "r", encoding="utf-8") as file:
        chat_text = file.read()

    chat_text = clean_chat_text(chat_text)
    chunks = chunk_text(chat_text)
    all_rows = []

    for idx, chunk in enumerate(chunks):
        print(f"Processing chunk {idx + 1}/{len(chunks)}...")
        api_response = call_deepseek_api(chunk)
        rows = parse_response_to_csv(api_response)
        all_rows.extend(rows)
        time.sleep(1)  # Avoid API rate limits

    csv_file = chat_file.replace('.txt', '.csv')
    with open(csv_file, "w", encoding="utf-8", newline="") as csv_out:
        writer = csv.writer(csv_out)
        writer.writerow(["Timestamp", "User", "Question/Message", "Answer/Response"])
        writer.writerows(all_rows)

    print(f"CSV file saved: {csv_file}")

def process_folder(folder_path):
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".txt"):
                chat_file = os.path.join(root, file)
                process_chat_to_csv(chat_file)

# Main execution
if __name__ == "__main__":
    chat_folder = r"C:\Users\fares\ChatUTM-Data\utm_data\whatsapp_groups\iss-yemen\ysag\Chemical\2022"
    process_folder(chat_folder)