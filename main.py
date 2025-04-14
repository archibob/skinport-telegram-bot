import requests
import time

# Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# Условия фильтра: что искать и по какой цене максимум
FILTERS = [
    {"keywords": ["talon knife"], "max_price": 300},
    {"keywords": ["sport gloves", "bronze morph"], "max_price": 150},
]

found_items = set()

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
        headers = {"Accept-Encoding": "br"}
        response = requests.get(API_URL, headers=headers)
        print(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            error_text = f"❌ Ошибка при запросе к Skinport: {response.status_code}\n{response.text}"
            print(error_text)
            send_telegram_message(error_text)
            return

        items = response.json()
        print(f"Получено {len(items)} товаров")

        found = False
        for item in items:
            market_name = item.get("market_hash_name", "").lower()
            price = item.get("min_price", None)
            item_id = item.get("id", None)

            if price is None or item_id is None:
                continue

            for f in FILTERS:
                if all(keyword in market_name for keyword in f["keywords"]) and price <= f["max_price"]:
                    if item_id not in found_items:
                        message = (
                            f"🔔 Найден предмет:\n"
                            f"{item['market_hash_name']}\n"
                            f"💶 Цена: {price} EUR"
                        )
                        print(message)
                        send_telegram_message(message)
                        found_items.add(item_id)
                        found = True
                    break

        if not found:
            print("Ничего не найдено.")

    except Exception as e:
        error_msg = f"❗ Ошибка при выполнении скрипта: {e}"
        print(error_msg)
        send_telegram_message(error_msg)

# 🔁 Запуск в цикле
while True:
    check_items()
    time.sleep(60)
