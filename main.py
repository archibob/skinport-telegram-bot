import requests
import time

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Ключевые слова, по которым фильтруем нужные предметы
KEYWORDS = ["Коготь", "Сажа"]  # Добавь свои ключи

# Заголовки для запроса с добавленной поддержкой Brotli
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Accept": "application/json",
    "Accept-Encoding": "br",  # Поддержка Brotli
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
        response = requests.get(API_URL, headers=HEADERS)  # Добавлены заголовки
        print(f"Status Code: {response.status_code}")
        print("Response Headers:", response.headers)  # Добавим вывод заголовков

        if response.status_code != 200:
            error_text = f"❌ Ошибка при запросе к Skinport: {response.status_code}\n{response.text}"
            print(error_text)
            send_telegram_message(error_text)
            return

        # Пробуем декодировать с использованием разных кодировок
        try:
            response_content = response.content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                response_content = response.content.decode('latin1')
            except UnicodeDecodeError as e:
                print(f"Ошибка при декодировании с latin1: {e}")
                response_content = response.content.decode('ascii', errors='ignore')

        print("Response content:", response_content)

        if not response_content.strip():  # Проверяем, что тело ответа не пустое
            error_msg = "❗ Ответ от API Skinport пустой!"
            print(error_msg)
            send_telegram_message(error_msg)
            return

        try:
            items = response.json()
        except ValueError as e:
            print(f"Ошибка при парсинге JSON: {e}")
            send_telegram_message(f"❗ Ошибка при парсинге JSON: {e}")
            return

        print(f"Получено {len(items)} товаров")

        found = False
        for item in items:
            market_name = item.get("market_hash_name", "")
            price = item.get("min_price", 0)
            if any(keyword.lower() in market_name.lower() for keyword in KEYWORDS):
                message = f"🔔 Найден предмет:\n{market_name}\n💶 Цена: {price / 100:.2f} EUR"
                print(message)
                send_telegram_message(message)
                found = True

        if not found:
            print("Ничего не найдено.")
    except Exception as e:
        error_msg = f"❗ Ошибка при выполнении скрипта: {e}"
        print(error_msg)
        send_telegram_message(error_msg)

# 🔁 Запуск в цикле
while True:
    check_items()
    time.sleep(60)  # Пауза 60 секунд
