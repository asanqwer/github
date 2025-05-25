from db import predictions_col
from utils import get_latest_period, random_prediction
import os
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
REGISTER_LINK = os.getenv("REGISTER_LINK")

def send_prediction():
    latest_period = get_latest_period()
    if not latest_period:
        return

    # Check if already predicted
    if predictions_col.find_one({"period": latest_period}):
        return

    choice = random_prediction()

    message = (
        f"[ WINGO 1 MINUTE ]\n"
        f"🌀 Period: {latest_period}\n"
        f"🧿 Choose - {choice}\n"
        f"📑 Read /howtobet before you proceed!\n"
        f"🔗 [Register Here]({REGISTER_LINK})"
    )

    bot.send_message(chat_id=GROUP_CHAT_ID, text=message, parse_mode="Markdown")
    predictions_col.insert_one({"period": latest_period, "choice": choice})
