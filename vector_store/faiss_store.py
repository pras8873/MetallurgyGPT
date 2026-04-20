import faiss
import numpy as np

def init_faiss(dim=1024):
    index = faiss.IndexFlatL2(dim)
    metadata_store = []
    return index, metadata_store