import asyncio
import re
import logging
import os
from flask import Flask, request, jsonify
from telethon import TelegramClient, errors

# ─── Environment Variables ──────────────────────────────────────────────
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")
BRIDGE_SECRET = os.getenv("BRIDGE_SECRET", "mysecret123")
SESSION_NAME = "session_bomber"

# ⚠️ YAHAN BOT KA USERNAME DAALO (bina @ ke)
BOT_USERNAME = "THAKUR_BOMBER_BOT"

# ─── Setup ──────────────────────────────────────────────────────────────
app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# ─── Login Function ─────────────────────────────────────────────────────
async def do_login():
    """Telegram mein login karo. Pehli baar OTP mangega."""
    await client.connect()
    if not await client.is_user_authorized():
        print("\n" + "="*50)
        print("  📱 TELEGRAM LOGIN REQUIRED!")
        print("="*50)
        print(f"  📱 OTP bheja ja raha hai {PHONE_NUMBER} pe...")
        print("  👇 Neeche 'Input' button se OTP daalo")
        print("="*50 + "\n")
        await client.send_code_request(PHONE_NUMBER)
        code = input().strip()  # Railway ke Input button se aayega
        try:
            await client.sign_in(PHONE_NUMBER, code)
            print("✅ Login successful!")
        except errors.SessionPasswordNeededError:
            print("🔒 2FA password daalo (neeche Input mein):")
            pwd = input().strip()
            await client.sign_in(password=pwd)
            print("✅ Login with 2FA successful!")
    else:
        print("✅ Already logged in!")

# ─── Button Click Function ─────────────────────────────────────────────
async def click_button(bot, button_text):
    """Bot ke message mein inline button dhoondh kar click karega."""
    async for msg in client.iter_messages(bot, limit=10):
        if not msg.buttons:
            continue
        for row in msg.buttons:
            for btn in row:
                if button_text.lower() in btn.text.lower():
                    logger.info(f"🖱️ Clicking: {btn.text}")
                    await btn.click()
                    return True
    return False

# ─── Bot Last Response ─────────────────────────────────────────────────
async def get_bot_response(bot):
    """Bot ka last incoming message return karega."""
    async for msg in client.iter_messages(bot, limit=3):
        if not msg.outgoing and msg.text:
            return msg.text
    return "Bot ne koi response nahi diya"

# ─── Attack Function ───────────────────────────────────────────────────
async def start_attack(number):
    """Poore attack ka flow yahan hai."""
    # Pehle login check
    await do_login()
    
    # Number clean karo
    num = re.sub(r'[\s\-\+\(\)]', '', number)
    if len(num) == 10:
        num = f"+91{num}"
    elif len(num) == 12 and num.startswith("91"):
        num = f"+{num}"
    
    logger.info(f"🎯 Target: {num}")
    
    # Bot dhoondho
    bot = await client.get_entity(BOT_USERNAME)
    
    # Step 1: /menu bhejo
    logger.info("📤 Sending /menu")
    await client.send_message(bot, "/menu")
    await asyncio.sleep(2)
    
    # Step 2: "START BOMB" button click karo
    logger.info("🖱️ Looking for START BOMB button")
    clicked = await click_button(bot, "START BOMB")
    if not clicked:
        return {"status": "failed", "error": "START BOMB button nahi mila"}
    
    await asyncio.sleep(2)
    
    # Step 3: Number bhejo
    logger.info(f"📤 Sending number: {num}")
    await client.send_message(bot, num)
    await asyncio.sleep(2)
    
    # Step 4: Bot ka response lao
    response = await get_bot_response(bot)
    logger.info(f"📩 Bot: {response[:100]}")
    
    return {
        "status": "success",
        "target": num,
        "bot_response": response
    }

# ─── API Route ─────────────────────────────────────────────────────────
@app.route("/", methods=["POST"])
def handle_request():
    """CF Worker se request aayegi yahan."""
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "JSON nahi mila"}), 400
    
    if data.get("secret") != BRIDGE_SECRET:
        return jsonify({"error": "Secret galat hai"}), 403
    
    action = data.get("action")
    number = data.get("number")
    
    if action != "bomb" or not number:
        return jsonify({"error": "Action ya number nahi hai"}), 400
    
    if not re.match(r'^\d{10,15}$', number):
        return jsonify({"error": "Number format galat hai"}), 400
    
    try:
        result = asyncio.run(start_attack(number))
        return jsonify(result)
    except Exception as e:
        logger.exception("❌ Attack failed")
        return jsonify({"status": "failed", "error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"service": "Bomber Bridge", "status": "running"})

# ─── Yeh ab MODULE LEVEL pe chalega (gunicorn ke saath kaam karega) ────
print("="*50)
print("  🔥 BRIDGE SERVER STARTING...")
print("="*50)

# Login ab yahan hota hai - module load hote hi
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(do_login())

print("🚀 Server ready on port 8080!")
