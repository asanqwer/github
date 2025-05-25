import os
import requests
import json
import random
import pytz
import threading
from telegram import Bot
from telegram.ext import Updater, CommandHandler
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = "-1002609387727"
bot = Bot(token=BOT_TOKEN)

stickers = [
    "CAACAgQAAxkBAAKmh2f5EBjXCvSqjGVYDT9P7yjKW6_IAAKOCAACi9XoU5p5sAokI77kNgQ",
    "CAACAgQAAxkBAAKmimf5EB9GTlXRtwVB3ez1nBUKzf69AAKaDAACfx_4UvcUEDj6i_r9NgQ",
    "CAACAgQAAxkBAAKmjWf5ECecZUCJtSeuqsaaVWILpTuyAALICwACG86YUDSKklgR_M5FNgQ",
    "CAACAgIAAxkBAAKmkGf5EDBgwnSDovUPpQGsTjMQdU69AAL4DAACNyx5S6FYW3VBcuj4NgQ"
]

def get_latest_period():
    url = "https://api.51gameapi.com/api/webapi/GetNoaverageEmerdList"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Accept": "application/json",
        "Authorization": "Bearer YOUR_TOKEN_HERE"  # Replace this
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
    try:
        data = response.json()
        return int(data["data"]["list"][0]["issueNumber"]) + 1
    except:
        return None

def get_random_prediction():
    return random.choice(["Big", "Small"])

def send_prediction():
    period = get_latest_period()
    if not period:
        print("Error fetching period.")
        return

    prediction = get_random_prediction()
    message = f"[WINGO 1MINUTE]\nPeriod {period}\nChoose - {prediction}"
    bot.send_message(chat_id=GROUP_CHAT_ID, text=message)

    if random.random() < 0.5:
        bot.send_sticker(chat_id=GROUP_CHAT_ID, sticker=random.choice(stickers))

    print(f"Sent: {message}")

# APScheduler in separate thread
def start_scheduler():
    scheduler = BlockingScheduler(timezone=pytz.utc)
    scheduler.add_job(send_prediction, 'interval', minutes=1)
    scheduler.start()

# Telegram /start handler
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Running ✅")

updater = Updater(token=BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))

# Run scheduler in background
threading.Thread(target=start_scheduler).start()

# Run bot polling
updater.start_polling()