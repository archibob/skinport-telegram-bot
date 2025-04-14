import requests
import time
from telegram import Bot

# Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
MAX_PRICE = 300  # максимум в € для Talon

bot = Bot(token=TELEGRAM_BOT_TOKEN)

def check_items():
    url = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"
    response = requests.get(url)
    items = response.json()

    found = False

    for item in items:
        name = item.get("market_hash_name", "")
        price = item.get("min_price", 0)

        if "Talon Knife" in name and price and price < MAX_PRICE:
            found = True
            message = f"🔪 Найден {name} за {price}€ на Skinport!\nСсылка: https://skinport.com/item/{item.get('item_id')}"
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

    if not found:
        print("❌ Подходящих предметов не найдено.")

def run_monitor():
    while True:
        try:
            print("🔍 Проверка предметов...")
            check_items()
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
        time.sleep(300)  # ждать 5 минут

if __name__ == "__main__":
    run_monitor()
