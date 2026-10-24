const chat = document.getElementById("chat");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const clearBtn = document.getElementById("clearBtn");

let history = [];
let busy = false;

function addMessage(role, text) {
    const row = document.createElement("div");
    row.className = `message ${role}`;

    if (role === "bot") {
        const avatar = document.createElement("div");
        avatar.className = "avatar";
        avatar.textContent = "✦";
        row.appendChild(avatar);
    }

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    // Use textContent so messages are displayed as text, not HTML.
    bubble.textContent = text;
    row.appendChild(bubble);
    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;

    return row;
}

async function sendMessage(text) {
    text = text.trim();

    if (!text || busy) return;

    busy = true;
    input.disabled = true;
    sendBtn.disabled = true;

    addMessage("user", text);

    const loading = addMessage("bot", "Thinking...");

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: text,
                history: history
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.reply || "Unable to send message.");
        }

        loading.querySelector(".bubble").textContent = data.reply;

        history.push(
            { role: "user", content: text },
            { role: "assistant", content: data.reply }
        );

        // Keep the browser conversation short.
        history = history.slice(-10);

    } catch (error) {
        loading.querySelector(".bubble").textContent =
            error.message || "Connection error. Please try again.";
    } finally {
        busy = false;
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
        chat.scrollTop = chat.scrollHeight;
    }
}

form.addEventListener("submit", function (event) {
    event.preventDefault();
    const text = input.value;
    if (text.trim() && !busy) {
        input.value = "";
        sendMessage(text);
    }
});

document.querySelectorAll(".suggestion").forEach(button => {
    button.addEventListener("click", () => {
        sendMessage(button.dataset.prompt);
    });
});

clearBtn.addEventListener("click", () => {
    if (busy) return;

    history = [];
    chat.replaceChildren();

    addMessage(
        "bot",
        "Chat cleared! 👋 What would you like to learn today?"
    );
});