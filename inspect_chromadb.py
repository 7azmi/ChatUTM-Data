import chromadb
from chromadb.config import Settings

# Connect to the ChromaDB persistence directory
client = chromadb.Client(Settings(persist_directory="./chroma_data", is_persistent=True))

# List all collections in ChromaDB
collection_names = client.list_collections()
print("Collections in ChromaDB:")
for name in collection_names:
    print(f"- {name}")

# Inspect a specific collection
collection_name = "langchain"  # Default collection name used by LangChain
collection = client.get_collection(collection_name)

# Retrieve all documents and metadata
documents = collection.get()
print("\nDocuments in Collection:")
for doc_id, doc_metadata, doc_content in zip(documents["ids"], documents["metadatas"], documents["documents"]):
    print(f"ID: {doc_id}")
    print(f"Metadata: {doc_metadata}")
    print(f"Content: {doc_content}")
    print("-" * 50)

# Retrieve embeddings (optional)
embeddings = collection.get(include=["embeddings"])
print("\nSample Embeddings:")
for i, embedding in enumerate(embeddings["embeddings"][:2]):  # Print first 2 embeddings
    print(f"Embedding {i + 1}: {embedding[:5]}...")  # Print first 5 dimensions