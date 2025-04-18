import asyncio
import json
import logging
import aiohttp
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# === CONFIG ===
TELEGRAM_BOT_TOKEN = "8095985098:AAGmSZ1JZFunP2un1392Uh4gUg7LY3AjD6A"
TELEGRAM_CHAT_ID = "388895285"
SCAN_INTERVAL = 120  # seconds

# === LOGGING ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === DATA ===
user_favorites = {}  # user_id: [{'name': ..., 'price': ..., 'quality': ...}]
notified_items = set()

# === UTILS ===
def format_skin_key(name: str, quality: str) -> str:
    return f"{name.strip().lower()}::{quality.strip().lower()}"

def get_item_url(item_id):
    return f"https://skinport.com/item/{item_id}"

# === COMMANDS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Добавить в избранное", callback_data="add_fav")],
        [InlineKeyboardButton("Список избранного", callback_data="list_fav")],
    ]
    await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if query.data == "add_fav":
        context.user_data["state"] = "waiting_for_fav"
        await query.edit_message_text("Введите название, максимальную цену и качество через |, например:\n`AK-47 | Redline | 30 | Field-Tested`", parse_mode="Markdown")
    elif query.data == "list_fav":
        favs = user_favorites.get(user_id, [])
        if not favs:
            await query.edit_message_text("Список избранного пуст.")
            return
        msg = "Ваш список избранного:\n\n"
        for i, item in enumerate(favs, 1):
            msg += f"{i}. {item['name']} | До {item['price']}€ | {item['quality']}\n"
        await query.edit_message_text(msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if context.user_data.get("state") == "waiting_for_fav":
        try:
            parts = update.message.text.strip().split("|")
            name = parts[0].strip()
            price = float(parts[1].strip())
            quality = parts[2].strip()
            fav_list = user_favorites.setdefault(user_id, [])
            fav_list.append({"name": name, "price": price, "quality": quality})
            await update.message.reply_text(f"Добавлено: {name} | до {price}€ | {quality}")
        except Exception:
            await update.message.reply_text("Ошибка формата. Попробуйте ещё раз.")
        context.user_data["state"] = None

# === SCAN FUNCTION ===
async def scan_site():
    global notified_items
    url = "https://api.skinport.com/api/browse?sort=price&order=asc"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()

        for user_id, favs in user_favorites.items():
            for fav in favs:
                for item in data.get("items", []):
                    item_name = item.get("market_hash_name")
                    item_price = item.get("price", 9999)
                    item_quality = item.get("wear_tier") or item.get("exterior")

                    if not item_name or not item_price or not item_quality:
                        continue

                    key = format_skin_key(item_name, item_quality)
                    fav_key = format_skin_key(fav["name"], fav["quality"])

                    if fav_key == key and item_price <= fav["price"]:
                        item_id = item.get("id") or item.get("item_id")
                        notify_id = f"{user_id}:{item_id}"
                        if notify_id in notified_items:
                            continue
                        notified_items.add(notify_id)
                        msg = f"Найден предмет для @{user_id}:\n\n{item_name} ({item_quality})\nЦена: {item_price}€\n\n{get_item_url(item_id)}"
                        await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
    except Exception as e:
        logger.error(f"Ошибка при сканировании: {e}")

async def scheduled_scan():
    await scan_site()

# === MAIN ===
if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_scan, "interval", seconds=SCAN_INTERVAL)
    scheduler.start()

    logger.info("Бот запущен.")
    app.run_polling()
