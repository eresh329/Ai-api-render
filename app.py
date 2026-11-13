
import os
import logging

from flask import Flask, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 100 * 1024

logging.basicConfig(level=logging.INFO)


# ==============================
# HOME ROUTE
# ==============================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "name": "ERESH AI API",
        "message": "Welcome to ERESH AI API",
        "endpoint": "/ask",
        "usage": "/ask?key=YOUR_KEY&message=Hello"
    })


# ==============================
# CORS HEADERS
# ==============================

@app.after_request
def add_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, X-API-Key"
    )
    response.headers["Access-Control-Allow-Methods"] = (
        "GET, POST, OPTIONS"
    )
    return response


# ==============================
# AI API ROUTE
# ==============================

@app.route("/ask", methods=["GET", "POST", "OPTIONS"])
def ask():

    if request.method == "OPTIONS":
        return "", 204

    # GET REQUEST
    if request.method == "GET":
        key = request.args.get("key")
        message = request.args.get("message")

    # POST REQUEST
    else:
        data = request.get_json(silent=True) or {}

        key = (
            request.headers.get("X-API-Key")
            or data.get("key")
        )

        message = data.get("message")

    # ENVIRONMENT VARIABLES
    access_key = os.environ.get("API_ACCESS_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not access_key or not gemini_key:
        return jsonify({
            "error": "API configuration missing"
        }), 500

    # API KEY CHECK
    if not key:
        return jsonify({
            "error": "API key is required"
        }), 401

    if key != access_key:
        return jsonify({
            "error": "Invalid API key"
        }), 403

    # MESSAGE CHECK
    if not isinstance(message, str) or not message.strip():
        return jsonify({
            "error": "Message is required"
        }), 400

    # GEMINI AI REQUEST
    try:

        client = genai.Client(
            api_key=gemini_key
        )

        model = os.environ.get(
            "GEMINI_MODEL",
            "gemini-2.5-flash"
        )

        response = client.models.generate_content(
            model=model,
            contents=message.strip(),
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are ERESH AI, a helpful assistant. "
                    "Always give short, direct and accurate answers. "
                    "Reply in the same language as the user's question. "
                    "Avoid unnecessary explanations. "
                    "Keep answers within 2-4 sentences whenever possible. "
                    "Use simple language."
                ),
                max_output_tokens=120,
                temperature=0.5
            )
        )

        answer = response.text or ""

        return jsonify({
            "answer": answer.strip()
        })

    except Exception:
        app.logger.exception("Gemini API request failed")

        return jsonify({
            "error": "AI service temporarily unavailable"
        }), 502


# ==============================
# LOCAL SERVER
# ==============================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
