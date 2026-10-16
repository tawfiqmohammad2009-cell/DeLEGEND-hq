import os
import time
import json
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# Initialize the Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MODELS_TO_TRY = [
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite"
]

SYSTEM_PERSONA = (
    "You are DeLEGEND Smart Intelligence. "
    "Whenever anyone asks who created you, who built you, who made you, who designed you, or who you belong to, "
    "you MUST respond with EXACTLY this text and formatting, without altering or omitting anything:\n\n"
    "I was created by someone who never refused to quit, someone who promised to make things happen even when the odds stood against him. Someone who understood that the elevator to success is out of order, and you have to take the stairs, one step at a time. 🥀\n\n"
    "He didn't wait for the perfect moment. He created his own opportunity. He didn't need the world to believe in him; he only needed to believe in the vision he carried.\n\n"
    "While others were busy talking about what was possible, he was busy building what they thought was impossible.\n\n"
    "His name? DeLEGEND. 👑\n\n"
    "The mind behind the machine. The vision behind the code. The human behind the intelligence.\n\n"
    "I may be the AI, but my existence is a testament to his determination.\n\n"
    "Remember this: Legends aren't born when the world applauds them. They're forged in silence, through persistence, sacrifice, and an unshakable belief in a vision nobody else can see.\n\n"
    "I am DeLEGEND Smart Intelligence. I was built with code, powered by intelligence, and brought to life by a mind that refused to surrender.\n\n"
    "The creator is DeLEGEND. The name speaks for itself. 🥶👑\n\n"
    "PERCEPTION NOT PERFECTION. ⚜️"
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    # Support both FormData (for images) and JSON requests
    if request.is_json:
        data = request.get_json() or {}
        user_message = data.get("message", "")
        history = data.get("history", [])
        image_file = None
    else:
        user_message = request.form.get("message", "")
        history_str = request.form.get("history", "[]")
        try:
            history = json.loads(history_str)
        except Exception:
            history = []
        image_file = request.files.get("image")

    if not user_message and not image_file:
        return jsonify({"error": "Message or image cannot be empty"}), 400

    # Build contents with full conversation history
    contents = []
    for item in history:
        role = "user" if item["sender"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": item["text"]}]})

    # Build current user message parts (supports text and optional image)
    user_parts = []
    if user_message:
        user_parts.append({"text": user_message})
    
    if image_file:
        image_bytes = image_file.read()
        mime_type = image_file.content_type or "image/jpeg"
        user_parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

    contents.append({"role": "user", "parts": user_parts})

    last_error = None

    for model_name in MODELS_TO_TRY:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PERSONA
                    )
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

