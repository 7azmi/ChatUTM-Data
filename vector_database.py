import os
import pinecone
from openai import OpenAI
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

# Load environment variables (for Pinecone and OpenAI API keys)
load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define the path to the 1.md file
file_path = "utm_data/whatsapp_groups/iss-yemen/ysag/computing/2025/1.md"

# Read the contents of the 1.md file
with open(file_path, "r", encoding="utf-8") as file:
    text = file.read()

# Generate embeddings using OpenAI's text-embedding-ada-002
response = client.embeddings.create(
    input=text,
    model="text-embedding-ada-002"
)
embedding = response.data[0].embedding

# Define Pinecone index name
index_name = "utm"

# Check if the index exists, otherwise create it
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=len(embedding),
        metric="cosine",  # Default metric for embeddings
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )

# Connect to the Pinecone index
index = pc.Index(index_name)

# Use the file path as the vector ID (truncate if necessary)
vector_id = file_path.replace("/", "-")[:512]  # Ensure it's within Pinecone's 512-character limit

# Insert the embedding into Pinecone
index.upsert([(vector_id, embedding)])

print(f"Embedding for '{file_path}' has been successfully uploaded to Pinecone index '{index_name}' with ID '{vector_id}'.")