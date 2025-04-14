import requests
import time

# Telegram bot token и chat_id
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"

# Настройки отслеживаемого предмета
TARGET_ITEMS = [
    {
        "name_contains": "Талон",
        "price_limit": 300  # В евро
    }
]

# URL API Skinport
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def check_items():
    response = requests.get(API_URL)
    if response.status_code != 200:
        print("Ошибка при запросе к API Skinport")
        return

    items = response.json()
    print(f"Получено {len(items)} предметов")

    for item in items:
        for target in TARGET_ITEMS:
            name = item.get("market_hash_name", "")
            price = item.get("price", 0)
            if target["name_contains"].lower() in name.lower() and price <= target["price_limit"]:
                msg = f"🔔 Найден предмет: <b>{name}</b>\n💸 Цена: {price} €\n🔗 {item.get('url')}"
                send_message(msg)

if __name__ == "__main__":
    while True:
        check_items()
        time.sleep(60)  # Проверка каждую минуту
