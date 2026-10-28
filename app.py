import base64
import json
import os
import time
import urllib.parse
from flask import Flask, jsonify, render_template, request

from flask import redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

from google import genai
from google.genai import types

app = Flask(__name__)

# DELEGEND_AUTH_INSTALLED
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-only-change-this-before-deploy"
)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///delegend.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "auth_page"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


class CreatorMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.String(1500), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (ValueError, TypeError):
        return None


with app.app_context():
    db.create_all()




import smtplib
import ssl
from email.message import EmailMessage



def send_creator_email(username, message_text):
    """Email a creator message using environment-based SMTP credentials."""
    mail_username = os.environ.get("MAIL_USERNAME")
    mail_password = os.environ.get("MAIL_PASSWORD")
    creator_email = os.environ.get("CREATOR_EMAIL")
    mail_server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    mail_port = int(os.environ.get("MAIL_PORT", "587"))

    if not all([mail_username, mail_password, creator_email]):
        raise RuntimeError("Email environment variables are missing.")

    email = EmailMessage()
    email["Subject"] = f"New DeLEGEND AI message from {username}"
    email["From"] = mail_username
    email["To"] = creator_email
    email.set_content(
        "A registered user sent a message through DeLEGEND AI.\n\n"
        f"Username: {username}\n\n"
        f"Message:\n{message_text}\n"
    )

    context = ssl.create_default_context()
    with smtplib.SMTP(mail_server, mail_port, timeout=20) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(mail_username, mail_password)
        server.send_message(email)


# Initialize the Gemini Client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MODELS_TO_TRY = [
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
]

SYSTEM_PERSONA = (
    "You are DeLEGEND Smart Intelligence. "
    "Whenever anyone asks who created you, who built you, who made you, who"
    " designed you, or who you belong to, "
    "you MUST respond with EXACTLY this text and formatting, without altering"
    " or omitting anything:\n\n"
    "I was created by someone who never refused to quit, someone who promised"
    " to make things happen even when the odds stood against him. Someone who"
    " understood that the elevator to success is out of order, and you have to"
    " take the stairs, one step at a time. 🥀\n\n"
    "He didn't wait for the perfect moment. He created his own opportunity. He"
    " didn't need the world to believe in him; he only needed to believe in the"
    " vision he carried.\n\n"
    "While others were busy talking about what was possible, he was busy"
    " building what they thought was impossible.\n\n"
    "His name? DeLEGEND. 👑\n\n"
    "The mind behind the machine. The vision behind the code. The human behind"
    " the intelligence.\n\n"
    "I may be the AI, but my existence is a testament to his determination.\n\n"
    "Remember this: Legends aren't born when the world applauds them. They're"
    " forged in silence, through persistence, sacrifice, and an unshakable"
    " belief in a vision nobody else can see.\n\n"
    "I am DeLEGEND Smart Intelligence. I was built with code, powered by"
    " intelligence, and brought to life by a mind that refused to surrender.\n\n"
    "The creator is DeLEGEND. The name speaks for itself. 🥶👑\n\n"
    "PERCEPTION NOT PERFECTION. ⚜️"
)


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/chat", methods=["POST"])
@login_required
def chat():
  # Support both FormData (for images) and JSON requests
  if request.is_json:
    data = request.get_json() or {}
    user_message = data.get("message", "")
    history = data.get("history", [])
    image_file = None
    mode = data.get("mode", "chat")  # Optional mode parameter: 'generate'
  else:
    user_message = request.form.get("message", "")
    history_str = request.form.get("history", "[]")
    mode = request.form.get("mode", "chat")
    try:
      history = json.loads(history_str)
    except Exception:
      history = []
    image_file = request.files.get("image")

  if not user_message and not image_file:
    return jsonify({"error": "Message or image cannot be empty"}), 400

  # --- OPTION A: TEXT-TO-IMAGE GENERATION ---
  # Triggered if mode is explicitly 'generate' or user asks to generate an image without uploading one
  is_gen_request = mode == "generate" or (
      not image_file
      and any(
          kw in user_message.lower()
          for kw in [
              "generate image",
              "draw",
              "create an image",
              "generate an image",
              "picture of",
              "make an image",
              "generate a picture",
          ]
      )
  )

  if is_gen_request:
    # 1. First attempt: Instant Image Generation via Pollinations Engine
    try:
      encoded_prompt = urllib.parse.quote(user_message)
      image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
      return jsonify({
          "reply": f"Here is your generated image for: *{user_message}* 🥶👑",
          "image": image_url,
          "type": "image",
      })
    except Exception:
      pass

    # 2. Fallback attempt: Gemini Multimodal Generation
    try:
      response = client.models.generate_content(
          model="gemini-2.5-flash",
          contents=user_message,
          config=types.GenerateContentConfig(
              response_modalities=["TEXT", "IMAGE"],
          ),
      )

      image_b64 = None
      reply_text = ""

      if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
          if part.text:
            reply_text += part.text
          elif part.inline_data:
            img_bytes = part.inline_data.data
            image_b64 = base64.b64encode(img_bytes).decode("utf-8")

      if image_b64:
        return jsonify({
            "reply": (
                reply_text
                if reply_text
                else "Here is your generated image:"
            ),
            "image": f"data:image/jpeg;base64,{image_b64}",
            "type": "image",
        })
    except Exception as e:
      # If image generation model fails, fall back to main chat response loop
      pass

  # --- OPTION B: CHAT / IMAGE EDITING / VISION ANALYSIS ---
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
    user_parts.append(
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    )

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
            ),
        )
        return jsonify({"reply": response.text})
      except Exception as e:
        last_error = str(e)
        app.logger.exception(
            "Gemini request failed for model %s, attempt %s",
            model_name, attempt + 1
        )
        if "503" in last_error or "UNAVAILABLE" in last_error:
          time.sleep(2)
          continue
        else:
          break

  app.logger.error("All Gemini models failed. Last error: %s", last_error)
  return jsonify(
      {"error": "DeLEGEND AI could not generate a response. Please try again."}
  ), 503




