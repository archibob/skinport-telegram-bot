import requests
import time

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Ключевые слова и минимальные цены для каждого типа предмета
ITEMS_PRICE_LIMITS = {
    "Коготь": 30000,  # 300 евро в центах
    "Спортивные перчатки | Окисление бронзы": 15000,  # 150 евро в центах
    "AK-47 | Redline": 25000  # Примерная цена для АК-47 | Redline, 250 евро в центах
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

            # Проверяем, если цена не равна None
            if price is not None:
                print(f"Проверяем товар: {market_name}, цена: {price / 100:.2f} EUR")

                # Ищем ключевое слово в названии товара и проверяем цену
                for keyword, min_price in ITEMS_PRICE_LIMITS.items():
                    if keyword.lower() in market_name.lower() and price <= min_price:
                        message = f"🔔 Найден предмет:\n{market_name}\n💶 Цена: {price / 100:.2f} EUR"
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
    time.sleep(60)  # Пауза 60 секунд
