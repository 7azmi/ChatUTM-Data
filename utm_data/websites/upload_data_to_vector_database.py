import os
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

# Configuration
API_KEY = os.getenv("DEFI_KNOWLEDGE_API_KEY")
BASE_URL = os.getenv("DEFI_KNOWLEDGE_API_URL")
SCRAPED_DATA_DIR = "scraped_data/"
SKIP_NON_200 = True

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
    "scrape_id": "string"
}


class DifyKnowledgeManager:
    def __init__(self):
        self.existing_knowledge_bases = self._get_existing_knowledge_bases()
        self.existing_metadata_fields = {}  # {kb_id: {field_name: field_id}}

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

            fields = {}
            for field in response.json().get("doc_metadata", []):
                fields[field["name"]] = field["id"]
            return fields
        except Exception as e:
            print(f"Error fetching metadata fields for KB {kb_id}: {str(e)}")
            return {}

    def _create_metadata_field(self, kb_id: str, name: str, field_type: str) -> Optional[str]:
        """Create a new metadata field in the knowledge base"""
        try:
            payload = {
                "type": field_type,
                "name": name
            }

            response = requests.post(
                f"{BASE_URL}/datasets/{kb_id}/metadata",
                headers=HEADERS,
                json=payload
            )
            response.raise_for_status()

            field_id = response.json().get("id")
            if field_id:
                print(f"Created metadata field '{name}' in KB {kb_id}")
                return field_id
        except Exception as e:
            print(f"Error creating metadata field '{name}': {str(e)}")
        return None

    def ensure_metadata_fields_exist(self, kb_id: str) -> bool:
        """Ensure all required metadata fields exist in the knowledge base"""
        if kb_id not in self.existing_metadata_fields:
            self.existing_metadata_fields[kb_id] = self._get_existing_metadata_fields(kb_id)

        existing_fields = self.existing_metadata_fields[kb_id]
        all_success = True

        for name, field_type in METADATA_FIELDS.items():
            if name not in existing_fields:
                field_id = self._create_metadata_field(kb_id, name, field_type)
                if field_id:
                    existing_fields[name] = field_id
                else:
                    all_success = False

        return all_success

    def create_knowledge_base(self, name: str, description: str = "") -> Optional[str]:
        """Create a new knowledge base if it doesn't exist"""
        if name in self.existing_knowledge_bases:
            print(f"Knowledge base '{name}' already exists")
            kb_id = self.existing_knowledge_bases[name]
            # Ensure metadata fields exist for existing KBs too
            self.ensure_metadata_fields_exist(kb_id)
            return kb_id

        try:
            payload = {
                "name": name,
                "description": description,
                "permission": "only_me",
                "indexing_technique": "high_quality"
            }

            response = requests.post(
                f"{BASE_URL}/datasets",
                headers=HEADERS,
                json=payload
            )
            response.raise_for_status()

            kb_id = response.json().get("id")
            if kb_id:
                self.existing_knowledge_bases[name] = kb_id
                print(f"Created knowledge base '{name}' with ID: {kb_id}")
                # Create metadata fields for new KB
                self.ensure_metadata_fields_exist(kb_id)
                return kb_id

        except Exception as e:
            print(f"Error creating knowledge base '{name}': {str(e)}")

        return None

    def _prepare_metadata(self, kb_id: str, metadata: Dict) -> List[Dict]:
        """Convert scraped metadata to Dify metadata format"""
        prepared = []

        # Mapping from scraped metadata fields to our defined fields
        field_mapping = {
            "title": "title",
            "sourceURL": "source_url",
            "url": "page_url",
            "statusCode": "status_code",
            "language": "language",
            "generator": "generator",
            "viewport": "viewport",
            "scrapeId": "scrape_id"
        }

        for scraped_field, our_field in field_mapping.items():
            if scraped_field in metadata and our_field in self.existing_metadata_fields[kb_id]:
                prepared.append({
                    "id": self.existing_metadata_fields[kb_id][our_field],
                    "value": str(metadata[scraped_field]),
                    "name": our_field
                })

        return prepared

    def upload_document(
            self,
            kb_id: str,
            title: str,
            content: str,
            metadata: Dict,
            doc_form: str = "text_model"
    ) -> bool:
        """Upload a document to the knowledge base with metadata"""
        try:
            # First upload the content
            upload_payload = {
                "name": title,
                "text": content,
                "indexing_technique": "high_quality",
                "doc_form": doc_form,
                "process_rule": {
                    "mode": "automatic",
                    "rules": {
                        "pre_processing_rules": [
                            {"id": "remove_extra_spaces", "enabled": True},
                            {"id": "remove_urls_emails", "enabled": True}
                        ],
                        "segmentation": {
                            "separator": "\n",
                            "max_tokens": 1000
                        }
                    }
                }
            }

            upload_response = requests.post(
                f"{BASE_URL}/datasets/{kb_id}/document/create-by-text",
                headers=HEADERS,
                json=upload_payload
            )
            upload_response.raise_for_status()

            document_id = upload_response.json().get("document", {}).get("id")
            if not document_id:
                print(f"Failed to get document ID for '{title}'")
                return False

            # Prepare and upload metadata
            metadata_list = self._prepare_metadata(kb_id, metadata)
            if metadata_list:
                metadata_payload = {
                    "operation_data": [{
                        "document_id": document_id,
                        "metadata_list": metadata_list
                    }]
                }

                metadata_response = requests.post(
                    f"{BASE_URL}/datasets/{kb_id}/documents/metadata",
                    headers=HEADERS,
                    json=metadata_payload
                )
                metadata_response.raise_for_status()

            print(f"Successfully uploaded '{title}' to knowledge base {kb_id}")
            return True

        except Exception as e:
            print(f"Error uploading document '{title}': {str(e)}")
            return False


