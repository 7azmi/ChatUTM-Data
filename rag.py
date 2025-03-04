from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.text_splitter import CharacterTextSplitter
from dotenv import load_dotenv
import os

# Load environment variables (e.g., OpenAI API key)
load_dotenv()

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Step 1: Load Documents
loader = TextLoader("utm_data/whatsapp_groups/iss-yemen/ysag/computing/2025/1.md")
documents = loader.load()

# Step 2: Split Documents into Chunks
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
texts = text_splitter.split_documents(documents)

# Step 3: Embed Documents
embeddings = OpenAIEmbeddings()

# Step 4: Store in ChromaDB with Persistence
vector_store = Chroma.from_documents(
    documents=texts,
    embedding=embeddings,
    persist_directory="./chroma_data"  # Directory to store embeddings
)

# Step 5: Retrieve Documents
retriever = vector_store.as_retriever()

# Step 6: Generate Response
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