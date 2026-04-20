from together import Together
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get API key
api_key = os.getenv("TOGETHER_API_KEY")
client = Together(api_key=api_key)

def embed_chunks(chunks):
    res = client.embeddings.create(
        input=chunks,
        model="intfloat/multilingual-e5-large-instruct"
    )
    return [e.embedding for e in res.data]