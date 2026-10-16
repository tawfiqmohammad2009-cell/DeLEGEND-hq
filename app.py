import os
import time
import json
from flask import Flask, render_template_string, request, jsonify
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeLEGEND AI</title>
    <style>
        body { background-color: #121212; color: #e0e0e0; font-family: sans-serif; margin: 0; padding: 15px; display: flex; flex-direction: column; height: 90vh; box-sizing: border-box; }
        h2 { color: #f39c12; margin: 0 0 10px 0; font-size: 1.2rem; }
        #chat-container { flex: 1; overflow-y: auto; border: 1px solid #333; padding: 12px; margin-bottom: 12px; border-radius: 8px; background: #1e1e1e; }
        .message { margin-bottom: 10px; padding: 10px; border-radius: 6px; line-height: 1.4; word-break: break-word; }
        .user { background: #2c3e50; text-align: right; }
        .model { background: #34495e; text-align: left; }
        #chat-form { display: flex; gap: 8px; align-items: center; }
        input[type="text"] { flex: 1; padding: 12px; border-radius: 6px; border: 1px solid #444; background: #222; color: #fff; font-size: 1rem; outline: none; }
        button { padding: 12px 18px; border: none; border-radius: 6px; background: #f39c12; color: #000; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        /* Explicit styling for when the button is locked/disabled */
        button:disabled { background: #444 !important; color: #888 !important; cursor: not-allowed; opacity: 0.7; }
        #image-input { display: none; }
        .attach-btn { background: #333; color: #fff; padding: 12px 14px; cursor: pointer; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }
    </style>
</head>
<body>
    <h2>DeLEGEND AI</h2>
    <div id="chat-container">
        <div class="message model"><b>AI:</b> Welcome to DeLEGEND AI. Type a question or attach an image to begin.</div>
    </div>

    <form id="chat-form">
        <input type="text" id="user-input" placeholder="Type your prompt..." autocomplete="off">
        <label for="image-input" class="attach-btn" id="attach-label">📎</label>
        <input type="file" id="image-input" accept="image/*">
        <button type="submit" id="send-btn">Send</button>
    </form>

    <script>
        const chatForm = document.getElementById('chat-form');
        const userInput = document.getElementById('user-input');
        const imageInput = document.getElementById('image-input');
        const sendBtn = document.getElementById('send-btn');
        const chatContainer = document.getElementById('chat-container');

        let chatHistory = [];

        chatForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const text = userInput.value.trim();
            const imageFile = imageInput.files[0];

            if (!text && !imageFile) return;

            // 1. LOCK THE SEND BUTTON IMMEDIATELY
            sendBtn.disabled = true;
            sendBtn.textContent = "Thinking...";
            userInput.disabled = true; // Also disable input to prevent multiple submissions

            let userDisplay = text ? text : "";
            if (imageFile) userDisplay += ` [Image: ${imageFile.name}]`;
            chatContainer.innerHTML += `<div class="message user"><b>You:</b> ${userDisplay}</div>`;
            chatContainer.scrollTop = chatContainer.scrollHeight;

            const formData = new FormData();
            formData.append('message', text);
            formData.append('history', JSON.stringify(chatHistory));
            if (imageFile) {
                formData.append('image', imageFile);
            }

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    chatContainer.innerHTML += `<div class="message model"><b>AI:</b> ${data.reply}</div>`;
                    
                    if (text) chatHistory.push({ sender: 'user', text: text });
                    chatHistory.push({ sender: 'model', text: data.reply });

                    userInput.value = '';
                    imageInput.value = '';
                } else {
                    chatContainer.innerHTML += `<div class="message model" style="color: #e74c3c;"><b>Error:</b> ${data.error || "Something went wrong."}</div>`;
                }
            } catch (err) {
                console.error("Network error:", err);
                chatContainer.innerHTML += `<div class="message model" style="color: #e74c3c;"><b>Error:</b> Network failure.</div>`;
            } finally {
                // 2. UNLOCK THE BUTTON ONCE AI RESPONDS
                sendBtn.disabled = false;
                sendBtn.textContent = "Send";
                userInput.disabled = false;
                userInput.focus();
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.form.get("message", "")
    history_str = request.form.get("history", "[]")
    
    try:
        history = json.loads(history_str)
    except Exception:
        history = []

    image_file = request.files.get("image")

    if not user_message and not image_file:
        return jsonify({"error": "Message or image cannot be empty"}), 400

    contents = []
    for item in history:
        role = "user" if item["sender"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": item["text"]}]})

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

