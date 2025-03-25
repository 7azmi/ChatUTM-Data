# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
MESSAGES_PER_CHUNK = 200  # Number of messages per chunk

# Load multiple Gemini API keys
GEMINI_API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5"),
    os.getenv("GEMINI_API_KEY_6"),
]

# Filter out any None values in case some keys are missing
GEMINI_API_KEYS = [key for key in GEMINI_API_KEYS if key]

SYSTEM_PROMPT = """
STRICTLY transform WhatsApp lecturer reviews into RAW markdown text (no code blocks). ONLY output if:
1. Lecturer name is clearly identified
2. Contains actual review content

Format (include ONLY available information):

### Lecturer Information
- **Name**: [Full name - REQUIRED]
- **Courses**: [If mentioned]
- **Contact**: [If provided]

### Review Summary
[Combined English summary]

### Key Points
[Bullet points of mentioned attributes]

### Context
[Relevant info from attachments]

### Date
[YYYY-MM-DD]

RULES:
1. NEVER use markdown code blocks (```)
2. Output must begin directly with ###
3. Include ALL sections with available info
4. Skip ENTIRE review if name is missing
5. Only use actual mentioned information
6. Combine duplicate comments naturally
7. Preserve critical negative/positive remarks
8. Date must be from message metadata
"""

MEDIA_CACHE = {}