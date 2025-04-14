from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Ваши настройки
TELEGRAM_BOT_TOKEN = "ВАШ_ТОКЕН"

# Функция для обработки команды /start
async def start(update: Update, context):
    await update.message.reply("Привет! Напиши название предмета и цену для поиска.")

# Основная функция для запуска бота
async def main():
    # Создание объекта Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация команд и обработчиков
    application.add_handler(CommandHandler("start", start))

    # Запуск бота с использованием нового синтаксиса
    await application.run_polling()

# Запуск асинхронной функции
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
