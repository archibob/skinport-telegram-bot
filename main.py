import logging
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters
)

TELEGRAM_BOT_TOKEN = "8095985098:AAGmSZ1JZFunP2un1392Uh4gUg7LY3AjD6A"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

items_to_search = {}
waiting_for_input = {}

def normalize(text):
    text = re.sub(r'\(.*?\)', '', text)
    text = text.lower().replace("-", " ").replace("|", " ").strip()
    return set(text.split())

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Добавить", callback_data="add")],
        [InlineKeyboardButton("📋 Список", callback_data="list")],
        [InlineKeyboardButton("🔍 Сканировать", callback_data="scan")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери действие:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "add":
        waiting_for_input[query.from_user.id] = "add"
        await query.edit_message_text("Введи название предмета и, при необходимости, цену (пример: AWP Asiimov 100):")
    elif query.data == "list":
        if not items_to_search:
            await query.edit_message_text("Список пуст.")
            return
        keyboard = [
            [InlineKeyboardButton(f"❌ {name}", callback_data=f"remove|{name}")]
            for name in items_to_search
        ]
        await query.edit_message_text("Отслеживаемые предметы:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "scan":
        await query.edit_message_text("Сканирование...")
        await scan(query, context, edit=True)
    elif query.data.startswith("remove|"):
        name = query.data.split("|", 1)[1]
        if name in items_to_search:
            del items_to_search[name]
            await query.edit_message_text(f"Удалён: {name}")
        else:
            await query.edit_message_text(f"{name} не найден.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if waiting_for_input.get(user_id) == "add":
        parts = update.message.text.strip().split()
        if not parts:
            await update.message.reply_text("Название не распознано.")
            return

        prices = []
        while parts and re.match(r"^\d+([.,]\d+)?$", parts[-1]):
            prices.insert(0, float(parts.pop().replace(",", ".")))

        item_name = " ".join(parts).lower()
        if not item_name:
            await update.message.reply_text("Название не распознано.")
            return

        if len(prices) == 2:
            min_price, max_price = prices
        elif len(prices) == 1:
            min_price, max_price = 0, prices[0]
        else:
            min_price, max_price = 0, 999

        items_to_search[item_name] = {"min": min_price, "max": max_price}
        await update.message.reply_text(f"Добавлен: {item_name} от {min_price}€ до {max_price}€")
        del waiting_for_input[user_id]

async def scan(update_or_query, context: ContextTypes.DEFAULT_TYPE, edit=False):
    try:
        response = requests.get(API_URL)
        data = response.json()
        found = []

        for entry in data:
            name = entry.get("market_hash_name", "")
            min_price = entry.get("min_price")
            item_url = entry.get("item_page", "")

            if "graffiti" in name.lower():
                continue

            name_set = normalize(name)
            for item_name, price_range in items_to_search.items():
                item_set = normalize(item_name)
                if item_set.issubset(name_set) and min_price:
                    price = float(min_price)
                    if price_range["min"] <= price <= price_range["max"]:
                        found.append(f"{name} за {price}€\n🔗 {item_url}")
                        break

        if found:
            msg = "Найдены предметы:\n\n" + "\n\n".join(found)
        else:
            msg = "Ничего не найдено."

        if edit:
            await update_or_query.edit_message_text(msg)
        else:
            await update_or_query.message.reply_text(msg)

    except Exception as e:
        logger.error(f"Ошибка при сканировании: {e}")
        if edit:
            await update_or_query.edit_message_text("Произошла ошибка.")
        else:
            await update_or_query.message.reply_text("Произошла ошибка.")

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("Бот запущен")
    app.run_polling()

if __name__ == '__main__':
    main()
