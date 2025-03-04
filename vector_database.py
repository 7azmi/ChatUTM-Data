import os
import faiss
import openai
import numpy as np
from dotenv import load_dotenv
from git import Repo
from git.exc import InvalidGitRepositoryError

load_dotenv()
# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI embedding model
FAISS_INDEX_PATH = "vector_database/faiss_index.index"
FILE_PATHS_PATH = "vector_database/file_paths.npy"  # Path to store file paths (metadata)
REPO_ROOT_DIR = "."  # Root directory of the Git repository

# Initialize FAISS index
dimension = 1536  # Dimension of OpenAI embeddings
index = faiss.IndexFlatL2(dimension)

def get_embedding(text):
    """Get embedding for a given text using OpenAI's API."""
    response = openai.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def read_md_file(file_path):
    """Read the content of a .md file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def update_faiss_index(index, file_paths, embeddings, existing_file_paths):
    """Update the FAISS index with new embeddings and metadata."""
    if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(FILE_PATHS_PATH):
        # Load existing index and file paths
        index = faiss.read_index(FAISS_INDEX_PATH)
        existing_file_paths = np.load(FILE_PATHS_PATH, allow_pickle=True).tolist()
    else:
        # Create new index and file paths list
        index = faiss.IndexFlatL2(dimension)
        existing_file_paths = []

    # Update or add new embeddings
    for file_path, embedding in zip(file_paths, embeddings):
        if file_path in existing_file_paths:
            # Update existing embedding
            idx = existing_file_paths.index(file_path)
            index.remove_ids(np.array([idx]))
            index.add(np.array([embedding]).astype("float32"))
            print(f"Updated embedding for file: {file_path}")
        else:
            # Add new embedding
            existing_file_paths.append(file_path)
            index.add(np.array([embedding]).astype("float32"))
            print(f"Added new embedding for file: {file_path}")

    # Save the updated index and file paths
    faiss.write_index(index, FAISS_INDEX_PATH)
    np.save(FILE_PATHS_PATH, np.array(existing_file_paths))
    print(f"Updated FAISS index with {len(file_paths)} embeddings.")

def detect_changes(repo):
    """Detect new, modified, and deleted .md files using Git."""
    changes = {"new": [], "modified": [], "deleted": []}
    try:
        if repo.bare:
            raise InvalidGitRepositoryError("Not a valid Git repository.")

        # Get the current HEAD commit
        head_commit = repo.head.commit
        print(f"Current HEAD commit: {head_commit.hexsha}")

        # Get the previous commit (if any)
        previous_commit = head_commit.parents[0] if head_commit.parents else None
        if previous_commit:
            print(f"Previous commit: {previous_commit.hexsha}")

            # Compare current and previous commits
            diff = previous_commit.diff(head_commit)
            print(f"Found {len(diff)} changes in the repository.")

            for change in diff:
                file_path = change.a_path if change.a_path else change.b_path
                if file_path.endswith(".md") and file_path != "README.md":
                    if change.change_type == "A":
                        changes["new"].append(file_path)
                    elif change.change_type == "M":
                        changes["modified"].append(file_path)
                    elif change.change_type == "D":
                        changes["deleted"].append(file_path)
        else:
            print("No previous commit found. Assuming initial commit.")
    except InvalidGitRepositoryError:
        print(f"{REPO_ROOT_DIR} is not a Git repository. Skipping Git-based change detection.")
    return changes

def main():
    # Load existing FAISS index and file paths (if they exist)
    if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(FILE_PATHS_PATH):
        print("Loading existing FAISS index and file paths.")
        index = faiss.read_index(FAISS_INDEX_PATH)
        existing_file_paths = np.load(FILE_PATHS_PATH, allow_pickle=True).tolist()
    else:
        print("Creating new FAISS index and file paths.")
        index = faiss.IndexFlatL2(dimension)
        existing_file_paths = []

    # Initialize Git repository
    print(f"Initializing Git repository at: {REPO_ROOT_DIR}")
    try:
        repo = Repo(REPO_ROOT_DIR)
    except InvalidGitRepositoryError:
        print(f"Error: {REPO_ROOT_DIR} is not a valid Git repository.")
        return

    # Detect changes using Git
    print("Detecting changes in .md files...")
    changes = detect_changes(repo)
    print(f"Changes detected: {changes}")

    # Process new and modified files
    embeddings = []
    file_paths = []
    for file_path in changes["new"] + changes["modified"]:
        full_path = os.path.join(REPO_ROOT_DIR, file_path)
        print(f"Processing file: {full_path}")
        try:
            content = read_md_file(full_path)
            embedding = get_embedding(content)
            embeddings.append(embedding)
            file_paths.append(file_path)
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

    # Update FAISS index with new or updated embeddings
    if embeddings:
        print(f"Updating FAISS index with {len(embeddings)} embeddings.")
        update_faiss_index(index, file_paths, embeddings, existing_file_paths)
    else:
        print("No new or modified .md files to process.")

    # Handle deleted files
    if changes["deleted"]:
        print(f"Deleted files detected: {changes['deleted']}")
        for file_path in changes["deleted"]:
            if file_path in existing_file_paths:
                idx = existing_file_paths.index(file_path)
                index.remove_ids(np.array([idx]))
                existing_file_paths.pop(idx)
                print(f"Removed embedding for file: {file_path}")
        # Save the updated index and file paths
        faiss.write_index(index, FAISS_INDEX_PATH)
        np.save(FILE_PATHS_PATH, np.array(existing_file_paths))

if __name__ == "__main__":
    main()