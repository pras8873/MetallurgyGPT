import hashlib
import json
import os
from ingestion.extractors import extract_text
from ingestion.chunking import chunk_text
from ingestion.embedding import embed_chunks
import numpy as np

def process_file(file_path, index, metadata_store):
    text = extract_text(file_path)

    if not text:
        return

    # -------- CHUNKING --------
    chunks = chunk_text(text)

    if not chunks:
        return

    # -------- DEBUG --------
    save_chunks_debug(chunks, os.path.basename(file_path))

    # -------- FILTER SAFE CHUNKS --------
    safe_chunks = [c for c in chunks if len(c.split()) < 300]

    if not safe_chunks:
        print(f"All chunks too large: {file_path}")
        return

    # -------- EMBEDDING --------
    try:
        vectors = embed_chunks(safe_chunks)
    except Exception as e:
        print(f"Embedding failed for {file_path}: {e}")
        return

    # -------- STORE (ALIGNED) --------
    for i, (chunk, vector) in enumerate(zip(safe_chunks, vectors)):
        index.add(np.array([vector]).astype("float32"))

        metadata_store.append({
            "source": file_path,
            "content": chunk,
            "chunk_id": i
        })

    print(f"Processed: {file_path} | Chunks stored: {len(safe_chunks)}")

def process_folder(folder_path, index, metadata_store):
    processed_files = load_processed_files()

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)

            current_hash = get_file_hash(file_path)
            if current_hash is None:
                continue

            # -------- SKIP LOGIC --------
            if file_path in processed_files:
                if processed_files[file_path] == current_hash:
                    print(f"Skipping (unchanged): {file_path}")
                    continue
                else:
                    print(f"Reprocessing (file changed): {file_path}")

            # -------- PROCESS --------
            process_file(file_path, index, metadata_store)

            # -------- UPDATE TRACKING --------
            processed_files[file_path] = current_hash

    save_processed_files(processed_files)

def save_chunks_debug(chunks, file_name):
    os.makedirs("debug_chunks", exist_ok=True)

    with open(f"debug_chunks/{file_name}.txt", "w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks):
            f.write(f"\n--- CHUNK {i} ---\n")
            f.write(chunk)
            f.write("\n")

PROCESSED_FILE = "processed_files.json"


# -------- LOAD --------
def load_processed_files():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, "r") as f:
            return json.load(f)   # returns dict
    return {}   # file_path → hash


# -------- SAVE --------
def save_processed_files(processed_files):
    with open(PROCESSED_FILE, "w") as f:
        json.dump(processed_files, f, indent=2)


# -------- HASH --------
def get_file_hash(file_path):
    try:
        with open(file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        print(f"Hash error for {file_path}: {e}")
        return None