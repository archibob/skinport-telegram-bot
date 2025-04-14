import requests
import time
import re

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Ключевые слова и максимальные цены (в евро)
ITEMS_PRICE_LIMITS = {
    "Sport Gloves | Bronze Morph": 150,
    "Talon Knife": 300,
    "AWP | Asiimov (Battle-Scarred)": 75
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

            # Логирование для отладки
            print(f"Проверка товара: {market_name}, Цена: {price}, Ссылка: {item_url}")

            # Пропускаем товары без цены
            if price is None:
                print(f"Пропущен товар без цены: {market_name}")
                continue

            # Проверка на Sport Gloves | Bronze Morph
            if re.search(r"Sport\s*Gloves\s*\|\s*Bronze\s*Morph", market_name, re.IGNORECASE):
                print(f"Найдено соответствие для перчаток: {market_name}")
                if price <= ITEMS_PRICE_LIMITS["Sport Gloves | Bronze Morph"]:
                    message = f"🔔 Найдены перчатки:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(message)
                    send_telegram_message(message)
                    matches_found += 1

            # Проверка на Talon Knife
            if re.search(r"Talon\s*Knife", market_name, re.IGNORECASE):
                print(f"Найдено соответствие для ножа: {market_name}")
                if price <= ITEMS_PRICE_LIMITS["Talon Knife"]:
                    message = f"🔔 Найден нож:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(message)
                    send_telegram_message(message)
                    matches_found += 1

            # Проверка на AWP | Asiimov (Battle-Scarred)
            if re.search(r"AWP\s*\|\s*Asiimov", market_name, re.IGNORECASE) and "Battle-Scarred" in market_name:
                print(f"Найдено соответствие для AWP Asiimov: {market_name}")
                if price <= ITEMS_PRICE_LIMITS["AWP | Asiimov (Battle-Scarred)"]:
                    message = f"🔔 Найдена AWP Asiimov (Battle-Scarred):\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
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
