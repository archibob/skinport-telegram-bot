import requests
import time
import re

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Ключевые слова и максимальные цены (в евро)
ITEMS_PRICE_LIMITS = {
    "Talon Knife": 300
}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("Ошибка отправки в Telegram:", response.text)
    except Exception as e:
        print("Ошибка Telegram:", e)

def check_items():
    try:
        headers = {
            "Accept-Encoding": "br",
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(API_URL, headers=headers)
        print(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            error_text = f"❌ Ошибка при запросе к Skinport: {response.status_code}\n{response.text}"
            print(error_text)
            send_telegram_message(error_text)
            return

        try:
            items = response.json()
        except Exception as e:
            print("Ошибка при парсинге JSON:", e)
            send_telegram_message(f"❗️ Ошибка при парсинге JSON: {e}")
            return

        print(f"Получено {len(items)} товаров")

        matches_found = 0

        for item in items:
            market_name = item.get("market_hash_name", "")
            price = item.get("min_price", None)
            item_url = item.get("item_page", "")

            print(f"Проверка товара: {market_name}, Цена: {price}, Ссылка: {item_url}")

            # Talon Knife
            if "talon knife" in market_name.lower():
                print(f"Найден Talon Knife: {market_name}")
                if price is not None and price <= ITEMS_PRICE_LIMITS["Talon Knife"]:
                    message = f"🔔 Найден Talon Knife:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(message)
                    send_telegram_message(message)
                    matches_found += 1

        if matches_found == 0:
            print("Ничего не найдено.")
            send_telegram_message("⚠️ Ничего не найдено из интересующих предметов.")

    except Exception as e:
        error_msg = f"❗ Ошибка при выполнении скрипта: {e}"
        print(error_msg)
        send_telegram_message(error_msg)

# 🔁 Запуск в цикле
while True:
    check_items()
    time.sleep(120)  # Пауза 2 минуты
