import logging
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from apscheduler.schedulers.background import BackgroundScheduler

TELEGRAM_BOT_TOKEN = "8095985098:AAGmSZ1JZFunP2un1392Uh4gUg7LY3AjD6A"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

user_items_to_search = {}  # индивидуальные списки предметов
favorite_items = {}  # избранное
waiting_for_input = {}  # ввод предметов

def normalize(text):
    text = re.sub(r'\(.*?\)', '', text)
    text = text.lower().replace("-", " ").replace("|", " ").strip()
    return set(text.split())

def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ Добавить", callback_data="add")],
        [InlineKeyboardButton("📋 Список", callback_data="list")],
        [InlineKeyboardButton("➕ Добавить в избранное", callback_data="add_favorite")],
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

    user_items_to_search.setdefault(user_id, {})
    favorite_items.setdefault(user_id, {})

    if query.data == "add":
        waiting_for_input[user_id] = "add"
        await query.edit_message_text("Введите название предмета и (необязательно) цену:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]]))
    elif query.data == "add_favorite":
        waiting_for_input[user_id] = "favorite"
        await query.edit_message_text("Введите название предмета и (необязательно) цену для добавления в избранное:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]]))
    elif query.data == "list":
        items = user_items_to_search.get(user_id, {})
        if not items:
            await query.edit_message_text("Список пуст.", reply_markup=main_keyboard())
            return
        keyboard = [[InlineKeyboardButton(f"❌ {name}", callback_data=f"delete|{name}")] for name in items.keys()]
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
        await query.edit_message_text("Ваши предметы:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data.startswith("delete|"):
        name = query.data.split("|", 1)[1]
        if name in user_items_to_search.get(user_id, {}):
            del user_items_to_search[user_id][name]
            await query.edit_message_text(f"Удалено: {name}", reply_markup=main_keyboard())
    elif query.data == "scan":
        await scan(query, context)
    elif query.data == "favorites":
        favs = favorite_items.get(user_id, {})
        if not favs:
            await query.edit_message_text("Избранное пусто.", reply_markup=main_keyboard())
            return
        keyboard = [[InlineKeyboardButton(f"❌ {name}", callback_data=f"remove_favorite|{name}")] for name in favs.keys()]
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
        await query.edit_message_text("Ваши избранные предметы:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data.startswith("remove_favorite|"):
        name = query.data.split("|", 1)[1]
        if name in favorite_items.get(user_id, {}):
            del favorite_items[user_id][name]
            await query.edit_message_text(f"Удалено из избранного: {name}", reply_markup=main_keyboard())
    elif query.data == "back":
        await query.edit_message_text("Выберите действие:", reply_markup=main_keyboard())

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    state = waiting_for_input.get(user_id)
    if not state:
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

    if len(prices) == 2:
        min_price, max_price = prices
    elif len(prices) == 1:
        min_price, max_price = 0, prices[0]
    else:
        min_price, max_price = 0, 999

    if state == "add":
        user_items_to_search.setdefault(user_id, {})[item_name] = {"min": min_price, "max": max_price}
        await update.message.reply_text(f"✅ Добавлен: {item_name} от {min_price}€ до {max_price}€", reply_markup=main_keyboard())
    elif state == "favorite":
        favorite_items.setdefault(user_id, {})[item_name] = {"min": min_price, "max": max_price}
        await update.message.reply_text(f"✅ Добавлен в избранное: {item_name} от {min_price}€ до {max_price}€", reply_markup=main_keyboard())

    del waiting_for_input[user_id]

async def scan(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    user_id = update_or_query.from_user.id
    found = []
    try:
        response = requests.get(API_URL)
        data = response.json()

        for entry in data:
            name = entry.get("market_hash_name", "")
            min_price = entry.get("min_price")
            item_url = entry.get("item_page", "")
            if "graffiti" in name.lower():
                continue

            name_set = normalize(name)

            for item_name, price_range in user_items_to_search.get(user_id, {}).items():
                if normalize(item_name).issubset(name_set) and min_price:
                    price = float(min_price)
                    if price_range["min"] <= price <= price_range["max"]:
                        found.append(f"{name} за {min_price}€\n🔗 {item_url}")
                        break

            for item_name, price_range in favorite_items.get(user_id, {}).items():
                if normalize(item_name).issubset(name_set) and min_price:
                    price = float(min_price)
                    if price_range["min"] <= price <= price_range["max"]:
                        found.append(f"⭐ Избранное: {name} за {min_price}€\n🔗 {item_url}")
                        break
    except Exception as e:
        logger.error(f"Ошибка при сканировании: {e}")
        await update_or_query.edit_message_text("Произошла ошибка при сканировании.", reply_markup=main_keyboard())
        return

    if found:
        await update_or_query.edit_message_text("Найдены предметы:\n\n" + "\n\n".join(found), reply_markup=main_keyboard())
    else:
        await update_or_query.edit_message_text("Ничего не найдено.", reply_markup=main_keyboard())

# Плановое сканирование (можно отключить или адаптировать под хранение ID пользователей)
async def scheduled_scan(context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(API_URL)
        data = response.json()
    except Exception as e:
        logger.error(f"Ошибка при регулярном сканировании: {e}")
        return

    for user_id in favorite_items:
        found = []
        for entry in data:
            name = entry.get("market_hash_name", "")
            min_price = entry.get("min_price")
            item_url = entry.get("item_page", "")
            if "graffiti" in name.lower():
                continue
            name_set = normalize(name)
            for item_name, price_range in favorite_items[user_id].items():
                if normalize(item_name).issubset(name_set) and min_price:
                    price = float(min_price)
                    if price_range["min"] <= price <= price_range["max"]:
                        found.append(f"⭐ {name} за {min_price}€\n🔗 {item_url}")
                        break
        if found:
            await context.bot.send_message(user_id, "Новые предметы:\n\n" + "\n\n".join(found))

def start_scheduled_scan(app: Application):
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_scan, 'interval', minutes=5, args=[app])
    scheduler.start()

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    start_scheduled_scan(app)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.run_polling()

if __name__ == '__main__':
    main()
