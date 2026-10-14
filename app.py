from flask import Flask, render_template, request, jsonify
from google import genai
import os

app = Flask(__name__)

# Initialize the Google GenAI client (picks up GEMINI_API_KEY from Render)
client = genai.Client()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=user_message,
        )
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-graphic', methods=['POST'])
def generate_graphic():
    data = request.json
    text = data.get('text', 'DeLEGEND SMART INTELLIGENCE')
    return jsonify({
        "status": "success",
        "message": f"Generated custom graphic for: '{text}'",
        "author": "DeLEGEND SMART INTELLIGENCE"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

