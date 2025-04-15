import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Токен твоего бота
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для команды /start
async def start(update: Update, context: CallbackContext) -> None:
    logger.info(f"Received /start from {update.message.from_user.username}")
    await update.message.reply_text('Привет! Я готов к работе!')

# Функция для команды /add
async def add(update: Update, context: CallbackContext) -> None:
    logger.info(f"Received /add from {update.message.from_user.username}")
    item = ' '.join(context.args)  # Получаем аргументы после команды
    if item:
        await update.message.reply_text(f'Предмет "{item}" добавлен.')
    else:
        await update.message.reply_text('Пожалуйста, укажи предмет для добавления.')

# Функция для команды /remove
async def remove(update: Update, context: CallbackContext) -> None:
    logger.info(f"Received /remove from {update.message.from_user.username}")
    item = ' '.join(context.args)  # Получаем аргументы после команды
    if item:
        await update.message.reply_text(f'Предмет "{item}" удален.')
    else:
        await update.message.reply_text('Пожалуйста, укажи предмет для удаления.')

# Основная асинхронная функция для запуска
async def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("remove", remove))

    # Запуск бота
    logger.info("Бот запущен.")
    await application.run_polling()

# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())
