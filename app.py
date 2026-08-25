from flask import Flask, request
import os
import requests
from google import genai
import traceback

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

print("===== APP STARTED =====")
print("GEMINI_API_KEY set:", bool(GEMINI_API_KEY))
print("WHATSAPP_ACCESS_TOKEN set:", bool(WHATSAPP_ACCESS_TOKEN))
print("PHONE_NUMBER_ID set:", bool(PHONE_NUMBER_ID))
print("PHONE_NUMBER_ID value:", PHONE_NUMBER_ID)

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
    print("\n\n========== NEW WEBHOOK REQUEST ==========")
    data = request.get_json()
    print("Full data:", data)

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            print("→ Status update aaya, ignore kar raha hoon")
            return "OK", 200

        message = value["messages"][0]
        sender = message["from"]
        msg_type = message.get("type")

        print("Sender:", sender)
        print("Type:", msg_type)

        if msg_type != "text":
            print("→ Text message nahi hai, ignore")
            return "OK", 200

        user_message = message["text"]["body"]
        print("User message:", user_message)

        print("→ Gemini ko bhej raha hoon...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_message
        )

        answer = response.text
        print("Gemini ka jawab:", answer)

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

        print("→ WhatsApp pe bhej raha hoon...")
        result = requests.post(url, headers=headers, json=payload, timeout=20)

        print("WhatsApp Status Code:", result.status_code)
        print("WhatsApp Response Body:", result.text)

    except Exception as e:
        print("!!!!!!!!!! ERROR !!!!!!!!!!")
        print(str(e))
        traceback.print_exc()

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
