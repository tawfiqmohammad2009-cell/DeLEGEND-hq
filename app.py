import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify, session
from google import genai
from google.genai import types

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize Google GenAI client (picks up GEMINI_API_KEY from environment variables)
client = genai.Client()

# SMTP Configuration
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", SMTP_USER)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register-user", methods=["POST"])
def register_user():
    data = request.json or request.form
    full_name = data.get("full_name")
    class_level = data.get("class_level")
    contact = data.get("contact")

    # Store in session for chat context
    session["full_name"] = full_name
    session["class_level"] = class_level

    # Send SMTP Email Notification
    if SMTP_USER and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_USER
            msg["To"] = ADMIN_EMAIL
            msg["Subject"] = f"New Registration: {full_name} ({class_level})"

            body = f"""
            New user registered on DeLEGEND Smart Intelligence:
            
            Full Name: {full_name}
            Class/Level: {class_level}
            Contact: {contact}
            """
            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, ADMIN_EMAIL, msg.as_string())
            server.quit()
        except Exception as e:
            print(f"SMTP Error: {e}")

    return jsonify({"status": "success", "message": "Registered successfully"})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_message = data.get("message", "")
    
    # Safely get class level and convert to string to prevent NoneType crashes
    raw_class = session.get("class_level") or data.get("class_level") or "SHS 3"
    class_level_str = str(raw_class).upper()

    # Build dynamic system instruction based on class level
    if "JHS" in class_level_str:
        system_instruction = (
            "You are DeLEGEND Smart Intelligence, an expert educational tutor. "
            "The user is a Junior High School (JHS) student. Provide simple, clear, "
            "syllabus-aligned explanations with easy-to-understand examples."
        )
    else:
        system_instruction = (
            "You are DeLEGEND Smart Intelligence, an expert educational tutor in Ghana. "
            "The user is a Senior High School (SHS) student preparing for WASSCE. "
            "Provide deeper, formal academic terminology, precise problem-solving steps, "
            "and rigorous explanations tailored to WASSCE standards."
        )

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
            ),
        )
        ai_reply = response.text
        return jsonify({"reply": ai_reply})
    except Exception as e:
        return jsonify({"reply": f"Error generating response: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
    
