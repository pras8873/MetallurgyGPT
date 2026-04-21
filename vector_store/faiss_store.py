import faiss
import numpy as np
import os
import pickle

INDEX_PATH = "faiss.index"
META_PATH = "metadata.pkl"


def init_faiss(dim=1024):
    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(INDEX_PATH)
        with open(META_PATH, "rb") as f:
            metadata = pickle.load(f)
        print("Loaded existing index ✅")
    else:
        index = faiss.IndexFlatL2(dim)
        metadata = []
        print("Created new index 🆕")

    return index, metadata


def save_faiss(index, metadata):
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(metadata, f)
    print("Saved index 💾")