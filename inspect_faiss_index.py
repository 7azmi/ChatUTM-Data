import os
import faiss
import numpy as np

# Configuration
FAISS_INDEX_PATH = "vector_database/faiss_index.index"  # Path to the FAISS index
FILE_PATHS_PATH = "vector_database/file_paths.npy"      # Path to the file storing metadata (file paths)

def inspect_faiss_index(index_path, file_paths_path):
    """Inspect the contents of a FAISS index and display metadata."""
    if not os.path.exists(index_path):
        print(f"Error: FAISS index file '{index_path}' does not exist.")
        return

    # Load the FAISS index
    index = faiss.read_index(index_path)
    print(f"FAISS index loaded from '{index_path}'.")

    # Get the number of vectors in the index
    num_vectors = index.ntotal
    print(f"Number of vectors in the index: {num_vectors}")

    # Load metadata (file paths)
    if os.path.exists(file_paths_path):
        file_paths = np.load(file_paths_path, allow_pickle=True)
        print(f"Metadata (file paths) loaded from '{file_paths_path}'.")
    else:
        print(f"Warning: Metadata file '{file_paths_path}' does not exist.")
        file_paths = None

    # Retrieve all vectors from the index
    if num_vectors > 0:
        print("\nInspecting vectors:")
        vectors = index.reconstruct_n(0, num_vectors)  # Retrieve all vectors
        for i, vector in enumerate(vectors):
            print(f"Vector {i}:")
            if file_paths is not None and i < len(file_paths):
                print(f"File: {file_paths[i]}")
            print(vector)  # Print the raw vector (embedding)
            print("-" * 40)
    else:
        print("The index is empty.")

if __name__ == "__main__":
    inspect_faiss_index(FAISS_INDEX_PATH, FILE_PATHS_PATH)