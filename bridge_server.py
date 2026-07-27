import asyncio
import re
import logging
import os
import threading
from flask import Flask, request, jsonify
from telethon import TelegramClient

# Render se Environment Variables lena
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BRIDGE_SECRET = os.getenv("BRIDGE_SECRET", "mysecret123")
BOT_USERNAME = "THAKUR_BOMBER_BOT"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🟢 Ek hi background loop banega jab app start hoga
_bg_loop = asyncio.new_event_loop()
_bg_thread = threading.Thread(target=_bg_loop.run_forever, daemon=True)
_bg_thread.start()

# 🟢 Client isi loop pe lock hoga
_client = TelegramClient("session_bomber", API_ID, API_HASH, loop=_bg_loop)

def run_async(coro):
    """Flask (sync) se Telethon (async) ko safely call karne ka rasta"""
    future = asyncio.run_coroutine_threadsafe(coro, _bg_loop)
    return future.result(timeout=120)

async def do_login():
    if not _client.is_connected():
        await _client.connect()
    if await _client.is_user_authorized():
        logger.info("✅ Session valid")
        return True
    logger.error("❌ Session invalid/expired")
    return False

async def start_attack(number):
    num = re.sub(r'[\s\-\+\(\)]', '', number)
    if len(num) == 10:
        num = f"+91{num}"
    elif len(num) == 12 and num.startswith("91"):
        num = f"+{num}"

    bot = await _client.get_entity(BOT_USERNAME)
    await _client.send_message(bot, "/menu")
    await asyncio.sleep(2)

    async for msg in _client.iter_messages(bot, limit=10):
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
        break

    await asyncio.sleep(2)
    await _client.send_message(bot, num)
    await asyncio.sleep(2)

    async for msg in _client.iter_messages(bot, limit=2):
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
        ok = run_async(do_login())
        if not ok:
            return jsonify({"status": "failed", "error": "Session expired. Re-login via Console."}), 401
        result = run_async(start_attack(data["number"]))
        return jsonify(result)
    except Exception as e:
        logger.exception("Attack failed")
        return jsonify({"status": "failed", "error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"service": "Bomber Bridge", "status": "running"})

if __name__ == "__main__":
    # Local testing ke liye
    app.run(host="0.0.0.0", port=8080, threaded=False)
