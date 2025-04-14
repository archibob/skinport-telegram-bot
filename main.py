import requests
import time
import re

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Ключевые слова и максимальные цены (в евро)
ITEMS_PRICE_LIMITS = {
    "Sport Gloves | Bronze Morph": 150,  # Максимальная цена для этих перчаток
    "Talon Knife": 300,  # Максимальная цена для ножей
    "AWP Asiimov (Battle-Scarred)": 75  # Максимальная цена для AWP Asiimov (Battle-Scarred)
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

        found = False
        for item in items:
            market_name = item.get("market_hash_name", "")
            price = item.get("min_price", None)
            item_url = item.get("item_page", "")  # Используем item_page для точной ссылки

            # Логируем все товары для отладки
            print(f"Товар: {market_name}, Цена: {price}, Ссылка: {item_url}")

            # Проверка для "Sport Gloves | Bronze Morph"
            if price is not None:
                if re.search(r"Sport Gloves\s*\|\s*Bronze Morph", market_name) and price <= ITEMS_PRICE_LIMITS["Sport Gloves | Bronze Morph"]:
                    message = f"🔔 Найден предмет:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(f"Найден товар: {message}")
                    send_telegram_message(message)
                    found = True

                # Логика для поиска ножей Talon Knife
                elif "talon knife" in market_name.lower() and price <= ITEMS_PRICE_LIMITS["Talon Knife"]:
                    message = f"🔔 Найден нож:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(f"Найден нож: {message}")
                    send_telegram_message(message)
                    found = True

                # Логика для поиска AWP Asiimov (Battle-Scarred)
                # Регулярное выражение, чтобы находить AWP Asiimov с Battle-Scarred
                if re.search(r"AWP\s*\|\s*Asiimov", market_name, re.IGNORECASE) and "Battle-Scarred" in market_name:
                    print(f"Проверка AWP Asiimov: {market_name} с ценой {price} евро")
                    if price is not None and price <= ITEMS_PRICE_LIMITS["AWP Asiimov (Battle-Scarred)"]:
                        message = f"🔔 Найден AWP Asiimov (Battle-Scarred):\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                        print(f"Найден AWP Asiimov: {message}")
                        send_telegram_message(message)
                        found = True
                    else:
                        print(f"AWP Asiimov не подходит по цене: {price} или товар уже был найден: {market_name}")

        if not found:
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
