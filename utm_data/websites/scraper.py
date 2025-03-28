import os
import json
from urllib.parse import urlparse
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

load_dotenv()

# Configuration
OVERWRITE_EXISTING = False  # Set to True to overwrite existing files, False to skip
LOG_FILE = "scrape_log.txt"  # File to log processing results


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


def log_message(message, print_message=True):
    """Log message to file and optionally print to console"""
    if print_message:
        print(message)
    with open(LOG_FILE, 'a', encoding='utf-8') as log:
        log.write(message + '\n')


def check_existing_files(url):
    """Check if files already exist for this URL"""
    folder_path = create_folder_structure(url)
    content_file = os.path.join(folder_path, 'content.json')
    metadata_file = os.path.join(folder_path, 'metadata.json')

    content_exists = os.path.exists(content_file)
    metadata_exists = os.path.exists(metadata_file)

    return content_exists or metadata_exists


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
    log_message(f"\nProcessing: {url}")

    # Check for existing files
    if check_existing_files(url) and not OVERWRITE_EXISTING:
        log_message("⏩ Already exists, skipping (set OVERWRITE_EXISTING=True to overwrite)")
        return "skipped"

    try:
        result = app.scrape_url(url, {'formats': ['markdown', 'html']})

        if isinstance(result, dict) and 'markdown' in result:
            folder_path = create_folder_structure(url)
            save_to_json(result, folder_path)
            log_message(f"✓ Successfully saved: {url}")
            return "success"
        else:
            log_message(f"⚠️ Unexpected response format for {url}")
            return "failed"

    except Exception as e:
        log_message(f"🔥 Error processing {url}:")
        log_message(f"Error type: {type(e).__name__}")
        log_message(f"Error details: {str(e)}")
        return "failed"


def main():
    # Initialize logging
    with open(LOG_FILE, 'w', encoding='utf-8') as log:
        log.write("Scraping Log\n============\n")

    # Initialize API
    app = FirecrawlApp(
        api_key=os.getenv("FIRECRAWL_API_KEY"),
        api_url=os.getenv("FIRECRAWL_API_URL")
    )

    # Load URLs
    input_file = "most_important_links (700 out of 70k).txt"
    if not os.path.exists(input_file):
        log_message(f"Error: Input file '{input_file}' not found")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    log_message(f"Loaded {len(urls)} URLs")
    log_message(f"OVERWRITE_EXISTING set to {OVERWRITE_EXISTING}")
    os.makedirs('scraped_data', exist_ok=True)

    # Process URLs
    results = {
        "success": 0,
        "failed": 0,
        "skipped": 0
    }

    for i, url in enumerate(urls, 1):
        log_message(f"\nURL {i}/{len(urls)}")
        status = process_single_url(url, app)
        results[status] += 1

    # Summary
    log_message("\n=== Processing Summary ===")
    log_message(f"Total URLs: {len(urls)}")
    log_message(f"Successful: {results['success']}")
    log_message(f"Failed: {results['failed']}")
    log_message(f"Skipped (existing): {results['skipped']}")
    log_message(f"Success rate: {results['success'] / len(urls) * 100:.1f}%")


if __name__ == "__main__":
    main()