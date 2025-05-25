import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGODB_URI"))
db = client["Telegrambot1"]

users_col = db["users"]
predictions_col = db["predictions"]
bets_col = db["bets"]
status_col = db["status"]
