import os
import pickle
import numpy as np
from flask import Flask, request, jsonify, render_template, session
from together import Together
from ddgs import DDGS
import faiss
from dotenv import load_dotenv
import uuid
# -------- LOAD ENV --------
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
app = Flask(__name__)
app.secret_key = "metallurgy-secret-key-123"   # change later
# -------- MODELS --------
#EMBED_MODEL = "togethercomputer/m2-bert-80M-32k-retrieval"
EMBED_MODEL = "intfloat/multilingual-e5-large-instruct"
#LLM_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"
#LLM_MODEL = "Qwen/Qwen2-7B-Instruct"
#LLM_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"
LLM_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct-Lite"
client = Together(api_key=TOGETHER_API_KEY)
# -------- LOAD FAISS --------
index = faiss.read_index("faiss.index")

with open("metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

print("FAISS + metadata loaded ✅")

# -------- EMBEDDING --------
import time


def embed_query(query, retries=3):
    for attempt in range(retries):
        try:
            print(f"[Embedding] Attempt {attempt + 1} for query")

            res = client.embeddings.create(
                model=EMBED_MODEL,
                input=[query]
            )

            print("[Embedding] Success ✅")
            return np.array(res.data[0].embedding).astype("float32")

        except Exception as e:
            print(f"[Embedding ERROR] {e}")
            time.sleep(2)

    raise Exception("Embedding failed after retries")


# -------- RETRIEVE --------
def retrieve_chunks(query, top_k=5):
    print(f"[Retrieve] Query: {query}")

    query_vec = embed_query(query).reshape(1, -1)

    print("[Retrieve] Searching FAISS...")
    distances, indices = index.search(query_vec, top_k)

    results = []
    for i in indices[0]:
        if i < len(metadata):
            results.append(metadata[i]["content"])

    print(f"[Retrieve] Found {len(results)} chunks")

    return "\n\n".join(results)


# -------- WEB SEARCH --------
def search_web(query):
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append(r["body"])
    except:
        return "Web search failed."

    return "\n".join(results)


# -------- LLM --------
def ask_llm(prompt):
    try:
        print("[LLM] Sending request...")

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a metallurgy expert."},
                {"role": "user", "content": prompt}
            ]
        )

        print("[LLM] Response received ✅")
        return response.choices[0].message.content

    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return "LLM failed to generate response."


# -------- ROUTES --------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.json
        query = data.get("query")

        print(f"\n[NEW QUERY] {query}")

        # -------- INIT SESSION --------
        if "chat_history" not in session:
            session["chat_history"] = []

        chat_history = session["chat_history"]

        # -------- RETRIEVE --------
        context = retrieve_chunks(query)
        web_context = search_web(query)

        # -------- PROMPT --------
        prompt = f"""
        You are a metallurgy expert chatbot.

        Conversation so far:
        {chat_history}

        Answer using:

        From Internal Database:
        {context}

        From Web Search:
        {web_context}

        Question:
        {query}

        Format:
        From Internal Database:
        <answer>

        From Web Search:
        <answer>
        """

        response = ask_llm(prompt)

        # -------- SAVE HISTORY --------
        chat_history.append({
            "user": query,
            "assistant": response
        })

        session["chat_history"] = chat_history

        return jsonify({"answer": response})

    except Exception as e:
        print(f"[FATAL ERROR] {e}")
        return jsonify({"answer": "Error occurred"}), 500

@app.route("/clear", methods=["POST"])
def clear():
    session.pop("chat_history", None)
    return jsonify({"status": "cleared"})
# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)