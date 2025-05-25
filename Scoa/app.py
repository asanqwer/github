import os
import json
import random
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Example: https://your-service-name.onrender.com

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0, use_context=True)

stickers = [
    "CAACAgQAAxkBAAKmh2f5EBjXCvSqjGVYDT9P7yjKW6_IAAKOCAACi9XoU5p5sAokI77kNgQ",
    "CAACAgQAAxkBAAKmimf5EB9GTlXRtwVB3ez1nBUKzf69AAKaDAACfx_4UvcUEDj6i_r9NgQ",
    "CAACAgQAAxkBAAKmjWf5ECecZUCJtSeuqsaaVWILpTuyAALICwACG86YUDSKklgR_M5FNgQ",
    "CAACAgIAAxkBAAKmkGf5EDBgwnSDovUPpQGsTjMQdU69AAL4DAACNyx5S6FYW3VBcuj4NgQ"
]

def get_latest_period():
    try:
        url = "https://api.51gameapi.com/api/webapi/GetNoaverageEmerdList"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json",
            "Authorization": "Bearer YOUR_TOKEN_HERE"  # If needed
        }
        payload = {
            "pageSize": 10,
            "pageNo": 1,
            "typeId": 1,
            "language": 0,
            "random": "6fadc24ccf2c4ed4afb5a1a5f84d2ba4",
            "signature": "4E071E587A80572ED6065D6F135F3ABE",
            "timestamp": 1733117040
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        data = response.json()
        return int(data["data"]["list"][0]["issueNumber"]) + 1
    except Exception as e:
        print(f"[ERROR] API failed: {e}")
        return None

def get_random_prediction():
    return random.choice(["Big", "Small"])

def send_prediction():
    period = get_latest_period()
    if not period:
        print("[ERROR] No period received")
        return

    prediction = get_random_prediction()
    message = (
        f"[WINGO 1MINUTE]\n"
        f"Period {period}\n"
        f"Choose - {prediction}\n"
        f"📑 Read /howtobet before you proceed!\n"
        f"🔗 https://www.18sikkim.com/#/register?invitationCode=643745098970"
    )

    try:
        bot.send_message(chat_id=GROUP_CHAT_ID, text=message)
        if random.random() < 0.5:
            bot.send_sticker(chat_id=GROUP_CHAT_ID, sticker=random.choice(stickers))
    except Exception as e:
        print(f"[ERROR] Send failed: {e}")

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Bot is live and ready.")

dispatcher.add_handler(CommandHandler("start", start))

@app.route("/")
def home():
    return "✅ Bot is running on webhook!"

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
    return "OK"

# Schedule predictions every 1 minute
scheduler = BackgroundScheduler()
scheduler.add_job(send_prediction, 'interval', minutes=1)
scheduler.start()

if __name__ == "__main__":
    bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
