import os
import time
import csv
import json
from openai import OpenAI
from dotenv import load_dotenv
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)

# Load environment variables
load_dotenv()

# Initialize DeepSeek API client
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')  # Use your DeepSeek API key
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# System message with the long prompt
SYSTEM_PROMPT = """
You are a helpful assistant. Extract meaningful question-answer pairs or discussions from the chat history, focusing on academic or university-related topics. Format the output in structured JSON with these keys:

- "topic": A descriptive topic of the discussion (e.g., "Network Communication Exam Preparation").
- "category": The category of the discussion. Must be one of: "Academic", "Student Life", "Visa/Immigration", or "Other".
- "question": Exact question or inquiry text.
- "answer": Exact answer or responses, including emails, contact numbers, or links if provided.
- "keywords": A list of relevant keywords or phrases related to the discussion (e.g., ["exam", "network communication", "test 2"]).
- "timestamp": Timestamp if available, formatted as "YYYY-MM-DD" (date only).

Ignore casual greetings, announcements, media omissions, missing or incomplete answers, or non-informative exchanges.
"""

# Function to call the DeepSeek API
def call_deepseek_api(chat_text):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # Use the correct DeepSeek model
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": chat_text}
            ],
            max_tokens=4096,  # Adjust based on your needs
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        print(Fore.RED + f"API Error: {e}")
        return "[]"

# Function to clean and parse the JSON response
def parse_json_response(json_response):
    # Remove backticks and 'json' marker if present
    if json_response.strip().startswith("```json"):
        json_response = json_response.strip()[7:-3].strip()  # Remove ```json and trailing ```
    try:
        return json.loads(json_response)
    except json.JSONDecodeError as e:
        print(Fore.RED + f"JSON Parsing Error: {e}")
        return []

# Function to split text into manageable chunks
def chunk_text(text, max_lines=250, overlap=10):
    lines = text.splitlines()  # Split text into lines
    chunks = []
    for i in range(0, len(lines), max_lines - overlap):
        chunk = "\n".join(lines[i:i + max_lines])  # Join lines into a chunk
        chunks.append(chunk)
    return chunks

# Function to process a single chat file with chunking
def process_single_file(file_path):
    # Read the chat history from the file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            chat_text = f.read()
    except Exception as e:
        print(Fore.RED + f"Error reading file {file_path}: {e}")
        return

    # Split the chat text into chunks
    chunks = chunk_text(chat_text)
    print(f"Processing file: {file_path} (split into {len(chunks)} chunks)")

    # Process each chunk and collect the results
    csv_data = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i + 1}/{len(chunks)}...")
        json_response = call_deepseek_api(chunk)
        print(f"json_response\n{json_response}\n")  # Debugging: Print the raw response
        # Parse JSON response and append to csv_data
        data = parse_json_response(json_response)
        if data:
            csv_data.extend(data)
        else:
            print(Fore.RED + f"Skipping chunk {i + 1} due to parsing error.")

    # Write the output to a CSV file
    csv_file_path = file_path.replace(".txt", ".csv")
    try:
        with open(csv_file_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=["topic", "category", "question", "answer", "keywords", "timestamp"])
            writer.writeheader()
            writer.writerows(csv_data)
        print(Fore.GREEN + f"Converted {file_path} -> {csv_file_path}")
    except Exception as e:
        print(Fore.RED + f"Error writing CSV file {csv_file_path}: {e}")

# Function to process all files in a folder
def process_folder(folder_path):
    # Check if the folder exists
    if not os.path.exists(folder_path):
        print(Fore.RED + f"Folder not found: {folder_path}")
        return

    # Iterate over all files in the folder
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        # Process only .txt files
        if file_name.endswith(".txt"):
            process_single_file(file_path)

# Main execution
if __name__ == "__main__":
    # Specify the path to the folder containing chat files
    chat_folder = r"C:\Users\fares\ChatUTM-Data\utm_data\whatsapp_groups\iss-yemen\ysag\Electrical\2025"  # Replace with your folder path
    process_folder(chat_folder)