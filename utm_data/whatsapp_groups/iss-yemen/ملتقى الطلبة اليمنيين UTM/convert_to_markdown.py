import os
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))  # Use your OpenAI API key

# System message with the long prompt
SYSTEM_PROMPT = """
You are a helpful assistant. Extract useful question-answer conversations from the following chat history and format them in Markdown. 
Focus on extracting only meaningful and relevant question-answer pairs or discussions that provide actionable or informative content, mostly academic or related to student life in university.
Ignore messages with missing or irrelevant information (e.g., deleted messages, media omissions, security updates, daily announcements, casual greetings, or non-informative exchanges).

**Formatting Rules**:
1. **Direct Question-Answer Pairs**:
   - If a conversation consists of a direct question and a clear answer, format it concisely as:
     ### [Topic/Subject]
     - **Question**: [Exact question text]
     - **Answer**: [Exact answer text, including links if provided] *(Timestamp)*

2. **Opinions & Responses**:
   - If multiple users provide varied opinions or responses to a question, structure it as:
     ### [Topic/Subject]
     - **Inquiry**: [Exact question or topic]
     - **Opinions & Responses**:
       - [Username 1]: [Response 1, including links if provided] *(Timestamp)*
       - [Username 2]: [Response 2, including links if provided] *(Timestamp)*

3. **General Rules**:
   - Do not include summaries, additional comments, or irrelevant content.
   - Generate multiple markdown sections inside the file so that they can be split smoothly using Python.
   - Do not add a global title like "# ChatUTM Conversations" or any overarching headers.
   - Output raw Markdown text only. Do not wrap the output in "```markdown" or any other code block syntax.
   - Ensure links are included in the output when they are part of the response.
"""

# Function to call the OpenAI API
def call_openai_api(chat_text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use GPT-4 Turbo
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": chat_text},
            ],
            max_tokens=4096,  # Adjust based on your needs
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"API Error: {e}")
        return ""

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
    with open(file_path, "r", encoding="utf-8") as f:
        chat_text = f.read()

    # Split the chat text into chunks
    chunks = chunk_text(chat_text)
    print(f"Processing file: {file_path} (split into {len(chunks)} chunks)")

    # Process each chunk and collect the results
    md_content = ""
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i + 1}/{len(chunks)}...")
        md_content += call_openai_api(chunk) + "\n"
        time.sleep(1)  # Avoid rate limits

    # Write the output to a Markdown file
    md_file_path = file_path.replace(".txt", ".md")
    with open(md_file_path, "w", encoding="utf-8") as md_file:
        md_file.write(md_content)

    print(f"Converted {file_path} -> {md_file_path}")

# Main execution
if __name__ == "__main__":
    # Specify the path to a single chat file
    chat_file = "2024/06.txt"  # Replace with your file path
    if os.path.exists(chat_file):
        process_single_file(chat_file)
    else:
        print(f"File not found: {chat_file}")