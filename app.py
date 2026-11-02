import os
from flask import Flask, jsonify, render_template, request
from openai import OpenAI, APIError, APITimeoutError

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024

SYSTEM_PROMPT = """
You are SmartBot, a friendly AI assistant for a college project.
Answer clearly and politely.
Explain difficult topics in simple English.
Help with programming, studies, project ideas and general questions.
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

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({
            "reply": "Server setup incomplete: API key is not configured."
        }), 503

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
        client = OpenAI(api_key=api_key, timeout=45.0)

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            max_tokens=700
        )

        reply = response.choices[0].message.content

        return jsonify({
            "reply": reply or "I couldn't create an answer. Please try again."
        })

    except APITimeoutError:
        return jsonify({
            "reply": "The AI is taking too long. Please try again."
        }), 504

    except APIError:
        app.logger.exception("OpenAI API request failed")
        return jsonify({
            "reply": "The AI service could not complete your request. Please check the server logs and API configuration."
        }), 502

    except Exception:
        app.logger.exception("Unexpected chat error")
        return jsonify({
            "reply": "Something went wrong. Please check the server logs."
        }), 500


if __name__ == "__main__":
    app.run(debug=False)
