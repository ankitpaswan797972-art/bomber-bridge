import asyncio, re, logging, os
from flask import Flask, request, jsonify
from telethon import TelegramClient, errors

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")
BRIDGE_SECRET = os.getenv("BRIDGE_SECRET", "mysecret123")
BOT_USERNAME = "THAKUR_BOMBER_BOT"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = TelegramClient("session_bomber", API_ID, API_HASH)

async def do_login():
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE_NUMBER)
        code = input("OTP: ")
        try:
            await client.sign_in(PHONE_NUMBER, code)
        except errors.SessionPasswordNeededError:
            pwd = input("2FA: ")
            await client.sign_in(password=pwd)

async def start_attack(number):
    await do_login()
    num = re.sub(r'[\s\-\+\(\)]', '', number)
    if len(num) == 10: num = f"+91{num}"
    elif len(num) == 12 and num.startswith("91"): num = f"+{num}"
    
    bot = await client.get_entity(BOT_USERNAME)
    await client.send_message(bot, "/menu")
    await asyncio.sleep(2)
    
    async for msg in client.iter_messages(bot, limit=10):
        if msg.buttons:
            for row in msg.buttons:
                for btn in row:
                    if "START" in btn.text.upper():
                        await btn.click()
                        break
                else: continue
                break
        break
    
    await asyncio.sleep(2)
    await client.send_message(bot, num)
    await asyncio.sleep(2)
    
    async for msg in client.iter_messages(bot, limit=2):
        if not msg.outgoing and msg.text:
            return {"status": "success", "target": num, "bot_response": msg.text}
    return {"status": "success", "target": num, "bot_response": "Sent"}

@app.route("/", methods=["POST"])
def handle():
    data = request.get_json(force=True, silent=True)
    if not data or data.get("secret") != BRIDGE_SECRET:
        return jsonify({"error": "Unauthorized"}), 403
    if data.get("action") != "bomb" or not data.get("number"):
        return jsonify({"error": "Invalid"}), 400
    try:
        return jsonify(asyncio.run(start_attack(data["number"])))
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"service": "Bomber Bridge", "status": "running"})

if __name__ == "__main__":
    asyncio.run(do_login())
    app.run(host="0.0.0.0", port=8080)