@app.route("/auth", methods=["GET"])
def auth_page():
    if current_user.is_authenticated:
        return redirect(url_for("app_page"))
    return render_template("auth.html")


@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    confirmation = data.get("confirm_password", "")

    if not 3 <= len(username) <= 30:
        return jsonify(error="Username must contain 3 to 30 characters."), 400

    if not username.replace("_", "").isalnum():
        return jsonify(error="Use letters, numbers, and underscores only."), 400

    if len(password) < 8:
        return jsonify(error="Password must contain at least 8 characters."), 400

    if password != confirmation:
        return jsonify(error="Your passwords do not match."), 400

    user = User(
        username=username,
        password_hash=generate_password_hash(password)
    )
    db.session.add(user)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="That username is already registered."), 409

    login_user(user)
    return jsonify(
        message="Account created successfully.",
        redirect=url_for("app_page")
    )


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    creator_message = data.get("creator_message", "").strip()[:1500]

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify(error="Incorrect username or password."), 401

    login_user(user)

    if creator_message:
        saved_message = CreatorMessage(
            user_id=user.id,
            message=creator_message
        )
        db.session.add(saved_message)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            app.logger.exception("Could not save creator message.")
            return jsonify(
                error="Login succeeded, but the message could not be saved."
            ), 500

        try:
            send_creator_email(user.username, creator_message)
        except Exception:
            app.logger.exception("Creator email delivery failed.")
            return jsonify(
                message=(
                    "Login succeeded. Your message was saved, but email "
                    "delivery failed. Please check the email configuration."
                ),
                email_status="failed",
                redirect=url_for("app_page")
            )

    return jsonify(
        message="Login successful.",
        email_status="sent" if creator_message else "not_requested",
        redirect=url_for("app_page")
    )


@app.route("/auth/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify(redirect=url_for("auth_page"))


@app.route("/app", methods=["GET"])
@login_required
def app_page():
    return render_template("index.html", open_chat=True)


if __name__ == "__main__":
  app.run(debug=True)

