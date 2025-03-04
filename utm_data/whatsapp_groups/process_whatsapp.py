import os
import re
import datetime
import openai
from collections import defaultdict

# 🔹 SETUP YOUR OPENAI API KEY HERE 🔹
openai.api_key = "your-openai-api-key"

# File paths
CHAT_FILE = "FullChatFoundation.txt"  # Chat history file
OUTPUT_FOLDER = r"C:\Users\fares\ChatUTM-Data\utm_data\whatsapp_groups\iss-yemen\ysag\computing\2025"

# WhatsApp Chat Regex Pattern
WHATSAPP_REGEX = r"(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2} ?[ap]m) - ([^:]+): (.+)"

# Function to extract monthly chat data
def extract_monthly_chat(chat_file):
    monthly_chats = defaultdict(list)  # {Month Year: [Messages]}
    
    with open(chat_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    for line in lines:
        match = re.match(WHATSAPP_REGEX, line)
        if match:
            date, time, sender, message = match.groups()
            try:
                month_year = datetime.datetime.strptime(date, "%d/%m/%y").strftime("%B %Y")
            except ValueError:
                continue  # Skip invalid date formats
            
            # Append message to the corresponding month
            monthly_chats[month_year].append(f"{sender}: {message}")

    return monthly_chats

# Function to generate AI-based summary using OpenAI GPT
def generate_summary(messages, month):
    prompt = f"""
You are an AI that summarizes academic WhatsApp group discussions into an LLM-ready Markdown file.
Below is a chat history for {month}. Extract the most relevant information and structure it under the following sections:

- **Key Dates and Deadlines** (Exams, semester start, registration deadlines)
- **Course Registration Issues** (Problems and solutions)
- **Recommended Professors** (Good and bad lecturers for various courses)
- **Exam Preparation** (Tips, past papers, study resources)
- **Technical Issues** (System errors, VPN issues, solutions)
- **General Advice** (University guidance, electives, student support)
- **Miscellaneous** (Anything else important)

Here is the chat data:
{messages}

Now, generate a structured summary in Markdown format.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

# Function to save summaries to Markdown files
def save_summaries(monthly_chats, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    for month, messages in monthly_chats.items():
        summary = generate_summary("\n".join(messages), month)
        md_filename = os.path.join(output_folder, f"{month}.md")
        
        with open(md_filename, "w", encoding="utf-8") as md_file:
            md_file.write(summary)
        
        print(f"✅ AI Summary saved: {md_filename}")

# Main Execution
if __name__ == "__main__":
    monthly_chats = extract_monthly_chat(CHAT_FILE)
    save_summaries(monthly_chats, OUTPUT_FOLDER)
