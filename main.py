import requests
import time

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

def check_items():
    try:
        headers = {
            "Accept-Encoding": "br",
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(API_URL, headers=headers)
        print(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Ошибка при запросе к Skinport: {response.status_code}")
            return

        try:
            items = response.json()
        except Exception as e:
            print("Ошибка при парсинге JSON:", e)
            return

        print(f"Получено {len(items)} товаров")

        # Логирование всех товаров для отладки
        for item in items:
            market_name = item.get("market_hash_name", "Нет названия")
            price = item.get("min_price", "Нет цены")
            item_url = item.get("item_page", "Нет ссылки")
            print(f"Товар: {market_name}, Цена: {price}, Ссылка: {item_url}")

    except Exception as e:
        print(f"❗ Ошибка при выполнении скрипта: {e}")

# Запуск одноразовой проверки
check_items()
