import json
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Настройки
TELEGRAM_BOT_TOKEN = '8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU'
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"
ITEMS_REQUEST_FILE = 'items_requests.json'

# Загрузка запросов из файла
def load_requests():
    try:
        with open(ITEMS_REQUEST_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Сохранение запросов в файл
def save_requests(requests):
    with open(ITEMS_REQUEST_FILE, 'w') as file:
        json.dump(requests, file)

# Функция добавления нового предмета
def add_item(update: Update, context: CallbackContext):
    # Проверяем правильность ввода
    if len(context.args) != 2:
        update.message.reply_text("Использование: /add_item <название> <цена>")
        return

    item_name = context.args[0]
    item_price = float(context.args[1])

    # Загружаем существующие запросы
    requests = load_requests()

    # Добавляем новый запрос
    requests[item_name] = item_price

    # Сохраняем запросы
    save_requests(requests)

    update.message.reply_text(f"Добавлен запрос на предмет: {item_name} с ценой до {item_price} EUR")

# Функция поиска предметов
def check_items():
    # Загружаем запросы
    requests = load_requests()

    # Перебираем все запросы
    for item_name, max_price in requests.items():
        response = requests.get(API_URL)
        if response.status_code == 200:
            items = response.json()
            for item in items:
                if item_name.lower() in item["market_hash_name"].lower():
                    price = float(item.get("min_price", 0))
                    if price <= max_price:
                        message = f"Найдено соответствие для {item_name}:\n{item['market_hash_name']}\nЦена: {price} EUR\n{item['item_page']}"
                        send_telegram_message(message)

# Функция отправки сообщения в Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": 'YOUR_CHAT_ID', "text": message}
    requests.post(url, data=payload)

def main():
    # Инициализация бота
    updater = Updater(TELEGRAM_BOT_TOKEN)

    # Команды
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('add_item', add_item))

    # Запуск бота
    updater.start_polling()

    # Проверка предметов
    check_items()

if __name__ == '__main__':
    main()
