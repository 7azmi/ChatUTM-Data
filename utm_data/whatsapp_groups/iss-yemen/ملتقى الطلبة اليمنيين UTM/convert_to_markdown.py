import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
# DeepSeek API configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")  # Replace with your actual DeepSeek API key
DEEPSEEK_BASE_URL = "https://api.deepseek.com"  # DeepSeek API base URL

# Initialize the OpenAI client for DeepSeek
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

# Prompt for the API
PROMPT = """
Extract useful question-answer conversations from the following chat history and format them in Markdown. 
Focus on extracting only meaningful and relevant question-answer pairs or discussions that provide actionable or informative content. 
Ignore messages with missing or irrelevant information (e.g., deleted messages, media omissions, security updates, daily announcements, casual greetings, or non-informative exchanges).

**Formatting Rules**:
1. **Direct Question-Answer Pairs**:
   - If a conversation consists of a direct question and a clear answer, format it concisely as:
     ```markdown
     ### [Topic/Subject]
     - **Question**: [Exact question text]
     - **Answer**: [Exact answer text]
     - **Timestamp**: [Timestamp of the question]
     ```

2. **Opinions & Responses**:
   - If multiple users provide varied opinions or responses to a question, structure it as:
     ```markdown
     ### [Topic/Subject]
     - **Inquiry**: [Exact question or topic]
     - **Opinions & Responses**:
       - [Username 1]: [Response 1] *(Timestamp)*
       - [Username 2]: [Response 2] *(Timestamp)*
     ```

3. **General Rules**:
   - Do not include summaries, additional comments, or irrelevant content.
   - Generate multiple markdown sections inside the file so that they can be split smoothly using Python.
   - Do not add a global title like "# ChatUTM Conversations" or any overarching headers.

**Chat History**:
{chat_text}

**Output in Markdown format. Do not add summary or other details, just the Markdown file text**:
---------------------------------------------
"""


# Function to call the DeepSeek API
def call_deepseek_api(chat_text):
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",  # Use the correct model name
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": chat_text},
            ],
            stream=False,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling DeepSeek API: {e}")
        return None


# Function to process a single chat file
def process_chat_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        chat_text = file.read()

    # Call the DeepSeek API to convert the chat to Markdown
    markdown_content = call_deepseek_api(chat_text)
    if not markdown_content:
        print(f"Skipping {input_file} due to API error.")
        return

    # Save the Markdown content to the output file
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(markdown_content)
    print(f"Created Markdown file: {output_file}")


# Function to process all chat files in the directory structure
def process_all_chat_files(base_dir, max_files=2):  # Add max_files parameter
    processed_files = 0  # Counter for processed files
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".txt") and processed_files < max_files:  # Limit the number of files
                input_file = os.path.join(root, file)
                output_file = os.path.join(root, file.replace(".txt", ".md"))
                process_chat_file(input_file, output_file)
                processed_files += 1  # Increment the counter
                if processed_files >= max_files:  # Stop after processing max_files
                    break


# Main function
if __name__ == "__main__":
    base_dir = "."  # Replace with the directory containing the {yyyy}/{mm}.txt files
    max_files = 1  # Process only 2 files for testing
    process_all_chat_files(base_dir, max_files)