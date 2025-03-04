# ChatUTM-Data

This repository is designed to manage and process documents for the **ChatUTM** application. It uses **ChromaDB** for storing document embeddings and **OpenAI embeddings** for text processing. The goal is to enable efficient document retrieval and querying for UTM-related data.

---

## Key Features

- **Document Embedding**: Automatically detects and embeds new or updated documents into ChromaDB.
- **Change Detection**: Tracks file changes using SHA-256 hashes to ensure only relevant updates are processed.
- **Querying**: Allows querying of embedded documents for retrieval tasks.
- **Inspection**: Provides tools to inspect the contents of ChromaDB.
