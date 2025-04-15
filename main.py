import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from typing import List, Dict

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилище предметов: {"название": лимит_цены}
items_to_search: Dict[str, float] = {}

# Функция для отправки сообщений
async def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            logger.error(f"Ошибка отправки в Telegram: {response.text}")
    except Exception as e:
        logger.error(f"Ошибка Telegram: {e}")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для поиска предметов на Skinport.\n"
        "Команды:\n"
        "/add <название> <макс_цена> - добавить предмет\n"
        "/remove <название> - удалить предмет\n"
        "/search - показать список\n"
        "/scan - ручной поиск"
    )

# Команда /add
async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Формат: /add <название> <макс_цена>")
        return

    *item_parts, price = context.args
    item_name = " ".join(item_parts)
    try:
        price_limit = float(price)
    except ValueError:
        await update.message.reply_text("Укажите корректную цену.")
        return

    items_to_search[item_name] = price_limit
    await update.message.reply_text(f"Добавлено: {item_name} до {price_limit}€")

# Команда /remove
async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Формат: /remove <название>")
        return

    item_name = " ".join(context.args)
    if item_name in items_to_search:
        del items_to_search[item_name]
        await update.message.reply_text(f"Удалено: {item_name}")
    else:
        await update.message.reply_text("Предмет не найден.")

# Команда /search
async def search_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not items_to_search:
        await update.message.reply_text("Список пуст.")
        return

    message = "Следим за:\n"
    for item, price in items_to_search.items():
        message += f"{item} — до {price}€\n"
    await update.message.reply_text(message)

# Команда /scan
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    found = []

    for item_name, max_price in items_to_search.items():
        item_url_name = item_name.replace(" ", "%20")
        url = f"https://api.skinport.com/v1/items?app_id=730&currency=EUR"
        try:
            response = requests.get(url)
            data = response.json()
            for entry in data:
                if entry["market_hash_name"] == item_name and entry["min_price"] <= max_price:
                    found.append(f"{item_name}: {entry['min_price']}€\nhttps://skinport.com/item/{item_url_name}")
        except Exception as e:
            logger.error(f"Ошибка при сканировании: {e}")

    if found:
        await update.message.reply_text("Найдены предметы:\n" + "\n\n".join(found))
    else:
        await update.message.reply_text("Ничего не найдено.")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_item))
    application.add_handler(CommandHandler("remove", remove_item))
    application.add_handler(CommandHandler("search", search_items))
    application.add_handler(CommandHandler("scan", scan))

    logger.info("Бот запущен")
    application.run_polling()

if __name__ == '__main__':
    main()
