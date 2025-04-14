import requests
import time

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

KEYWORDS = ["Коготь", "Сажа"]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Accept-Encoding": "br",  # Поддержка Brotli, если сервер её применит
}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"Ошибка отправки в Telegram: {response.text}")
    except Exception as e:
        print(f"Ошибка Telegram: {e}")

def check_items():
    try:
        response = requests.get(API_URL, headers=HEADERS)
        print(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            error_text = f"❌ Ошибка при запросе к Skinport: {response.status_code}\n{response.text}"
            print(error_text)
            send_telegram_message(error_text)
            return

        try:
            items = response.json()
        except Exception as e:
            error_msg = f"❗ Ошибка при парсинге JSON: {e}"
            print(error_msg)
            send_telegram_message(error_msg)
            return

        print(f"Получено {len(items)} товаров")
        found = False
        for item in items:
            name = item.get("market_hash_name", "")
            price = item.get("min_price", 0)
            if any(keyword.lower() in name.lower() for keyword in KEYWORDS):
                message = f"🔔 Найден предмет:\n{name}\n💶 Цена: {price / 100:.2f} EUR"
                print(message)
                send_telegram_message(message)
                found = True

        if not found:
            print("Ничего не найдено.")
    except Exception as e:
        error_msg = f"❗ Ошибка при выполнении скрипта: {e}"
        print(error_msg)
        send_telegram_message(error_msg)

# 🔁 Цикл
while True:
    check_items()
    time.sleep(60)
