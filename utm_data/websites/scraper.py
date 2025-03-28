import os
import json
from urllib.parse import urlparse
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

load_dotenv()


def create_folder_structure(url):
    """Create folder structure based on URL"""
    parsed = urlparse(url)
    netloc = parsed.netloc.replace('www.', '')
    path = parsed.path.strip('/')
    folder_path = os.path.join('scraped_data', netloc)
    if path:
        path_parts = path.split('/')
        folder_path = os.path.join(folder_path, *path_parts)
    return folder_path


def save_to_json(data, folder_path):
    """Save data as JSON in the specified folder"""
    os.makedirs(folder_path, exist_ok=True)
    if 'markdown' in data:
        with open(os.path.join(folder_path, 'content.json'), 'w', encoding='utf-8') as f:
            json.dump({'markdown': data['markdown']}, f, indent=2, ensure_ascii=False)
    if 'metadata' in data:
        with open(os.path.join(folder_path, 'metadata.json'), 'w', encoding='utf-8') as f:
            json.dump(data['metadata'], f, indent=2, ensure_ascii=False)


def process_single_url(url, app):
    """Process a single URL with detailed error reporting"""
    print(f"\nProcessing: {url}")

    try:
        result = app.scrape_url(url, {'formats': ['markdown', 'html']})

        if isinstance(result, dict) and 'markdown' in result:
            folder_path = create_folder_structure(url)
            save_to_json(result, folder_path)
            print(f"✓ Successfully saved: {url}")
            return True
        else:
            print(f"⚠️ Unexpected response format for {url}")
            return False

    except Exception as e:
        print(f"🔥 Error processing {url}:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {str(e)}")
        return False


def main():
    # Initialize API
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

    # Load URLs
    input_file = "most_important_links (700 out of 70k).txt"  # Changed to simpler filename
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(urls)} URLs")
    os.makedirs('scraped_data', exist_ok=True)

    # Process URLs one by one
    success_count = 0
    for i, url in enumerate(urls, 1):
        print(f"\nURL {i}/{len(urls)}")
        if process_single_url(url, app):
            success_count += 1

        # Manual control for debugging
        if i < len(urls):
            input("Press Enter to continue to next URL...")

    print(f"\nFinished processing. Success: {success_count}/{len(urls)}")


if __name__ == "__main__":
    main()