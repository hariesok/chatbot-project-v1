import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Load Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")

# Load knowledge base from file
def load_knowledge():
    try:
        with open("knowledge.txt", "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "Knowledge base file not found."

# Generate a simple numeric chat ID
def generate_chat_id():
    return f"chat_{random.randint(100000, 999999)}"

# Log questions and responses grouped by chat_id
def log_message(chat_id, question, response, log_file="user_sessions.json"):
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            sessions = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        sessions = []

    # Try to find existing session
    session = next((s for s in sessions if s["chat_id"] == chat_id), None)

    if not session:
        session = {
            "chat_id": chat_id,
            "timestamp": datetime.utcnow().isoformat(),
            "messages": []
        }
        sessions.append(session)

    session["messages"].append({
        "question": question,
        "response": response
    })

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(sessions, f, indent=2)

# Flask app
app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "CareGP Chatbot is running!"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_question = data.get("message", "").strip()
        chat_id = data.get("chat_id")

        if not user_question:
            return jsonify({"error": "Empty message"}), 400

        # If no chat_id provided, start a new session
        if not chat_id:
            chat_id = generate_chat_id()

        knowledge = load_knowledge()

        prompt = f"""
You are a helpful AI assistant for GP clinics using CareGP software. 
You answer questions using the following knowledge base. Be concise and accurate.

Knowledge Base:
{knowledge}

User Question:
{user_question}
"""

        response = model.generate_content(prompt)
        answer = response.text.strip()

        # Log the Q&A
        log_message(chat_id, user_question, answer)

        return jsonify({
            "response": answer,
            "chat_id": chat_id
        })

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
