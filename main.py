import requests
import time
import re
import random

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

# Функция отправки сообщений в Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("Ошибка отправки в Telegram:", response.text)
    except Exception as e:
        print("Ошибка Telegram:", e)

# Функция проверки наличия товаров
def check_items():
    try:
        headers = {
            "Accept-Encoding": "br",
            "User-Agent": "Mozilla/5.0"
        }
        
        # Попытки запроса с задержками для избежания блокировки
        retries = 3
        for _ in range(retries):
            response = requests.get(API_URL, headers=headers)
            if response.status_code == 200:
                break
            print(f"Ошибка запроса, повторная попытка... Статус: {response.status_code}")
            time.sleep(random.randint(5, 15))  # Задержка перед повтором
        else:
            print("Не удалось получить данные после нескольких попыток.")
            send_telegram_message("❗️ Не удалось получить данные с Skinport.")
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

            # Логика для поиска нужных товаров
            if re.search(r"Sport\s*Gloves\s*\|\s*Bronze\s*Morph", market_name, re.IGNORECASE):
                print(f"Найдено соответствие для перчаток: {market_name}")
                if price is not None and price <= ITEMS_PRICE_LIMITS["Sport Gloves | Bronze Morph"]:
                    message = f"🔔 Найдены перчатки:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(message)
                    send_telegram_message(message)
                    matches_found += 1

            if "talon knife" in market_name.lower():
                print(f"Найдено соответствие для ножа: {market_name}")
                if price is not None and price <= ITEMS_PRICE_LIMITS["Talon Knife"]:
                    message = f"🔔 Найден нож:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(message)
                    send_telegram_message(message)
                    matches_found += 1

            if re.search(r"AWP\s*\|\s*Asiimov", market_name, re.IGNORECASE):
                print(f"Найдено соответствие для AWP Asiimov: {market_name}")
                if "Battle-Scarred" in market_name and price is not None and price <= ITEMS_PRICE_LIMITS["AWP | Asiimov (Battle-Scarred)"]:
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
