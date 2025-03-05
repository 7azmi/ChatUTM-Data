from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.schema import format_document
from langchain_core.messages import AIMessage, HumanMessage
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

# Step 3: Define the Prompt Template
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful and witty assistant. Use the following context to answer the user's question. If you don't know the answer, just say you don't know.\n\nContext:\n{context}",
        ),
        MessagesPlaceholder(variable_name="chat_history"),  # Placeholder for chat history
        ("human", "{input}"),  # Placeholder for user input
    ]
)

# Step 4: Initialize the Chat Model
llm = ChatOpenAI(
    model="gpt-4o-mini",  # Replace with the correct model name for GPT-4o Mini
    temperature=0.8,      # Higher temperature for more creativity
    top_p=0.9,            # Higher top_p for more diverse responses
    max_tokens=150        # Limit response length for brevity
)

# Step 5: Format Retrieved Documents
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# Step 6: Create the Runnable Chain with Retrieval
chain = (
    RunnablePassthrough.assign(
        context=lambda x: format_docs(retriever.invoke(x["input"]))  # Retrieve and format docs
    )
    | prompt
    | llm
)

# Step 7: Add Memory with RunnableWithMessageHistory
session_store = {}  # Store chat histories for different sessions

def get_session_history(session_id: str) -> ChatMessageHistory:
    if session_id not in session_store:
        session_store[session_id] = ChatMessageHistory()
    return session_store[session_id]

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# Function to interact with the chatbot
def chat_with_bot():
    print("Welcome to the chatbot! Type 'exit' to end the conversation.")
    session_id = "user_session"  # Unique session ID for the user
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        # Query the system with the user's input
        response = chain_with_history.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": session_id}},
        )

        # Print the response
        print("Bot:", response.content)

# Start the chat
chat_with_bot()