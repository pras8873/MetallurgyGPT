// 🔴 IMPORTANT: replace with your deployed backend URL
const BASE_URL = "http://127.0.0.1:5000";

function addMessage(text, type) {
    const chat = document.getElementById("chat");

    const msg = document.createElement("div");
    msg.className = "message " + type;
    msg.innerText = text;

    chat.appendChild(msg);
    chat.scrollTop = chat.scrollHeight;
}

async function ask() {
    const query = document.getElementById("query").value;
    if (!query) return;

    addMessage(query, "user");

    document.getElementById("query").value = "";

    addMessage("Thinking...", "bot");

    const res = await fetch(`${BASE_URL}/ask`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({query})
    });

    const data = await res.json();

    // remove "Thinking..."
    document.querySelector(".bot:last-child").remove();

    addMessage(data.answer, "bot");
}

async function clearChat() {
    await fetch(`${BASE_URL}/clear`, {method: "POST"});
    document.getElementById("chat").innerHTML = "";
}