import os
from flask import Flask, render_template, request, jsonify
from google import genai

app = Flask(__name__)

# Initialize the Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Models prioritized by availability & performance
MODEL_FALLBACKS = [
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite"
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

    # Loop through fallback models if one experiences high demand (503)
    for model_name in MODEL_FALLBACKS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_message,
            )
            return jsonify({"reply": response.text})
        except Exception as e:
            print(f"Model {model_name} failed with error: {e}. Trying fallback...")
            last_error = str(e)

    # If all models fail, return the error
    return jsonify({"error": f"Service busy. Details: {last_error}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
