from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_chroma import Chroma  # Updated import
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
import os

# Load environment variables (e.g., OpenAI API key)
load_dotenv()

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Step 1: Load ChromaDB with Persistence
embeddings = OpenAIEmbeddings()
vector_store = Chroma(
    persist_directory="./chroma_data",  # Directory where embeddings are stored
    embedding_function=embeddings
)

# Step 2: Retrieve Documents
retriever = vector_store.as_retriever()

# Step 3: Generate Response
qa_chain = RetrievalQA.from_chain_type(
    llm=OpenAI(),
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)

# Query the system
query = "What is the main topic of the document?"
response = qa_chain.invoke({"query": query})

# Print the response
print("Answer:", response["result"])
print("Source Documents:", response["source_documents"])