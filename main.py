import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

# --- Конфигурация ---
TELEGRAM_BOT_TOKEN = "ВАШ_ТОКЕН"
TELEGRAM_CHAT_ID = "ВАШ_CHAT_ID"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# --- Логирование ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Хранилище ---
items_to_track = {}  # {ключевые_слова: макс_цена}

# --- Telegram отправка ---
async def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            logger.error(f"Ошибка Telegram: {response.text}")
    except Exception as e:
        logger.error(f"Ошибка Telegram: {e}")

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "👋 Привет! Я бот для отслеживания предметов на Skinport.\n\n"
        "📌 Команды:\n"
        "/add <название> <макс_цена> — отслеживать предмет\n"
        "/remove <название> — удалить предмет\n"
        "/search — список отслеживаемых предметов\n"
        "/scan <ключевые слова> — найти предметы вручную"
    )
    await update.message.reply_text(message)

async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Пример: /add Karambit Knife 650")
        return

    *name_parts, price_str = context.args
    item_name = " ".join(name_parts)

    try:
        max_price = float(price_str.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Неверный формат цены. Пример: 650")
        return

    items_to_track[item_name.lower()] = max_price
    await update.message.reply_text(f"✅ Добавлен: {item_name} до {max_price}€")

async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пример: /remove Karambit Knife")
        return

    item_name = " ".join(context.args).lower()
    if item_name in items_to_track:
        del items_to_track[item_name]
        await update.message.reply_text(f"🗑️ Удалён: {item_name}")
    else:
        await update.message.reply_text("Предмет не найден в списке.")

async def search_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not items_to_track:
        await update.message.reply_text("Список пуст.")
        return

    msg = "🔍 Отслеживаемые предметы:\n"
    for item, price in items_to_track.items():
        msg += f"— {item} до {price}€\n"
    await update.message.reply_text(msg)

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пример: /scan Karambit Knife")
        return

    keywords = " ".join(context.args).lower()
    found = []

    try:
        response = requests.get(API_URL)
        data = response.json()

        for entry in data:
            name = entry.get("market_hash_name", "").lower()
            price = entry.get("min_price")
            url = entry.get("item_page")

            if keywords in name and price:
                found.append(f"{entry['market_hash_name']} — {price}€\n🔗 {url}")

    except Exception as e:
        logger.error(f"Ошибка сканирования: {e}")
        await update.message.reply_text("Произошла ошибка.")
        return

    if found:
        await update.message.reply_text("🛒 Найдено:\n\n" + "\n\n".join(found))
    else:
        await update.message.reply_text("Ничего не найдено.")

# --- Авто-проверка отслеживаемых предметов ---
async def auto_check():
    await asyncio.sleep(5)
    while True:
        try:
            response = requests.get(API_URL)
            data = response.json()

            for entry in data:
                name = entry.get("market_hash_name", "")
                price = entry.get("min_price")
                url = entry.get("item_page", "")
                name_lower = name.lower()

                for item_keywords, max_price in items_to_track.items():
                    if item_keywords in name_lower and price and float(price) <= max_price:
                        message = f"🔔 Найден предмет: {name} за {price}€\n🔗 {url}"
                        await send_telegram_message(message)

        except Exception as e:
            logger.error(f"Ошибка в авто-проверке: {e}")

        await asyncio.sleep(60)  # каждые 60 секунд

# --- Запуск ---
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_item))
    app.add_handler(CommandHandler("remove", remove_item))
    app.add_handler(CommandHandler("search", search_items))
    app.add_handler(CommandHandler("scan", scan))

    logger.info("Бот запущен.")
    asyncio.create_task(auto_check())  # запуск авто-проверки

    app.run_polling()

if __name__ == "__main__":
    main()
