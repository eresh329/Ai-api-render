
import os
from flask import Flask, request, jsonify
from google import genai

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 100 * 1024

@app.after_request
def add_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": True,
        "name": "ERESH AI API",
        "message": "Welcome to ERESH AI API",
        "endpoint": "/ask",
        "usage": "/ask?key=YOUR_KEY&message=Hello"
    })


@app.route("/ask", methods=["GET", "POST", "OPTIONS"])
def ask():

    if request.method == "OPTIONS":
        return "", 204

    if request.method == "GET":
        key = request.args.get("key")
        message = request.args.get("message")
    else:
        data = request.get_json(silent=True) or {}
        key = request.headers.get("X-API-Key") or data.get("key")
        message = data.get("message")

    access_key = os.environ.get("API_ACCESS_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")

    if not access_key or not gemini_key:
        return jsonify({
            "status": False,
            "error": "API configuration missing"
        }), 500

    if not key:
        return jsonify({
            "status": False,
            "error": "API key is required"
        }), 401

    if key != access_key:
        return jsonify({
            "status": False,
            "error": "Invalid API key"
        }), 403

    if not isinstance(message, str) or not message.strip():
        return jsonify({
            "status": False,
            "error": "Message is required"
        }), 400

    try:
        client = genai.Client(api_key=gemini_key)

        model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

        response = client.models.generate_content(
            model=model,
            contents=message.strip()
        )

        return jsonify({
            "status": True,
            "creator": "ERESH",
            "model": model,
            "response": response.text or ""
        })

    except Exception:
        app.logger.exception("Gemini API request failed")
        return jsonify({
            "status": False,
            "error": "AI service temporarily unavailable"
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
