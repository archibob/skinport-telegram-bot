import requests
import time
import brotli

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
TELEGRAM_CHAT_ID = "your-telegram-chat-id"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Ключевые слова, по которым фильтруем нужные предметы
KEYWORDS = ["Коготь", "Сажа"]

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
        
        # Проверим, если сервер вернул статус 200
        if response.status_code != 200:
            error_text = f"❌ Ошибка при запросе к Skinport: {response.status_code}\n{response.text}"
            print(error_text)
            send_telegram_message(error_text)
            return

        # Проверка типа контента
        content_type = response.headers.get("Content-Type")
        if "application/json" not in content_type:
            error_msg = f"❗ Ответ не в формате JSON. Получен тип: {content_type}"
            print(error_msg)
            send_telegram_message(error_msg)
            return

        # Проверим, сжаты ли данные с помощью Brotli
        if 'br' in response.headers.get('Content-Encoding', ''):
            response_content = brotli.decompress(response.content).decode('utf-8')
        else:
            response_content = response.text  # если не сжато, просто читаем как текст

        print("Response content:", response_content)

        # Теперь пробуем распарсить JSON
        try:
            items = response.json()  # Пробуем распарсить как JSON
            print(f"Получено {len(items)} товаров")
        except ValueError:
            error_msg = f"❗ Ошибка при парсинге JSON, возможно неверный формат: {response_content}"
            print(error_msg)
            send_telegram_message(error_msg)
            return

        # Ищем предметы с нужными ключевыми словами
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
