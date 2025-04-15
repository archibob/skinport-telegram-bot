import logging
from telegram import Update
from telegram.ext import Application, CommandHandler
import os
import requests

# Задаем токен и ID чата
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info(f"Команда /start от пользователя {update.message.from_user.username}")
    message = "Привет! Я бот для поиска предметов на Skinport.\n" \
              "Используй команду /add для добавления нового предмета для поиска.\n" \
              "Используй команду /remove для удаления предмета из поиска."
    await update.message.reply_text(message)

# Основная функция для запуска бота
async def main():
    # Создание объекта приложения
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))

    # Запуск бота
    logger.info("Бот запускается...")
    await application.run_polling()

if __name__ == '__main__':
    # Запускаем бота без использования asyncio.run(), т.к. в Railway уже есть активный цикл
    import sys
    from io import StringIO
    sys.stdout = StringIO()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.run_polling()
