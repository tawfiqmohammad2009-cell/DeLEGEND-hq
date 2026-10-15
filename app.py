import os
import time
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

# Initialize the Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MODELS_TO_TRY = [
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite"
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    history = data.get("history", [])
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Build contents with full conversation history
    contents = []
    for item in history:
        role = "user" if item["sender"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": item["text"]}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    last_error = None

    for model_name in MODELS_TO_TRY:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                )
                return jsonify({"reply": response.text})
            except Exception as e:
                last_error = str(e)
                if "503" in last_error or "UNAVAILABLE" in last_error:
                    time.sleep(2)
                    continue
                else:
                    break

    return jsonify({"error": "DeLEGEND AI network busy. Retrying momentarily..."}), 503

if __name__ == "__main__":
    app.run(debug=True)
