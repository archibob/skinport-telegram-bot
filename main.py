import logging
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

TELEGRAM_BOT_TOKEN = "8095985098:AAGmSZ1JZFunP2un1392Uh4gUg7LY3AjD6A"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

items_to_search = {}
favorite_items = {}
waiting_for_input = {}
search_results = {}

def normalize(text):
    text = re.sub(r'\(.*?\)', '', text)
    text = text.lower().replace("-", " ").replace("|", " ").strip()
    return set(text.split())

def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Добавить", callback_data="add")],
        [InlineKeyboardButton("📋 Список", callback_data="list")],
        [InlineKeyboardButton("⭐ Избранное", callback_data="favorites")],
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
    elif query.data == "list":
        if not items_to_search:
            await query.message.reply_text("Список пуст.", reply_markup=main_keyboard())
            return
        keyboard = [
            [InlineKeyboardButton(f"❌ {name}", callback_data=f"delete|{name}")]
            for name in items_to_search.keys()
        ]
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
        await query.message.reply_text("Ваши предметы:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "favorites":
        if not favorite_items:
            await query.message.reply_text("Избранное пусто.", reply_markup=main_keyboard())
            return
        msg = "\n".join(
            [f"{name} — до {info['max']}€" for name, info in favorite_items.items()]
        )
        await query.message.reply_text("⭐ Избранное:\n" + msg, reply_markup=main_keyboard())
    elif query.data.startswith("delete|"):
        name = query.data.split("|", 1)[1]
        if name in items_to_search:
            del items_to_search[name]
            await query.message.reply_text(f"Удалено: {name}", reply_markup=main_keyboard())
    elif query.data.startswith("fav|"):
        item_name = query.data.split("|", 1)[1]
        info = search_results.get(item_name)
        if info:
            favorite_items[item_name] = info
            await query.message.reply_text(f"⭐ Добавлено в избранное: {item_name}", reply_markup=main_keyboard())
    elif query.data == "scan":
        await scan(query, context)
    elif query.data == "back":
        await query.message.reply_text("Выберите действие:", reply_markup=main_keyboard())

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if waiting_for_input.get(user_id) == "add":
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
        del waiting_for_input[user_id]
    else:
        await search_item(update, context)

async def search_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    if len(prices) == 2:
        min_price, max_price = prices
    elif len(prices) == 1:
        min_price, max_price = 0, prices[0]
    else:
        min_price, max_price = 0, 999

    search_results.clear()
    found = []

    try:
        response = requests.get(API_URL)
        data = response.json()

        for entry in data:
            name = entry.get("market_hash_name", "")
            item_url = entry.get("item_page", "")
            price = entry.get("min_price")

            if "graffiti" in name.lower() or not price:
                continue

            if normalize(item_name).issubset(normalize(name)):
                price_f = float(price)
                if min_price <= price_f <= max_price:
                    search_results[name] = {"min": min_price, "max": max_price}
                    found.append(f"{name} — {price}€\n🔗 {item_url}")
                    await update.message.reply_text(
                        f"{name} — {price}€\n🔗 {item_url}",
                        reply_markup=InlineKeyboardMarkup(
                            [[InlineKeyboardButton("⭐ В избранное", callback_data=f"fav|{name}")]]
                        )
                    )

        if not found:
            await update.message.reply_text("Ничего не найдено.", reply_markup=main_keyboard())

    except Exception as e:
        logger.error(f"Ошибка при поиске: {e}")
        await update.message.reply_text("Произошла ошибка при поиске.", reply_markup=main_keyboard())

async def scan(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    found = []
    try:
        response = requests.get(API_URL)
        data = response.json()

        for entry in data:
            name = entry.get("market_hash_name", "")
            min_price = entry.get("min_price")
            item_url = entry.get("item_page", "")

            if "graffiti" in name.lower() or not min_price:
                continue

            name_set = normalize(name)
            for item_name, price_range in items_to_search.items():
                if normalize(item_name).issubset(name_set):
                    price = float(min_price)
                    if price_range["min"] <= price <= price_range["max"]:
                        found.append(f"{name} за {min_price}€\n🔗 {item_url}")
                        break

            for item_name, price_range in favorite_items.items():
                if normalize(item_name).issubset(name_set):
                    price = float(min_price)
                    if price <= price_range["max"]:
                        await context.bot.send_message(
                            chat_id=update_or_query.effective_chat.id,
                            text=f"⭐ Найдено в избранном: {name} за {min_price}€\n🔗 {item_url}"
                        )

    except Exception as e:
        logger.error(f"Ошибка при сканировании: {e}")
        await update_or_query.message.reply_text("Ошибка при сканировании.", reply_markup=main_keyboard())
        return

    if found:
        await update_or_query.message.reply_text("Найдены предметы:\n\n" + "\n\n".join(found), reply_markup=main_keyboard())
    else:
        await update_or_query.message.reply_text("Ничего не найдено.", reply_markup=main_keyboard())

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.run_polling()

if __name__ == '__main__':
    main()
