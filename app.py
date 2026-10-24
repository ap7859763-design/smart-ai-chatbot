from flask import Flask, jsonify, render_template, request
import requests

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2:1b"

SYSTEM_PROMPT = """
You are SmartBot, a friendly AI assistant for a college project.
Answer clearly and politely.
Explain difficult topics in simple English.
Help with programming, studies, ideas and general questions.
If you do not know something, say so honestly.
"""

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    history = data.get("history", [])

    if not isinstance(message, str):
        return jsonify({"reply": "Invalid message."}), 400

    message = message.strip()

    if not message:
        return jsonify({"reply": "Please enter a message."}), 400

    if len(message) > 4000:
        return jsonify({
            "reply": "Please keep your message under 4000 characters."
        }), 400

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if isinstance(history, list):
        for item in history[-10:]:
            if not isinstance(item, dict):
                continue

            role = item.get("role")
            content = item.get("content")

            if role in ("user", "assistant") and isinstance(content, str):
                messages.append({
                    "role": role,
                    "content": content[:4000]
                })

    messages.append({"role": "user", "content": message})

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False
            },
            timeout=180
        )
        response.raise_for_status()

        result = response.json()
        reply = result.get("message", {}).get("content", "")

        return jsonify({
            "reply": reply or "I couldn't create an answer. Please try again."
        })

    except requests.exceptions.ConnectionError:
        return jsonify({
            "reply": "Cannot connect to Ollama. Please open Ollama and try again."
        }), 503

    except requests.exceptions.Timeout:
        return jsonify({
            "reply": "The AI is taking too long. Please try again."
        }), 504

    except requests.exceptions.RequestException:
        app.logger.exception("Local AI request failed")
        return jsonify({
            "reply": "Local AI request failed. Please check the terminal."
        }), 502


if __name__ == "__main__":
    app.run(debug=True)