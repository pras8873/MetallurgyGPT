def chunk_text(text, max_words=200):
    words = text.split()
    chunks = []

    for i in range(0, len(words), max_words):
        chunk = words[i:i + max_words]
        chunks.append(" ".join(chunk))
    print("Chunk size:", [len(c.split()) for c in chunks])
    return chunks

from ingestion.embedding import embed_chunks
def safe_embed(chunks):
    valid_chunks = []

    for chunk in chunks:
        if len(chunk.split()) < 500:  # safety
            valid_chunks.append(chunk)

    return embed_chunks(valid_chunks)