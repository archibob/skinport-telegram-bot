import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_BOT_TOKEN = "ВАШ_ТОКЕН"
TELEGRAM_CHAT_ID = "ВАШ_CHAT_ID"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

items_to_search = {}

def normalize(name: str) -> str:
    return name.lower().replace("|", "").replace("-", "").replace("  ", " ").strip()

async def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            logger.error(f"Ошибка отправки в Telegram: {response.text}")
    except Exception as e:
        logger.error(f"Ошибка Telegram: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "Привет! Я бот для поиска предметов на Skinport.\n"
        "Команды:\n"
        "/add <название> <макс_цена> [мин_цена] — добавить предмет\n"
        "/remove <название> — удалить предмет\n"
        "/search — список предметов\n"
        "/scan — ручной поиск по сайту"
    )
    await update.message.reply_text(message)

async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Используй: /add <название> <макс_цена> [мин_цена]")
        return

    try:
        if len(context.args) >= 3:
            try:
                max_price = float(context.args[-2].replace(",", "."))
                min_price = float(context.args[-1].replace(",", "."))
                name_parts = context.args[:-2]
            except ValueError:
                max_price = float(context.args[-1].replace(",", "."))
                min_price = None
                name_parts = context.args[:-1]
        else:
            max_price = float(context.args[-1].replace(",", "."))
            min_price = None
            name_parts = context.args[:-1]
    except ValueError:
        await update.message.reply_text("Неверный формат цены.")
        return

    item_name = " ".join(name_parts)

    if min_price is not None and min_price > max_price:
        await update.message.reply_text("Минимальная цена не может быть выше максимальной.")
        return

    items_to_search[item_name] = (min_price, max_price)

    await update.message.reply_text(
        f"Добавлен: {item_name} с ценой от {min_price if min_price else 'не задано'} до {max_price}€"
    )

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

async def search_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not items_to_search:
        await update.message.reply_text("Список отслеживаемых предметов пуст.")
        return

    message = "Отслеживаемые предметы:\n"
    for item, (min_price, max_price) in items_to_search.items():
        message += f"- {item} от {min_price if min_price else 0}€ до {max_price}€\n"
    await update.message.reply_text(message)

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    found = []
    try:
        response = requests.get(API_URL)
        data = response.json()
        logger.info(f"Получено {len(data)} предметов от API")

        for entry in data:
            name = entry.get("market_hash_name", "")
            min_price_entry = entry.get("min_price")
            item_url = entry.get("item_page", "")

            norm_name = normalize(name)

            for item_name, (min_price, max_price) in items_to_search.items():
                query = normalize(item_name)

                if query in norm_name and min_price_entry:
                    price = float(min_price_entry)
                    if price <= max_price and (min_price is None or price >= min_price):
                        if "graffiti" not in norm_name:
                            found.append(f"{name} за {price}€\n🔗 {item_url}")
    except Exception as e:
        logger.error(f"Ошибка при сканировании: {e}")
        await update.message.reply_text("Произошла ошибка при сканировании.")
        return

    if found:
        await update.message.reply_text("Найдены предметы:\n\n" + "\n\n".join(found))
    else:
        await update.message.reply_text("Ничего не найдено.")

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
