import requests
import time

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Ключевые слова, по которым фильтруем нужные предметы
KEYWORDS = ["Talon Knife", "Sport Gloves | Bronze Morph"]  # Ищем ножи "Talon Knife" и перчатки "Sport Gloves | Bronze Morph"
MIN_PRICE = 10000  # Минимальная цена в ценах Skinport (10000 = 100 EUR)
MAX_PRICE = 20000  # Максимальная цена в ценах Skinport (20000 = 200 EUR)

# Список уже отправленных товаров (по их ID)
sent_items = []

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
            # Логируем всю структуру item, чтобы понять, как выглядят данные
            print(f"Данные товара: {item}")

            market_name = item.get("market_hash_name", "")
            price = item.get("min_price", 0)

            # Логируем цену, чтобы понять, что мы получаем
            print(f"Название: {market_name}, Цена: {price}")

            # Проверка на None для цены
            if price is None:
                print(f"Цена для {market_name} не найдена.")
                continue  # Пропускаем этот товар, если цена не найдена

            # Преобразование цены
