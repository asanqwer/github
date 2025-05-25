import os
import random
import requests
import threading
import time
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, CallbackContext
from telegram.ext import MessageHandler, Filters
from db import users_col, status_col, predictions_col
from prediction import send_prediction
from utils import STICKERS, determine_win, get_result_for_period
from queue import Queue

load_dotenv()

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

update_queue = Queue()
dispatcher = Dispatcher(bot, update_queue, use_context=True)

@app.route("/")
def index():
    return "Bot is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

def start(update, context):
    user = update.effective_user
    chat_id = user.id
    if not users_col.find_one({"user_id": chat_id}):
        users_col.insert_one({"user_id": chat_id, "balance": 100, "bets": []})
        update.message.reply_text("Welcome! You've been registered with ₹100 balance.")
    else:
        update.message.reply_text("Welcome back!")

def profile(update, context):
    user = update.effective_user
    u = users_col.find_one({"user_id": user.id})
    update.message.reply_text(f"💰 Balance: ₹{u['balance']}")

def leaderboard(update, context):
    top = users_col.find().sort("balance", -1).limit(5)
    text = "🏆 Top Players:\n"
    for i, u in enumerate(top, 1):
        text += f"{i}. {u['user_id']} - ₹{u['balance']}\n"
    update.message.reply_text(text)

def check_results_loop():
    while True:
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
                            try:
                                bot.send_sticker(chat_id=user["user_id"], sticker=random.choice(STICKERS))
                            except Exception as e:
                                print(f"Error sending sticker: {e}")

        time.sleep(60)

def prediction_loop():
    while True:
        try:
            send_prediction()
        except Exception as e:
            print(f"Prediction error: {e}")
        time.sleep(60)

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("profile", profile))
dispatcher.add_handler(CommandHandler("leaderboard", leaderboard))

if __name__ == "__main__":
    threading.Thread(target=prediction_loop, daemon=True).start()
    threading.Thread(target=check_results_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
