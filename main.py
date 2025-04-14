import requests
import time

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Ключевые слова, по которым фильтруем нужные предметы
KEYWORDS = ["Коготь", "Sport Gloves | Bronze Morph"]  # Ищем ножи "Коготь" и перчатки "Окисление бронзы"

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
            price = item.get("min_price", 0)

            # Проверка на None для цены
            if price is None:
                print(f"Цена для {market_name} не найдена.")
                continue  # Пропускаем этот товар, если цена не найдена

            # Преобразование цены в евро (если цена указана в центрах)
            price_in_euro = price / 100.0  # Преобразуем цену из центров в евро

            # Проверка на наличие ключевых слов в названии предмета
            if any(keyword.lower() in market_name.lower() for keyword in KEYWORDS):
                message = f"🔔 Найден предмет:\n{market_name}\n💶 Цена: {price_in_euro:.2f} EUR"
                print(message)
                send_telegram_message(message)
                found = True

        if not found:
            print("Ничего не найдено.")
            send_telegram_message("❗️ Не найдено товаров по запросу.")
    except Exception as e:
        error_msg = f"❗ Ошибка при выполнении скрипта: {e}"
        print(error_msg)
        send_telegram_message(error_msg)

# 🔁 Запуск в цикле
while True:
    check_items()
    time.sleep(60)  # Пауза 60 секунд
