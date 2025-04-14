import requests
import time
import re
import json
import os

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# Путь к файлу для хранения данных о товарах
ITEMS_FILE = "items.json"

# Загрузка текущего списка товаров
def load_items():
    if os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, 'r') as file:
            return json.load(file)
    return {}

# Сохранение списка товаров в файл
def save_items(items):
    with open(ITEMS_FILE, 'w') as file:
        json.dump(items, file)

# 🔧 Ключевые слова и максимальные цены (по умолчанию)
ITEMS_PRICE_LIMITS = load_items()

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

# Функция обработки команд
def handle_command(command):
    global ITEMS_PRICE_LIMITS
    # Добавление нового товара
    match = re.match(r"^add (\S.+) (\d+)$", command)
    if match:
        item_name = match.group(1)
        price_limit = int(match.group(2))
        ITEMS_PRICE_LIMITS[item_name] = price_limit
        save_items(ITEMS_PRICE_LIMITS)
        return f"✅ Товар '{item_name}' добавлен с ценой {price_limit} EUR."

    # Удаление товара
    match = re.match(r"^remove (\S.+)$", command)
    if match:
        item_name = match.group(1)
        if item_name in ITEMS_PRICE_LIMITS:
            del ITEMS_PRICE_LIMITS[item_name]
            save_items(ITEMS_PRICE_LIMITS)
            return f"✅ Товар '{item_name}' удален."
        else:
            return f"❌ Товар '{item_name}' не найден."

    return "❗️ Команда не распознана."

# Функция проверки наличия товаров
def check_items():
    try:
        headers = {
            "Accept-Encoding": "br",
            "User-Agent": "Mozilla/5.0"
        }
        
        response = requests.get(API_URL, headers=headers)
        if response.status_code != 200:
            send_telegram_message(f"❌ Ошибка при запросе к Skinport: {response.status_code}")
            return

        try:
            items = response.json()
        except Exception as e:
            send_telegram_message(f"❗️ Ошибка при парсинге JSON: {e}")
            return

        print(f"Получено {len(items)} товаров")

        matches_found = 0

        for item in items:
            market_name = item.get("market_hash_name", "")
            price = item.get("min_price", None)
            item_url = item.get("item_page", "")

            print(f"Проверка товара: {market_name}, Цена: {price}, Ссылка: {item_url}")

            for item_name, price_limit in ITEMS_PRICE_LIMITS.items():
                if re.search(re.escape(item_name), market_name, re.IGNORECASE):
                    print(f"Найдено соответствие для товара: {market_name}")
                    if price is not None and price <= price_limit:
                        message = f"🔔 Найден товар:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                        print(message)
                        send_telegram_message(message)
                        matches_found += 1

        if matches_found == 0:
            send_telegram_message("⚠️ Ничего не найдено из интересующих предметов.")

    except Exception as e:
        error_msg = f"❗ Ошибка при выполнении скрипта: {e}"
        print(error_msg)
        send_telegram_message(error_msg)

# Основная функция для работы с Telegram
def start_bot():
    last_update_id = None
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={last_update_id}"
            response = requests.get(url)
            updates = response.json().get("result", [])

            for update in updates:
                last_update_id = update["update_id"] + 1
                message = update["message"].get("text", "")
                if message:
                    print(f"Получена команда: {message}")
                    response_message = handle_command(message)
                    send_telegram_message(response_message)

        except Exception as e:
            print("Ошибка бота:", e)
        
        time.sleep(5)

# 🔁 Запуск в цикле
while True:
    check_items()
    time.sleep(120)  # Пауза 2 минуты
    start_bot()  # Запуск Telegram-бота
