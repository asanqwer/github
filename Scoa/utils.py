import random 
import requests

STICKERS = [
    "CAACAgUAAxkBAAEBVZhmZAgqBQr9vC-lxZyovIVrFj2QzwAC1QEAAvcCyVfvvOK9zdcZlS8E",
    "CAACAgUAAxkBAAEBVZpmZAgzpWTAl95McAABLuIT6kFaOiLJwHgcAAJdAQACq7soV6I_H6lZfJQvBA",
    "CAACAgUAAxkBAAEBVZxmZAg0NoA7X0NDLczKDoIuzR2RiwACFgEAAjrCyFeoz8ML-FKO0y8E",
]

def get_latest_period():
    try:
        res = requests.get("https://api.51gameapi.com/api/webapi/GetNoaverageEmerdList", timeout=5)
        data = res.json()
        return data["data"][0]["period"]
    except Exception as e:
        print(f"Error fetching latest period: {e}")
        return None

def get_result_for_period(period):
    try:
        res = requests.get("https://api.51gameapi.com/api/webapi/GetNoaverageEmerdList", timeout=5)
        data = res.json()
        for item in data["data"]:
            if item["period"] == period:
                return int(item["number"])
        return None
    except Exception as e:
        print(f"Error fetching result for period {period}: {e}")
        return None

def random_prediction():
    return random.choice(["Big", "Small"])

def determine_win(prediction, result):
    if result is None:
        return False
    if prediction == "Big" and result >= 5:
        return True
    if prediction == "Small" and result <= 4:
        return True
    return False
