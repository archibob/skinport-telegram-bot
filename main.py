import requests
import time

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Ключевые слова и максимальные цены
ITEMS_PRICE_LIMITS = {
    "talon knife": 300,       # в евро
    "bronze morph": 150       # в евро
}

# Храним ID уже найденных товаров
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

        try:
            items = response.json()
        except Exception as e:
            print("Ошибка при парсинге JSON:", e)
            send_telegram_message(f"❗️ Ошибка при парсинге JSON: {e}")
            return

        print(f"Получено {len(items)} товаров")

        found = False
        for item in items:
            market_name = item.get("market_hash_name", "")
            price = item.get("min_price", None)
            item_id = item.get("id", None)

            if price is None or item_id is None:
                continue

            market_name_lower = market_name.lower()

            for keyword, max_price in ITEMS_PRICE_LIMITS.items():
                if keyword in market_name_lower and price <= max_price and item_id not in found_items:
                    message = (
                        f"🔔 Найден предмет:\n"
                        f"{market_name}\n"
                        f"💶 Цена: {price} EUR"
                    )
                    print(message)
                    send_telegram_message(message)
                    found_items.add(item_id)
                    found = True
                    break  # не проверяем другие ключевые слова

        if not found:
            print("Ничего не найдено.")
            # Не шлём лишний раз Telegram, чтобы не спамить

    except Exception as e:
        error_msg = f"❗ Ошибка при выполнении скрипта: {e}"
        print(error_msg)
        send_telegram_message(error_msg)

# 🔁 Запуск в цикле
while True:
    check_items()
    time.sleep(60)
