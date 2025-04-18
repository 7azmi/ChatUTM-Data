import re

def process_markdown(md_file_path):
    """
    Processes a markdown file to:
        - Add a space within each headline
        - Keep one newline between headlines
        - Add two newlines after the Date headline
        - Preserves original file on error.

    Args:
        md_file_path (str): The path to the markdown file.
    """

    try:
        with open(md_file_path, 'r') as f:
            content = f.read()
        original_content = content

        # Remove "---" lines and extra spaces (as before, for safety)
        content = re.sub(r'^(---+)$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^[ ]+', '', content, flags=re.MULTILINE)
        content = re.sub(r'[ ]+$', '', content, flags=re.MULTILINE)
        content = re.sub(r'\n\s*\n', '\n', content)

        # Add one space within every chunk headline (e.g., ###Lecturer Information becomes ### Lecturer Information)
        content = re.sub(r'(###)(\w)', r'\1 \2', content)

        # Ensure there is only one newline between headlines and two newlines after the date headline
        content = re.sub(r'(###\s+.*?)\n(###\s+.*?)', r'\1\n\2', content) #One new line betw headlines
        content = re.sub(r'(###\s+Date\n\d{4}-\d{2}-\d{2})\n', r'\1\n\n', content) #two newlines after date

        with open(md_file_path, 'w') as f:
            f.write(content)

    except Exception as e:
        print(f"An error occurred: {e}")
        with open(md_file_path, 'w') as f:
            f.write(original_content)
        print("Original content restored.")
        return

    print(f"Markdown file '{md_file_path}' processed and updated.")


# Example usage:
file_path = '/home/humadi/Github/ChatUTM-Data/utm_data/whatsapp_groups/iss-yemen/ysag/electrical/mediafiles/ysag-electrical-faculty.md'  # Replace with your file path
process_markdown(file_path)