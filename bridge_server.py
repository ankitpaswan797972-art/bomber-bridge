import re
import logging
import os
import time
from flask import Flask, request, jsonify
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
BRIDGE_SECRET = os.getenv("BRIDGE_SECRET", "mysecret123")
BOT_USERNAME = "THAKUR_BOMBER_BOT"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_client = None

def get_client():
    global _client
    if _client is None:
        if SESSION_STRING:
            # String Session use karenge
            _client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        else:
            _client = TelegramClient("session_bomber", API_ID, API_HASH)
    return _client

@app.route("/", methods=["POST"])
def handle():
    data = request.get_json(force=True, silent=True)
    if not data or data.get("secret") != BRIDGE_SECRET:
        return jsonify({"error": "Secret galat hai"}), 403
    if data.get("action") != "bomb" or not data.get("number"):
        return jsonify({"error": "Sahi number daal bhai"}), 400
    try:
        client = get_client()
        client.connect()
        if not client.is_user_authorized():
            return jsonify({"status": "failed", "error": "Session expired."}), 401

        number = data["number"]
        num = re.sub(r'[\s\-\+\(\)]', '', number)
        if len(num) == 10:
            num = f"+91{num}"
        elif len(num) == 12 and num.startswith("91"):
            num = f"+{num}"

        bot = client.get_entity(BOT_USERNAME)
        client.send_message(bot, "/menu")
        time.sleep(2)

        # Sync mode me iter_messages ki jagah get_messages use hota hai
        msgs = client.get_messages(bot, limit=10)
        for msg in msgs:
            if msg.buttons:
                for row in msg.buttons:
                    for btn in row:
                        if "START" in btn.text.upper():
                            btn.click()
                            break
                    else:
                        continue
                    break
                break
            break

        time.sleep(2)
        client.send_message(bot, num)
        time.sleep(2)

        msgs = client.get_messages(bot, limit=2)
        for msg in msgs:
            if not msg.outgoing and msg.text:
                return jsonify({"status": "success", "target": num, "bot_response": msg.text})
        
        return jsonify({"status": "success", "target": num, "bot_response": "Sent"})
    except Exception as e:
        logger.exception("Attack failed")
        return jsonify({"status": "failed", "error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"service": "Bomber Bridge", "status": "running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=False)
