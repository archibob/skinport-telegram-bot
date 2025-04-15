import logging
import requests
from urllib.parse import quote
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Токен и ID чата
TELEGRAM_BOT_TOKEN = "8095985098:AAGmSZ1JZFunP2un1392Uh4gUg7LY3AjD6A"
TELEGRAM_CHAT_ID = "388895285"

# Логирование
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилище отслеживаемых предметов: (название, максимальная цена)
tracked_items = []

# Отправка сообщения в Telegram
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
    message = "Привет! Я бот для поиска предметов на Skinport.\n\n" \
              "🟢 /add <название> <макс_цена> — добавить предмет\n" \
              "🔴 /remove <название> — удалить предмет\n" \
              "📋 /search — показать отслеживаемые предметы\n" \
              "🔍 /scan — проверить наличие на Skinport"
    await update.message.reply_text(message)

# Команда /add
async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Формат: /add <название> <макс_цена>")
        return
    item_name = " ".join(context.args[:-1])
    try:
        max_price = float(context.args[-1])
    except ValueError:
        await update.message.reply_text("Последний аргумент должен быть числом (макс. цена).")
        return

    tracked_items.append((item_name, max_price))
    await update.message.reply_text(f"Добавлен: {item_name} до {max_price}€")

# Команда /remove
async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Формат: /remove <название>")
        return
    item_name = " ".join(context.args)
    for item in tracked_items:
        if item[0].lower() == item_name.lower():
            tracked_items.remove(item)
            await update.message.reply_text(f"Удалён: {item_name}")
            return
    await update.message.reply_text("Такой предмет не найден в списке.")

# Команда /search
async def search_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tracked_items:
        await update.message.reply_text("Список отслеживаемых предметов пуст.")
        return
    message = "🔍 Отслеживаемые предметы:\n"
    for name, price in tracked_items:
        message += f"- {name} до {price}€\n"
    await update.message.reply_text(message)

# Команда /scan
async def scan_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tracked_items:
        await update.message.reply_text("Список отслеживаемых предметов пуст.")
        return

    found = []
    for item_name, max_price in tracked_items:
        url = f"https://api.skinport.com/v1/items?app_id=730&currency=EUR&tradable=1"
        try:
            response = requests.get(url)
            if response.status_code != 200:
                await update.message.reply_text("Ошибка запроса к API Skinport.")
                return
            data = response.json()
        except Exception as e:
            await update.message.reply_text(f"Ошибка при запросе к Skinport: {e}")
            return

        for item in data:
            name = item.get("market_hash_name", "")
            min_price = item.get("min_price")

            if item_name.lower() in name.lower() and float(min_price) <= max_price:
                item_url_name = quote(name, safe='')
                found.append(f"{name} за {min_price}€\nhttps://skinport.com/item/{item_url_name}")

    if found:
        await update.message.reply_text("🟢 Найдено:\n\n" + "\n\n".join(found))
    else:
        await update.message.reply_text("🔍 Ничего не найдено.")

# Запуск бота
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_item))
    application.add_handler(CommandHandler("remove", remove_item))
    application.add_handler(CommandHandler("search", search_items))
    application.add_handler(CommandHandler("scan", scan_items))

    logger.info("Бот запускается...")
    application.run_polling()

if __name__ == '__main__':
    main()
