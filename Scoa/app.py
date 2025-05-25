import os
import random
import requests
import logging
import threading
import time
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
from telegram.utils.request import Request
from queue import Queue

from db import users_col, status_col, predictions_col
from prediction import send_prediction
from utils import STICKERS, determine_win, get_result_for_period

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = "https://sikkimbot.onrender.com/webhook"  # Update this to your Render domain + /webhook

bot = Bot(token=BOT_TOKEN, request=Request(con_pool_size=8))
update_queue = Queue()
dispatcher = Dispatcher(bot, update_queue, workers=4, use_context=True)

@app.route("/")
def index():
    return "🤖 SikkimBot is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    response = requests.post(url, data={"url": WEBHOOK_URL})
    if response.status_code == 200:
        logging.info("✅ Webhook set successfully")
    else:
        logging.error(f"❌ Failed to set webhook: {response.text}")

def start(update, context: CallbackContext):
    user = update.effective_user
    chat_id = user.id
    if not users_col.find_one({"user_id": chat_id}):
        users_col.insert_one({"user_id": chat_id, "balance": 100, "bets": []})
        update.message.reply_text("✅ Welcome! You've been registered with ₹100 balance.")
    else:
        update.message.reply_text("👋 Welcome back!")

def profile(update, context: CallbackContext):
    user = update.effective_user
    u = users_col.find_one({"user_id": user.id})
    update.message.reply_text(f"💰 Balance: ₹{u['balance']}")

def leaderboard(update, context: CallbackContext):
    top = users_col.find().sort("balance", -1).limit(5)
    text = "🏆 Top Players:\n"
    for i, u in enumerate(top, 1):
        text += f"{i}. {u['user_id']} - ₹{u['balance']}\n"
    update.message.reply_text(text)

# Background job to check win/loss results
def check_results_loop():
    while True:
        try:
            last = predictions_col.find().sort("period", -1).limit(1)
            for p in last:
                period = p["period"]
                result = get_result_for_period(period)
                if result is None:
                    continue

                for user in users_col.find():
                    for b in user.get("bets", []):
                        if b["period"] == period:
                            win = determine_win(b["choice"], result)
                            amount = b["amount"]
                            new_bal = user["balance"] + amount if win else user["balance"] - amount
                            users_col.update_one({"user_id": user["user_id"]}, {"$set": {"balance": new_bal}})
                            if win:
                                bot.send_sticker(chat_id=user["user_id"], sticker=random.choice(STICKERS))
        except Exception as e:
            logging.error(f"[check_results_loop] Error: {e}")
        time.sleep(60)

# Background job to send predictions
def prediction_loop():
    while True:
        try:
            send_prediction()
        except Exception as e:
            logging.error(f"[prediction_loop] Error: {e}")
        time.sleep(60)

# Telegram Handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("profile", profile))
dispatcher.add_handler(CommandHandler("leaderboard", leaderboard))

if __name__ == "__main__":
    threading.Thread(target=prediction_loop).start()
    threading.Thread(target=check_results_loop).start()
    
    # Set webhook only on deploy (prevent multiple set calls)
    if os.getenv("FLASK_ENV") != "development":
        set_webhook()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
