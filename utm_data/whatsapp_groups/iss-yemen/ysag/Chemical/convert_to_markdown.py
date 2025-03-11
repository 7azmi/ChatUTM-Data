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
You are a helpful assistant. Extract meaningful question-answer pairs or discussions from the chat history, focusing on academic or university-related topics. Format the output in Markdown following these rules:

1. **Direct Question-Answer Pairs**:
   - Format as:
     ### [Topic/Subject]
     - **Question**: [Exact question text]
     - **Answer**: [Exact answer text, including links if provided] *(Timestamp)*

2. **Opinions & Responses**:
   - Format as:
     ### [Topic/Subject]
     - **Inquiry**: [Exact question or topic]
     - **Opinions & Responses**:
       - [Username 1]: [Response 1, including links if provided] *(Timestamp)*
       - [Username 2]: [Response 2, including links if provided] *(Timestamp)*

3. **General Rules**:
   - Ignore casual greetings, announcements, media omissions, or non-informative exchanges.
   - Ignore requests for filling out forms.
   - Output raw Markdown text only, without overarching headers or code block syntax.
   - Split content into multiple Markdown sections for easy processing.
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

# Function to process all files in a folder
def process_folder(folder_path):
    # Check if the folder exists
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
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
    chat_folder = "../2022/"  # Replace with your folder path
    process_folder(chat_folder)