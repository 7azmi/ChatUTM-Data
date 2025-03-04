import os
import json
import hashlib

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import CharacterTextSplitter

load_dotenv()

# Define paths
directory = "utm_data"
metadata_file = directory + "/file_hashes.json"

def compute_file_hash(file_path):
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_hashes(metadata_file):
    """Load file hashes from a metadata file."""
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            return json.load(f)
    return {}

def save_hashes(metadata_file, hashes):
    """Save file hashes to a metadata file."""
    with open(metadata_file, "w") as f:
        json.dump(hashes, f, indent=2)

def detect_changes(directory, metadata_file):
    """Detect new, modified, and deleted files."""
    current_hashes = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".md") and file != "README.md":
                file_path = os.path.join(root, file)
                current_hashes[file_path] = compute_file_hash(file_path)

    stored_hashes = load_hashes(metadata_file)

    new_files = [path for path in current_hashes if path not in stored_hashes]
    modified_files = [path for path in current_hashes if path in stored_hashes and current_hashes[path] != stored_hashes[path]]
    deleted_files = [path for path in stored_hashes if path not in current_hashes]

    return new_files, modified_files, deleted_files, current_hashes

def update_chromadb(new_files, modified_files, deleted_files, vector_store):
    """Update ChromaDB with new, modified, and deleted files."""
    embeddings = OpenAIEmbeddings()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    # DELETE embeddings for modified & deleted files
    files_to_remove = deleted_files + modified_files  # Remove old versions before adding new ones
    if files_to_remove:
        all_docs = vector_store.get()  # Fetch all stored docs
        ids_to_delete = [
            doc_id for doc_id, meta in zip(all_docs["ids"], all_docs["metadatas"])
            if meta and meta.get("source") in files_to_remove
        ]
        if ids_to_delete:
            vector_store.delete(ids=ids_to_delete)
            print(f"Deleted {len(ids_to_delete)} embeddings.")

    # ADD new & modified files
    for file_path in new_files + modified_files:
        loader = TextLoader(file_path)
        documents = loader.load()
        texts = text_splitter.split_documents(documents)
        vector_store.add_texts(
            [doc.page_content for doc in texts],
            metadatas=[{"source": file_path} for _ in texts]
        )

def log_changes(new_files, modified_files, deleted_files):
    """Log changes to the console."""
    print("Embedding Summary:")
    print(f"- New Files: {len(new_files)}")
    for file in new_files:
        print(f"  + {file}")
    print(f"- Modified Files: {len(modified_files)}")
    for file in modified_files:
        print(f"  * {file}")
    print(f"- Deleted Files: {len(deleted_files)}")
    for file in deleted_files:
        print(f"  - {file}")

# Initialize ChromaDB
vector_store = Chroma(persist_directory="./chroma_data", embedding_function=OpenAIEmbeddings())

# Detect changes
new_files, modified_files, deleted_files, current_hashes = detect_changes(directory, metadata_file)

# Update ChromaDB
update_chromadb(new_files, modified_files, deleted_files, vector_store)

# Log changes
log_changes(new_files, modified_files, deleted_files)

# Save updated hashes
save_hashes(metadata_file, current_hashes)
