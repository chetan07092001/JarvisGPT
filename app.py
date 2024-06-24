import logging
import os
import requests
from flask import Flask, render_template, session, request, jsonify
from flask_session import Session
from PyPDF2 import PdfReader
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Configuring server-side session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Load OpenAI API key
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    logger.error("OPENAI_API_KEY environment variable not set")
else:
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {openai_api_key}"}

def format_message_history(history):
    formatted_history = []
    for msg in history:
        if 'user' in msg:
            formatted_history.append({"role": "user", "content": msg['user']})
        elif 'bot' in msg:
            formatted_history.append({"role": "assistant", "content": msg['bot']})
    return formatted_history

@app.route("/")
def root_route():
    return render_template("template.html")

@app.route("/send_message", methods=['POST'])
def send_message():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"message": "No message provided"}), 400

    logger.info(f"User message: {user_message}")

    if 'history' not in session:
        session['history'] = []

    session['history'].append({"user": user_message})

    if len(session['history']) > 10:
        session['history'] = session['history'][-10:]

    conversation_history = format_message_history(session['history'])
    if not conversation_history:
        conversation_history = [{"role": "system", "content": "You are a helpful assistant."}]

    try:
        request_data = {
            "model": "gpt-4",
            "messages": conversation_history,
            "temperature": 0.7,
            "max_tokens": 150
        }

        logger.info(f"Request payload: {request_data}")

        response = requests.post(api_url, headers=headers, json=request_data, timeout=30)
        response.raise_for_status()

        response_data = response.json()
        logger.info(f"Response payload: {response_data}")

        bot_response = response_data["choices"][0]["message"]["content"].strip()
        
        # Ensure the bot response is formatted as a code block if it contains code
        if "```" in bot_response:
            bot_response = f"\n```\n{bot_response}\n```"

        session['history'].append({"bot": bot_response})
        return jsonify({"message": bot_response})
    except requests.Timeout:
        logger.error("The request timed out")
        return jsonify({"message": "The request timed out. Please try again."}), 500
    except requests.RequestException as e:
        logger.error(f"Error calling OpenAI API: {e.response.text}")
        return jsonify({"message": "Sorry, something went wrong with the chatbot service."}), 500


@app.route("/upload_file", methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    try:
        if file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(file)
        elif file.filename.endswith('.xlsx'):
            text = extract_text_from_xlsx(file)
        else:
            return jsonify({"message": "Unsupported file type"}), 400

        bot_response = process_text_with_gpt(text)
        return jsonify({"message": bot_response})
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return jsonify({"message": "Error processing file."}), 500

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ''
    for page in reader.pages:
        text += page.extract_text() + "\n\n"
    return text

def extract_text_from_xlsx(xlsx_file):
    df = pd.read_excel(xlsx_file)
    return df.to_string()

def process_text_with_gpt(text):
    request_data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "Format and present the following content appropriately."},
            {"role": "user", "content": text}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    }

    response = requests.post(api_url, headers=headers, json=request_data, timeout=30)
    response.raise_for_status()
    response_data = response.json()
    return response_data["choices"][0]["message"]["content"].strip()


