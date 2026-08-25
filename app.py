from flask import Flask, request
import os
import requests
from google import genai
import traceback

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

print("===== APP STARTED =====", flush=True)
print("GEMINI_API_KEY set:", bool(GEMINI_API_KEY), flush=True)
print("WHATSAPP_ACCESS_TOKEN set:", bool(WHATSAPP_ACCESS_TOKEN), flush=True)
print("PHONE_NUMBER_ID set:", bool(PHONE_NUMBER_ID), flush=True)
print("PHONE_NUMBER_ID value:", PHONE_NUMBER_ID, flush=True)

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
    print("\n\n========== NEW WEBHOOK REQUEST ==========", flush=True)
    data = request.get_json()
    print("Full data:", data, flush=True)

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            print("→ Status update aaya, ignore", flush=True)
            return "OK", 200

        message = value["messages"][0]
        sender = message["from"]
        msg_type = message.get("type")

        print("Sender:", sender, flush=True)
        print("Type:", msg_type, flush=True)

        if msg_type != "text":
            print("→ Text nahi hai, ignore", flush=True)
            return "OK", 200

        user_message = message["text"]["body"]
        print("User message:", user_message, flush=True)

        print("→ Gemini ko bhej raha hoon...", flush=True)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message
        )

        answer = response.text
        print("Gemini ka jawab:", answer, flush=True)

        url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": sender,
            "type": "text",
            "text": {"body": answer}
        }

        print("→ WhatsApp pe bhej raha hoon...", flush=True)
        result = requests.post(url, headers=headers, json=payload, timeout=20)

        print("WhatsApp Status Code:", result.status_code, flush=True)
        print("WhatsApp Response Body:", result.text, flush=True)

    except Exception as e:
        print("!!!!!!!!!! ERROR !!!!!!!!!!", flush=True)
        print(str(e), flush=True)
        traceback.print_exc()

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
