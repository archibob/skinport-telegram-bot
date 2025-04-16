import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Токен и ID чата
TELEGRAM_BOT_TOKEN = "8095985098:AAGmSZ1JZFunP2un1392Uh4gUg7LY3AjD6A"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Хранилище отслеживаемых предметов в виде словаря: название -> макс. цена
items_to_search = {}

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
    message = (
        "Привет! Я бот для поиска предметов на Skinport.\n"
        "Команды:\n"
        "/add <название> <макс_цена> — добавить предмет\n"
        "/remove <название> — удалить предмет\n"
        "/search — список предметов\n"
        "/scan — ручной поиск по сайту"
    )
    await update.message.reply_text(message)

# Команда /add
async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Используй: /add <название> <макс_цена>")
        return

    *name_parts, price_str = context.args
    item_name = " ".join(name_parts)

    try:
        max_price = float(price_str.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Неверный формат цены.")
        return

    items_to_search[item_name] = max_price
    await update.message.reply_text(f"Добавлен: {item_name} до {max_price}€")

# Команда /remove
async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /remove <название>")
        return

    item_name = " ".join(context.args)
    if item_name in items_to_search:
        del items_to_search[item_name]
        await update.message.reply_text(f"Удалён: {item_name}")
    else:
        await update.message.reply_text(f"{item_name} не найден в списке.")

# Команда /search
async def search_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not items_to_search:
        await update.message.reply_text("Список отслеживаемых предметов пуст.")
        return

    message = "Отслеживаемые предметы:\n"
    for item, price in items_to_search.items():
        message += f"- {item} до {price}€\n"
    await update.message.reply_text(message)

# Команда /scan
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    found = []
    url = API_URL

    try:
        response = requests.get(url)
        data = response.json()
        logger.info(f"Получено {len(data)} предметов от API")

        for entry in data:
            name = entry.get("market_hash_name", "")
            min_price = entry.get("min_price")
            item_url = entry.get("item_page", "")

            logger.info(f"Проверка предмета: {name} - цена: {min_price} - ссылка: {item_url}")

            # Ищем ключевые слова в названии
            for item_name, max_price in items_to_search.items():
                # Разбиваем строку на ключевые слова
                item_keywords = item_name.lower().split()

                # Проверяем, содержатся ли все ключевые слова в названии предмета
                if all(keyword in name.lower() for keyword in item_keywords) and min_price and float(min_price) <= max_price:
                    found.append(f"{name} за {min_price}€\n🔗 {item_url}")

    except Exception as e:
        logger.error(f"Ошибка при сканировании: {e}")
        await update.message.reply_text("Произошла ошибка при сканировании.")
        return

    if found:
        await update.message.reply_text("Найдены предметы:\n\n" + "\n\n".join(found))
    else:
        await update.message.reply_text("Ничего не найдено.")

# Запуск бота
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_item))
    app.add_handler(CommandHandler("remove", remove_item))
    app.add_handler(CommandHandler("search", search_items))
    app.add_handler(CommandHandler("scan", scan))

    logger.info("Бот запускается...")
    app.run_polling()

if __name__ == '__main__':
    main()
