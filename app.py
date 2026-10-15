import os
import time
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

# Initialize the Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Currently active models to try in order
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
    user_message = data.get("message", "")
    
    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    last_error = None

    # Loop through target models
    for model_name in MODELS_TO_TRY:
        # Retry up to 3 times for 503 high demand traffic spikes
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=user_message,
                )
                return jsonify({"reply": response.text})
            except Exception as e:
                last_error = str(e)
                # If hit by 503 high demand, wait 2 seconds and retry automatically
                if "503" in last_error or "UNAVAILABLE" in last_error:
                    time.sleep(2)
                    continue
                else:
                    # Non-503 error, break and switch to next model
                    break

    return jsonify({"error": "Google Gemini servers are temporarily busy. Please try again in a few seconds."}), 503

if __name__ == "__main__":
    app.run(debug=True)
