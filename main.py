import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests

# Задаем токен и ID чата
TELEGRAM_BOT_TOKEN = "8095985098:AAGmSZ1JZFunP2un1392Uh4gUg7LY3AjD6A"
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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Команда /start от пользователя {update.message.from_user.username}")
    message = "Привет! Я бот для поиска предметов на Skinport.\n" \
              "Используй команду /add <название предмета> для добавления нового предмета.\n" \
              "Используй команду /remove <название предмета> для удаления предмета."
    await update.message.reply_text(message)

# Команда /add для добавления предмета
async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Пожалуйста, укажите название предмета для добавления.")
        return

    item_name = " ".join(context.args)
    logger.info(f"Пользователь {update.message.from_user.username} добавил предмет: {item_name}")
    # Здесь вы можете добавить логику для добавления предмета в базу данных или список.
    
    # Отправка подтверждения
    await update.message.reply_text(f"Предмет '{item_name}' успешно добавлен в поиск.")

# Команда /remove для удаления предмета
async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Пожалуйста, укажите название предмета для удаления.")
        return

    item_name = " ".join(context.args)
    logger.info(f"Пользователь {update.message.from_user.username} удалил предмет: {item_name}")
    # Здесь вы можете добавить логику для удаления предмета из базы данных или списка.
    
    # Отправка подтверждения
    await update.message.reply_text(f"Предмет '{item_name}' успешно удален из поиска.")

# Основная функция для запуска бота
def main():
    # Создание объекта приложения
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_item))
    application.add_handler(CommandHandler("remove", remove_item))

    # Запуск бота (переход на polling)
    logger.info("Бот запускается...")
    application.run_polling()

if __name__ == '__main__':
    # Прямо вызываем основной метод без asyncio.run()
    main()
