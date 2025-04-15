import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import os
import requests

# Задаем токен и ID чата
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация ключевых слов для поиска
ITEMS_PRICE_LIMITS = {}

# Функция для отправки сообщений в Telegram
async def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            logger.error(f"Ошибка отправки в Telegram: {response.text}")
    except Exception as e:
        logger.error(f"Ошибка Telegram: {e}")

# Команда /start для приветствия и описания команд
async def start(update: Update, context):
    message = "Привет! Я бот для поиска предметов на Skinport.\n" \
              "Используй команду /add для добавления нового предмета для поиска.\n" \
              "Используй команду /remove для удаления предмета из поиска."
    await update.message.reply_text(message)

# Команда /add для добавления предметов
async def add(update: Update, context):
    if len(context.args) != 2:
        await update.message.reply_text("Ошибка! Используй команду как: /add <предмет> <макс. цена>")
        return

    item_name = context.args[0]
    try:
        max_price = float(context.args[1])
    except ValueError:
        await update.message.reply_text("Ошибка! Цена должна быть числом.")
        return

    ITEMS_PRICE_LIMITS[item_name] = max_price
    await update.message.reply_text(f"Предмет {item_name} добавлен с максимальной ценой {max_price} EUR.")

# Команда /remove для удаления предметов
async def remove(update: Update, context):
    if len(context.args) != 1:
        await update.message.reply_text("Ошибка! Используй команду как: /remove <предмет>")
        return

    item_name = context.args[0]

    if item_name in ITEMS_PRICE_LIMITS:
        del ITEMS_PRICE_LIMITS[item_name]
        await update.message.reply_text(f"Предмет {item_name} удален из списка поиска.")
    else:
        await update.message.reply_text(f"Предмет {item_name} не найден в списке поиска.")

# Основная функция для запуска бота
async def main():
    # Создание объекта приложения
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("remove", remove))

    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    # Просто вызови основной асинхронный метод без asyncio.run
    import asyncio
    asyncio.create_task(main())
