import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from urllib.parse import quote

# Задаем токен и ID чата
TELEGRAM_BOT_TOKEN = "8095985098:AAGmSZ1JZFunP2un1392Uh4gUg7LY3AjD6A"
TELEGRAM_CHAT_ID = "388895285"

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилище предметов для поиска (можно заменить на базу данных)
items_to_search = []

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
              "Используй команду /remove <название предмета> для удаления предмета.\n" \
              "Используй команду /search для поиска добавленных предметов."
    await update.message.reply_text(message)

# Команда /add для добавления предмета
async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Пожалуйста, укажите название предмета для добавления.")
        return

    item_name = " ".join(context.args)
    logger.info(f"Пользователь {update.message.from_user.username} добавил предмет: {item_name}")

    # Добавляем предмет в хранилище
    items_to_search.append(item_name)

    # Отправка подтверждения
    await update.message.reply_text(f"Предмет '{item_name}' успешно добавлен в поиск.")

# Команда /remove для удаления предмета
async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Пожалуйста, укажите название предмета для удаления.")
        return

    item_name = " ".join(context.args)
    logger.info(f"Пользователь {update.message.from_user.username} удалил предмет: {item_name}")

    # Удаляем предмет из хранилища
    if item_name in items_to_search:
        items_to_search.remove(item_name)
        await update.message.reply_text(f"Предмет '{item_name}' успешно удален из поиска.")
    else:
        await update.message.reply_text(f"Предмет '{item_name}' не найден в списке поиска.")

# Команда /search для поиска добавленных предметов
async def search_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not items_to_search:
        await update.message.reply_text("Список предметов для поиска пуст.")
    else:
        message = "Вот список предметов для поиска:\n" + "\n".join(items_to_search)
        await update.message.reply_text(message)

# Команда /scan для сканирования предметов по API
async def scan_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not items_to_search:
        await update.message.reply_text("Список предметов для поиска пуст.")
        return

    # Параметры для поиска
    max_price = 80  # пример цены, можно сделать динамичным
    found = []

    # Ищем предметы через API
    for item_name in items_to_search:
        url = f"https://api.skinport.com/api/v1/search?query={item_name}&limit=20"
        response = requests.get(url)
        data = response.json().get("data", [])

        for item in data:
            name = item.get("market_hash_name", "")
            min_price = item.get("min_price")

            # Проверка на None
            if min_price is None:
                continue

            if item_name.lower() in name.lower() and float(min_price) <= max_price:
                item_url_name = quote(name, safe='')
                found.append(f"{name} за {min_price}€\nhttps://skinport.com/item/{item_url_name}")

    # Если предметы найдены, отправляем сообщения
    if found:
        message = "Найдены следующие предметы:\n" + "\n\n".join(found)
        await send_telegram_message(message)
        await update.message.reply_text("Поиск завершён. Результаты отправлены в чат.")
    else:
        await update.message.reply_text("По заданным критериям предметы не найдены.")

# Основная функция для запуска бота
def main():
    # Создание объекта приложения
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_item))
    application.add_handler(CommandHandler("remove", remove_item))
    application.add_handler(CommandHandler("search", search_items))
    application.add_handler(CommandHandler("scan", scan_items))

    # Запуск бота (переход на polling)
    logger.info("Бот запускается...")
    application.run_polling()

if __name__ == '__main__':
    # Прямо вызываем основной метод без asyncio.run()
    main()
