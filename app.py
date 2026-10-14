from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

client = OpenAI()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": user_message}]
        )
        return jsonify({"response": response.choices[0].message.content})
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

