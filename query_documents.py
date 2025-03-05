from langchain_openai import OpenAIEmbeddings, ChatOpenAI  # Use ChatOpenAI for custom models
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
import os

# Load environment variables (e.g., API key)
load_dotenv()

# Set your OpenAI API key (or custom API key for GPT-4o Mini)
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Step 1: Load ChromaDB with Persistence
embeddings = OpenAIEmbeddings()
vector_store = Chroma(
    persist_directory="./chroma_data",  # Directory where embeddings are stored
    embedding_function=embeddings
)

# Step 2: Retrieve Documents
retriever = vector_store.as_retriever()

# Step 3: Generate Response with GPT-4o Mini and increased creativity
qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(
        model="gpt-4o-mini",  # Replace with the correct model name for GPT-4o Mini
        temperature=0.8,      # Higher temperature for more creativity
        top_p=0.9,           # Higher top_p for more diverse responses
        max_tokens=150        # Limit response length for brevity
    ),
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)

# Query the system with a witty prompt
query = "what is your name"
response = qa_chain.invoke({"query": query})

# Print the response
print("Answer:", response["result"])
print("Source Documents:", response["source_documents"])