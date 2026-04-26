import os
import pickle
import numpy as np
from flask import Flask, request, jsonify, render_template, session
from together import Together
from ddgs import DDGS
import faiss
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

import uuid
# -------- LOAD ENV --------
load_dotenv()
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
app = Flask(__name__)
CORS(app)
app.secret_key = "metallurgy-secret-key-123"   # change later
# -------- MODELS --------
#EMBED_MODEL = "togethercomputer/m2-bert-80M-32k-retrieval"
EMBED_MODEL = "intfloat/multilingual-e5-large-instruct"
#LLM_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"
#LLM_MODEL = "Qwen/Qwen2-7B-Instruct"
#LLM_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"
#LLM_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct-Lite"
LLM_MODEL = "Qwen/Qwen3.5-9B-FP8"
#DOC_MODEL = "Qwen/Qwen3.5-9B-FP8"
#WEB_MODEL = "LFM2-24B-A2B"
#WEB_MODEL = "Qwen/Qwen2.5-7B-Instruct-Turbo"
#DOC_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct-Lite"
#WEB_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct-Lite"
DOC_MODEL = "Qwen/Qwen3.5-9B"
WEB_MODEL = "LiquidAI/LFM2-24B-A2B"

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
def ask_llm(prompt, model):
    try:
        print("[LLM] Sending request...")
        print("model", model)
        print("prompt", prompt)
        response = client.chat.completions.create(
            model=model,
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


@app.route("/")
def home():
    return jsonify({"message": "MetallurgyGPT API running"})


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
        web_query = f"{query} metallurgy continuous casting steel"
        web_context = search_web(web_query)

        # -------- PROMPTS --------

        # 🔹 DOCUMENT PROMPT (strict grounding)
        doc_prompt = f"""
        You are a metallurgy expert.

        Use ONLY the provided internal database context.
        If answer is not present, say: Not found in internal database.

        Conversation:
        {chat_history}

        Context:
        {context}

        Question:
        {query}
        """

        # 🔹 WEB PROMPT (reasoning + interpretation)
        web_prompt = f"""
        You are a senior metallurgical engineer specializing in:

        - Continuous casting
        - Steelmaking
        - Segregation and solidification
        - EMS (Electromagnetic Stirring)
        - MEMS (Mold Electromagnetic Stirring)
        - FEMS (Final Electromagnetic Stirring)
        - MSR (Mechanical Soft Reduction)
        - Ladle furnace(LF)
        -Vaccume Degassing(VD)

        IMPORTANT:
        - Ignore unrelated meanings of MSR (like companies, TV shows, abbreviations)
        - Focus ONLY on metallurgy context
        - If web data is irrelevant, ignore it

        Conversation:
        {chat_history}

        Web Data:
        {web_context}

        Question:
        {query}

        Give a technically correct and industry-relevant answer.
        """

        print("[LLM] Generating document answer...")
        doc_answer = ask_llm(doc_prompt, DOC_MODEL)

        print("[LLM] Generating web answer...")
        web_answer = ask_llm(web_prompt, WEB_MODEL)

        # -------- COMBINE RESPONSE --------
        final_response = f"""
        From Internal Database:
        {doc_answer}
        
        From Web Search:
        {web_answer}
        """

        # -------- SAVE HISTORY --------
        chat_history.append({
            "user": query,
            "assistant": final_response
        })

        session["chat_history"] = chat_history

        return jsonify({"answer": final_response})

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