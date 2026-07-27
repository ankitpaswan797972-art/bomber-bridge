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

# Global event loop — ek hi loop pure app mein chalega
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

client = TelegramClient("session_bomber", API_ID, API_HASH)

async def do_login():
    """Login without interactive input — session file should already exist."""
    await client.connect()
    if await client.is_user_authorized():
        logger.info("Session already valid")
        return True
    logger.error("Session invalid or expired")
    return False

async def start_attack(number):
    logged_in = await do_login()
    if not logged_in:
        return {"status": "failed", "error": "Session expired. Re-login manually via Railway Console."}

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
        # ✅ Use the SAME event loop — NOT asyncio.run()
        result = loop.run_until_complete(start_attack(data["number"]))
        return jsonify(result)
    except Exception as e:
        logger.exception("Attack failed")
        return jsonify({"status": "failed", "error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"service": "Bomber Bridge", "status": "running"})

# ✅ Startup: connect on the same loop
ok = loop.run_until_complete(do_login())
if not ok:
    logger.warning("Session not ready. Run manual login in Railway Console.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
