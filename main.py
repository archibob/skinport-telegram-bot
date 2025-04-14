import requests
import time

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Ключевые слова и максимальные цены (в евро)
ITEMS_PRICE_LIMITS = {
    "Talon Knife": 300,
    "Sport Gloves": 150
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
            print(f"Полные данные товара: {item}")  # Выводим полную информацию для каждого товара

            market_name = item.get("market_hash_name", "")
            price = item.get("min_price", None)
            item_url = item.get("url", "Ссылка не доступна")  # Попробуем использовать 'url' из данных

            # Выводим поля товара, чтобы увидеть, какие данные мы можем использовать
            print(f"Товар: {market_name}, Цена: {price}, Ссылка: {item_url}")

            if price is not None:
                for keyword, max_price in ITEMS_PRICE_LIMITS.items():
                    if keyword.lower() in market_name.lower() and price <= max_price:
                        message = (
                            f"🔔 Найден предмет:\n"
                            f"{market_name}\n"
                            f"💶 Цена: {price} EUR\n"
                            f"🔗 Ссылка: {item_url}"
                        )
                        print(message)
                        send_telegram_message(message)
                        found = True
                        break

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

