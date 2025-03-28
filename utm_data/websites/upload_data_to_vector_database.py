import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_KEY = os.getenv("DEFI_KNOWLEDGE_API_KEY")
BASE_URL = os.getenv("DEFI_KNOWLEDGE_API_URL")
SCRAPED_DATA_DIR = "scraped_data/"
SKIP_NON_200 = True
OVERWRITE_EXISTING = False  # Set to True to overwrite existing documents
SCRAPE_ID_KEY = "scrapeId"  # Key in metadata.json containing unique identifier

# Headers for API requests
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Define all metadata fields we want to use with their types
METADATA_FIELDS = {
    "title": "string",
    "source_url": "string",
    "page_url": "string",
    "status_code": "number",
    "language": "string",
    "generator": "string",
    "viewport": "string",
    "scrape_id": "string"  # Maps to SCRAPE_ID_KEY from metadata
}


class DifyKnowledgeManager:
    def __init__(self):
        self.existing_knowledge_bases = self._get_existing_knowledge_bases()
        self.existing_metadata_fields = {}
        self.processed_scrape_ids = self._load_processed_scrape_ids()

    def _get_existing_knowledge_bases(self) -> Dict[str, str]:
        """Get all existing knowledge bases and return as {name: id} dict"""
        try:
            response = requests.get(
                f"{BASE_URL}/datasets?limit=100",
                headers=HEADERS
            )
            response.raise_for_status()
            return {kb["name"]: kb["id"] for kb in response.json().get("data", [])}
        except Exception as e:
            print(f"Error fetching knowledge bases: {str(e)}")
            return {}

    def _get_existing_metadata_fields(self, kb_id: str) -> Dict[str, str]:
        """Get existing metadata fields for a knowledge base"""
        try:
            response = requests.get(
                f"{BASE_URL}/datasets/{kb_id}/metadata",
                headers=HEADERS
            )
            response.raise_for_status()
            return {field["name"]: field["id"] for field in response.json().get("doc_metadata", [])}
        except Exception as e:
            print(f"Error fetching metadata fields: {str(e)}")
            return {}

    def _create_metadata_field(self, kb_id: str, name: str, field_type: str) -> Optional[str]:
        """Create a new metadata field in the knowledge base"""
        try:
            response = requests.post(
                f"{BASE_URL}/datasets/{kb_id}/metadata",
                headers=HEADERS,
                json={"type": field_type, "name": name}
            )
            response.raise_for_status()
            return response.json().get("id")
        except Exception as e:
            print(f"Error creating metadata field '{name}': {str(e)}")
            return None

    def ensure_metadata_fields_exist(self, kb_id: str) -> bool:
        """Ensure all required metadata fields exist in the knowledge base"""
        existing_fields = self.existing_metadata_fields.setdefault(kb_id, self._get_existing_metadata_fields(kb_id))
        success = True

        for name, field_type in METADATA_FIELDS.items():
            if name not in existing_fields:
                if field_id := self._create_metadata_field(kb_id, name, field_type):
                    existing_fields[name] = field_id
                else:
                    success = False
        return success

    def create_knowledge_base(self, name: str) -> Optional[str]:
        """Create or get existing knowledge base"""
        if kb_id := self.existing_knowledge_bases.get(name):
            print(f"Using existing knowledge base: {name}")
            self.ensure_metadata_fields_exist(kb_id)
            return kb_id

        try:
            response = requests.post(
                f"{BASE_URL}/datasets",
                headers=HEADERS,
                json={
                    "name": name,
                    "permission": "only_me",
                    "indexing_technique": "high_quality"
                }
            )
            response.raise_for_status()
            kb_id = response.json()["id"]
            self.existing_knowledge_bases[name] = kb_id
            self.ensure_metadata_fields_exist(kb_id)
            return kb_id
        except Exception as e:
            print(f"Error creating knowledge base: {str(e)}")
            return None

    def _prepare_metadata(self, kb_id: str, metadata: Dict) -> List[Dict]:
        """Convert scraped metadata to Dify format"""
        field_mapping = {
            "title": "title",
            "sourceURL": "source_url",
            "url": "page_url",
            "statusCode": "status_code",
            "language": "language",
            "generator": "generator",
            "viewport": "viewport",
            SCRAPE_ID_KEY: "scrape_id"
        }

        prepared = []
        for scraped_key, our_key in field_mapping.items():
            if scraped_key in metadata and our_key in self.existing_metadata_fields[kb_id]:
                prepared.append({
                    "id": self.existing_metadata_fields[kb_id][our_key],
                    "value": str(metadata[scraped_key]),
                    "name": our_key
                })
        return prepared

    def _load_processed_scrape_ids(self) -> Set[str]:
        """Load previously processed scrape IDs (persisted between runs)"""
        try:
            with open("processed_scrape_ids.json", "r") as f:
                return set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return set()

    def _save_processed_scrape_ids(self):
        """Save processed scrape IDs to disk"""
        with open("processed_scrape_ids.json", "w") as f:
            json.dump(list(self.processed_scrape_ids), f)

    def handle_document(self, kb_id: str, metadata: Dict, content: str) -> bool:
        """Core document handling logic with duplicate prevention"""
        scrape_id = metadata.get(SCRAPE_ID_KEY)

        if not scrape_id:
            print("⚠️ Document missing scrapeId - cannot track duplicates")
            return False

        if scrape_id in self.processed_scrape_ids:
            if OVERWRITE_EXISTING:
                print(f"🔄 Updating existing document: {scrape_id}")
                # Implement update logic here if needed
            else:
                print(f"⏩ Skipping duplicate: {scrape_id}")
                return True

        try:
            # Document upload
            response = requests.post(
                f"{BASE_URL}/datasets/{kb_id}/document/create-by-text",
                headers=HEADERS,
                json={
                    "name": metadata.get("title", "Untitled Document"),
                    "text": content,
                    "indexing_technique": "high_quality",
                    "process_rule": {
                        "mode": "automatic",
                        "rules": {
                            "pre_processing_rules": [
                                {"id": "remove_extra_spaces", "enabled": True},
                                {"id": "remove_urls_emails", "enabled": True}
                            ],
                            "segmentation": {"separator": "\n", "max_tokens": 1000}
                        }
                    }
                }
            )
            response.raise_for_status()
            document_id = response.json()["document"]["id"]

            # Metadata upload
            metadata_payload = self._prepare_metadata(kb_id, metadata)
            if metadata_payload:
                requests.post(
                    f"{BASE_URL}/datasets/{kb_id}/documents/metadata",
                    headers=HEADERS,
                    json={"operation_data": [{"document_id": document_id, "metadata_list": metadata_payload}]}
                ).raise_for_status()

            self.processed_scrape_ids.add(scrape_id)
            print(f"✅ Successfully processed: {scrape_id}")
            return True

        except Exception as e:
            print(f"❌ Error processing document: {str(e)}")
            return False


def process_directory(root_dir: str):
    manager = DifyKnowledgeManager()

    for domain in os.listdir(root_dir):
        domain_path = os.path.join(root_dir, domain)
        if not os.path.isdir(domain_path):
            continue

        print(f"\n🌐 Processing domain: {domain}")
        kb_id = manager.create_knowledge_base(domain)
        if not kb_id:
            continue

        for root, _, files in os.walk(domain_path):
            if "metadata.json" in files and "content.json" in files:
                try:
                    with open(os.path.join(root, "metadata.json")) as f:
                        metadata = json.load(f)

                    if SKIP_NON_200 and metadata.get("statusCode") != 200:
                        continue

                    with open(os.path.join(root, "content.json")) as f:
                        content = json.load(f)["markdown"]

                    manager.handle_document(kb_id, metadata, content)

                except Exception as e:
                    print(f"Error processing {root}: {str(e)}")

    # Save processed IDs at end of run
    manager._save_processed_scrape_ids()


if __name__ == "__main__":
    if not os.path.exists(SCRAPED_DATA_DIR):
        print(f"Error: Directory {SCRAPED_DATA_DIR} not found")
    else:
        process_directory(SCRAPED_DATA_DIR)