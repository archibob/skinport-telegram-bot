import requests
import time
import re
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Ключевые слова и максимальные цены (в евро)
ITEMS_PRICE_LIMITS = {
    "Sport Gloves | Bronze Morph": 150,
    "Talon Knife": 300,
    "AWP | Asiimov (Battle-Scarred)": 75
}

# Функция отправки сообщения в Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("Ошибка отправки в Telegram:", response.text)
    except Exception as e:
        print("Ошибка Telegram:", e)

# Функция для добавления предметов
async def add_item(update: Update, context):
    item_name = " ".join(context.args)
    if item_name:
        if item_name not in ITEMS_PRICE_LIMITS:
            ITEMS_PRICE_LIMITS[item_name] = float('inf')  # По умолчанию без ограничения
            await update.message.reply_text(f"✅ Предмет '{item_name}' добавлен в список для поиска.")
        else:
            await update.message.reply_text(f"❗ Предмет '{item_name}' уже в списке.")
    else:
        await update.message.reply_text("⚠️ Пожалуйста, укажите имя предмета.")

# Функция для удаления предметов
async def remove_item(update: Update, context):
    item_name = " ".join(context.args)
    if item_name in ITEMS_PRICE_LIMITS:
        del ITEMS_PRICE_LIMITS[item_name]
        await update.message.reply_text(f"✅ Предмет '{item_name}' удален из списка для поиска.")
    else:
        await update.message.reply_text(f"❗ Предмет '{item_name}' не найден в списке.")

# Функция для старта бота
async def start(update: Update, context):
    await update.message.reply_text("Привет! Я бот для отслеживания предметов на Skinport. Используй /add <название> для добавления предметов.")

# Функция для проверки предметов на Skinport
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

            # Проверяем только те предметы, которые есть в ITEMS_PRICE_LIMITS
            for item_name in ITEMS_PRICE_LIMITS:
                if re.search(item_name, market_name, re.IGNORECASE):
                    print(f"Найдено соответствие для {item_name}: {market_name}")
                    if price is not None and price <= ITEMS_PRICE_LIMITS[item_name]:
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

# Запуск проверки предметов в цикле
async def monitor_items():
    while True:
        check_items()
        await asyncio.sleep(120)  # Пауза 2 минуты

# Основная функция
async def main():
    # Создаем и запускаем приложение Telegram
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_item))
    application.add_handler(CommandHandler("remove", remove_item))

    # Запускаем мониторинг предметов
    asyncio.create_task(monitor_items())

    # Запускаем polling
    await application.run_polling()

if __name__ == '__main__':
    # Не используем asyncio.run(), так как event loop уже используется
    asyncio.run(main())