def process_directory(root_dir: str):
    """Process all scraped data and upload to Dify"""
    manager = DifyKnowledgeManager()

    for subdomain in os.listdir(root_dir):
        subdomain_path = os.path.join(root_dir, subdomain)
        if not os.path.isdir(subdomain_path):
            continue

        print(f"\nProcessing subdomain: {subdomain}")

        # Create or get knowledge base for this subdomain
        kb_id = manager.create_knowledge_base(
            name=subdomain,
            description=f"Knowledge base for {subdomain}"
        )

        if not kb_id:
            print(f"Skipping subdomain {subdomain} - couldn't create/get knowledge base")
            continue

        # Process all content files in this subdomain
        for root, _, files in os.walk(subdomain_path):
            if "content.json" in files and "metadata.json" in files:
                content_path = os.path.join(root, "content.json")
                metadata_path = os.path.join(root, "metadata.json")

                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    # Skip if status code is not 200 and we're configured to skip
                    if SKIP_NON_200 and metadata.get("statusCode") != 200:
                        print(f"Skipping {content_path} - status code {metadata.get('statusCode')}")
                        continue

                    with open(content_path, 'r', encoding='utf-8') as f:
                        content_data = json.load(f)

                    # Get title from metadata or use the directory name
                    title = metadata.get("title", os.path.basename(root))
                    markdown_content = content_data.get("markdown", "")

                    if not markdown_content.strip():
                        print(f"Skipping {content_path} - empty content")
                        continue

                    # Upload the document
                    success = manager.upload_document(
                        kb_id=kb_id,
                        title=title,
                        content=markdown_content,
                        metadata=metadata
                    )

                    if not success:
                        print(f"Failed to upload {content_path}")

                except Exception as e:
                    print(f"Error processing {content_path}: {str(e)}")


if __name__ == "__main__":
    if not os.path.exists(SCRAPED_DATA_DIR):
        print(f"Error: Scraped data directory not found at {SCRAPED_DATA_DIR}")
    else:
        process_directory(SCRAPED_DATA_DIR)