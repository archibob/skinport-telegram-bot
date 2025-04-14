import requests
import time

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Ключевые слова и максимальные цены (в евро)
ITEMS_PRICE_LIMITS = {
    "Sport Gloves | Bronze Morph": 150,  # Ищем все перчатки этого типа
    "Talon Knife": 300  # Ищем все Talon Knife ниже 300 евро
}

# Храним уникальные идентификаторы уже найденных товаров
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
            unique_id = f"{market_name}:{price}"

            # Логируем все товары для отладки
            print(f"Проверка товара: {market_name}, Цена: {price}, Ссылка: {item_url}")

            # Проверка для перчаток Sport Gloves | Bronze Morph
            if price is not None and "Sport Gloves" in market_name and "Bronze Morph" in market_name and price <= ITEMS_PRICE_LIMITS["Sport Gloves | Bronze Morph"] and unique_id not in found_items:
                message = f"🔔 Найден предмет:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                print(f"Найден товар: {message}")
                send_telegram_message(message)
                found_items.add(unique_id)
                found = True

            # Логика для поиска ножей Talon Knife
            elif price is not None and "talon knife" in market_name.lower() and price <= ITEMS_PRICE_LIMITS["Talon Knife"] and unique_id not in found_items:
                message = f"🔔 Найден предмет:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                print(f"Найден нож: {message}")
                send_telegram_message(message)
                found_items.add(unique_id)
                found = True

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
