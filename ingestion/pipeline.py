import os
from ingestion.extractors import extract_text
from ingestion.chunking import chunk_text
from ingestion.embedding import embed_chunks
import numpy as np

def process_file(file_path, index, metadata_store):
    text = extract_text(file_path)
    if not text:
        return

    chunks = chunk_text(text)
    vectors = embed_chunks(chunks)

    index.add(np.array(vectors).astype("float32"))

    for chunk in chunks:
        metadata_store.append({
            "source": file_path,
            "content": chunk
        })

def process_folder(folder_path, index, metadata_store):
    for root, _, files in os.walk(folder_path):
        for file in files:
            path = os.path.join(root, file)
            try:
                process_file(path, index, metadata_store)
                print(f"Processed: {file}")
            except Exception as e:
                print(f"Error: {file}, {e}")