import logging
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

TELEGRAM_BOT_TOKEN = "8095985098:AAGmSZ1JZFunP2un1392Uh4gUg7LY3AjD6A"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

items_to_search = {}
favorite_items = {}
waiting_for_input = {}

def normalize(text):
    text = re.sub(r'\(.*?\)', '', text)
    text = text.lower().replace("-", " ").replace("|", " ").strip()
    return set(text.split())

def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Добавить", callback_data="add")],
        [InlineKeyboardButton("⭐ В избранное", callback_data="add_fav")],
        [InlineKeyboardButton("📋 Список", callback_data="list")],
        [InlineKeyboardButton("🔍 Сканировать", callback_data="scan")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите действие:", reply_markup=main_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "add":
        waiting_for_input[user_id] = "add"
        await query.message.reply_text("Введите название предмета и (необязательно) цену:")
    elif query.data == "add_fav":
        waiting_for_input[user_id] = "fav"
        await query.message.reply_text("Введите название избранного предмета и максимальную цену:")
    elif query.data == "list":
        if not items_to_search and not favorite_items:
            await query.message.reply_text("Список пуст.", reply_markup=main_keyboard())
            return
        text = "🎯 Отслеживаемые:\n"
        for name, p in items_to_search.items():
            text += f"• {name} — {p['min']}€–{p['max']}€\n"
        text += "\n⭐ Избранное:\n"
        for name, max_price in favorite_items.items():
            text += f"• {name} — до {max_price}€\n"
        await query.message.reply_text(text, reply_markup=main_keyboard())
    elif query.data == "scan":
        await scan(query, context)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    mode = waiting_for_input.get(user_id)

    if not mode:
        return

    parts = update.message.text.strip().split()
    if not parts:
        await update.message.reply_text("Название не распознано.", reply_markup=main_keyboard())
        return

    prices = []
    while parts and re.match(r"^\d+([.,]\d+)?$", parts[-1]):
        prices.insert(0, float(parts.pop().replace(",", ".")))

    item_name = " ".join(parts).lower()
    if not item_name:
        await update.message.reply_text("Название не распознано.", reply_markup=main_keyboard())
        return

    if mode == "add":
        if len(prices) == 2:
            min_price, max_price = prices
        elif len(prices) == 1:
            min_price, max_price = 0, prices[0]
        else:
            min_price, max_price = 0, 999

        items_to_search[item_name] = {"min": min_price, "max": max_price}
        await update.message.reply_text(
            f"✅ Добавлен: {item_name} от {min_price}€ до {max_price}€",
            reply_markup=main_keyboard()
        )
    elif mode == "fav":
        if prices:
            favorite_items[item_name] = prices[0]
            await update.message.reply_text(
                f"⭐ Добавлено в избранное: {item_name} до {prices[0]}€",
                reply_markup=main_keyboard()
            )
        else:
            await update.message.reply_text("Укажите максимальную цену.", reply_markup=main_keyboard())
    del waiting_for_input[user_id]

async def scan(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    found = []
    try:
        response = requests.get(API_URL)
        data = response.json()

        for entry in data:
            name = entry.get("market_hash_name", "")
            min_price = entry.get("min_price")
            item_url = entry.get("item_page", "")

            if not name or not min_price:
                continue

            name_set = normalize(name)
            price_f = float(min_price)

            # Проверка обычного списка
            for item_name, price_range in items_to_search.items():
                if normalize(item_name).issubset(name_set) and price_range["min"] <= price_f <= price_range["max"]:
                    found.append(f"🎯 {name} — {price_f}€\n🔗 {item_url}")
                    break

            # Проверка избранного
            for fav_name, max_price in favorite_items.items():
                if normalize(fav_name).issubset(name_set) and price_f <= max_price:
                    found.append(f"⭐ {name} — {price_f}€\n🔗 {item_url}")
                    # Отправка сразу, как найдено
                    await context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"⭐ Найдено в избранном:\n{name} — {price_f}€\n🔗 {item_url}")

    except Exception as e:
        logger.error(f"Ошибка при сканировании: {e}")
        await update_or_query.message.reply_text("Произошла ошибка при сканировании.", reply_markup=main_keyboard())
        return

    if isinstance(update_or_query, Update):  # ручной запуск
        msg = "Найдено:\n\n" + "\n\n".join(found) if found else "Ничего не найдено."
        await update_or_query.message.reply_text(msg, reply_markup=main_keyboard())

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.run_polling()

if __name__ == '__main__':
    main()
