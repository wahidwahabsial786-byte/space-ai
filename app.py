
from flask import Flask, request
import os
import requests
from google import genai

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

client = genai.Client(api_key=GEMINI_API_KEY)

VERIFY_TOKEN = "space_ai_verify_2026"


@app.route("/")
def home():
    return "Space AI is running successfully!"


@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Verification failed", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = message["from"]
        user_message = message["text"]["body"]

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message
        )

        answer = response.text

        url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"

        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": sender,
            "type": "text",
            "text": {
                "body": answer
            }
        }

        result = requests.post(url, headers=headers, json=payload)

print("WhatsApp status:", result.status_code)
print("WhatsApp response:", result.text)

    except Exception as e:
        print("Error:", e)

    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
