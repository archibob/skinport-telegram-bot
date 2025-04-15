import requests
import time
import re
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Ключевые слова и максимальные цены (в евро)
ITEMS_PRICE_LIMITS = {}

# Включим логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Команда /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я бот для отслеживания скинов на Skinport. Используй команду /add для добавления предмета.")

# Команда /add
def add(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        update.message.reply_text("Пожалуйста, укажите название предмета для поиска. Например, /add Sport Gloves | Bronze Morph")
        return

    item = ' '.join(context.args)
    update.message.reply_text(f"Добавил предмет для поиска: {item}")

    # Добавление предмета в список для поиска с ценой по умолчанию 150 EUR
    ITEMS_PRICE_LIMITS[item] = 150

# Функция для отправки сообщений в Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("Ошибка отправки в Telegram:", response.text)
    except Exception as e:
        print("Ошибка Telegram:", e)

# Функция для проверки товаров
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

        matches_found = 0

        for item in items:
            market_name = item.get("market_hash_name", "")
            price = item.get("min_price", None)
            item_url = item.get("item_page", "")

            # Логирование для отладки
            print(f"Проверка товара: {market_name}, Цена: {price}, Ссылка: {item_url}")

            for item_name, price_limit in ITEMS_PRICE_LIMITS.items():
                if re.search(item_name, market_name, re.IGNORECASE):
                    print(f"Найдено соответствие для товара: {market_name}")
                    if price is not None and price <= price_limit:
                        message = f"🔔 Найден товар:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                        print(message)
                        send_telegram_message(message)
                        matches_found += 1

        if matches_found == 0:
            print("Ничего не найдено.")
            send_telegram_message("⚠️ Ничего не найдено из интересующих предметов.")

    except Exception as e:
        error_msg = f"❗ Ошибка при выполнении скрипта: {e}"
        print(error_msg)
        send_telegram_message(error_msg)

# Настроим бота
def main():
    # Токен и создание Updater
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)

    # Получим диспетчер для обработки команд
    dp = updater.dispatcher

    # Добавляем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add))

    # Запуск бота
    updater.start_polling()

    # Запуск скрипта проверки товаров в фоновом режиме
    while True:
        check_items()
        time.sleep(120)  # Пауза 2 минуты

    updater.idle()

if __name__ == '__main__':
    main()

