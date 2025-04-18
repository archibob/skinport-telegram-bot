import logging
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from apscheduler.schedulers.background import BackgroundScheduler

# 
TELEGRAM_BOT_TOKEN = "8095985098:AAGmSZ1JZFunP2un1392Uh4gUg7LY3AjD6A"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Хранилища
items_to_search = {}
favorite_items = {}  # user_id -> { item_name: {min, max, quality} }
waiting_for_input = {}

# Упрощение названий
def normalize(text):
    text = re.sub(r'\(.*?\)', '', text)
    text = text.lower().replace("-", " ").replace("|", " ").strip()
    return set(text.split())

# Главное меню
def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить", callback_data="add")],
        [InlineKeyboardButton("📋 Список", callback_data="list")],
        [InlineKeyboardButton("➕ В избранное", callback_data="add_favorite")],
        [InlineKeyboardButton("⭐ Избранное", callback_data="favorites")],
        [InlineKeyboardButton("🔍 Сканировать", callback_data="scan")]
    ])

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите действие:", reply_markup=main_keyboard())

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "add":
        waiting_for_input[user_id] = "add"
        await query.edit_message_text("Введите название, цену и качество (опц.):", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]]))

    elif query.data == "add_favorite":
        waiting_for_input[user_id] = "favorite"
        await query.edit_message_text("Введите название, цену и качество (опц.) для избранного:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]]))

    elif query.data == "list":
        if not items_to_search:
            await query.edit_message_text("Список пуст.", reply_markup=main_keyboard())
            return
        keyboard = [[InlineKeyboardButton(f"❌ {name}", callback_data=f"delete|{name}") for name in items_to_search]]
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
        await query.edit_message_text("Ваши предметы:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("delete|"):
        name = query.data.split("|", 1)[1]
        if name in items_to_search:
            del items_to_search[name]
        await query.edit_message_text(f"Удалено: {name}", reply_markup=main_keyboard())

    elif query.data == "favorites":
        user_favs = favorite_items.get(user_id, {})
        if not user_favs:
            await query.edit_message_text("Избранное пусто.", reply_markup=main_keyboard())
            return
        keyboard = [[InlineKeyboardButton(f"❌ {name}", callback_data=f"remove_favorite|{name}") for name in user_favs]]
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
        await query.edit_message_text("Избранное:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("remove_favorite|"):
        name = query.data.split("|", 1)[1]
        favorite_items.get(user_id, {}).pop(name, None)
        await query.edit_message_text(f"Удалено из избранного: {name}", reply_markup=main_keyboard())

    elif query.data == "scan":
        await scan(query, context)

    elif query.data == "back":
        await query.edit_message_text("Выберите действие:", reply_markup=main_keyboard())

# Обработка текстовых сообщений
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    mode = waiting_for_input.get(user_id)

    if not mode:
        return

    text = update.message.text.strip()
    parts = text.split()

    # Выделим цены и возможное качество
    prices, quality = [], None
    quality_keywords = {"factory", "minimal", "field", "well", "battle"}
    while parts:
        part = parts[-1].lower()
        if re.match(r"\d+([.,]\d+)?", part):
            prices.insert(0, float(parts.pop().replace(",", ".")))
        elif any(k in part for k in quality_keywords):
            quality = part
            parts.pop()
        else:
            break

    item_name = " ".join(parts).lower()
    if not item_name:
        await update.message.reply_text("Название не распознано.", reply_markup=main_keyboard())
        return

    min_price, max_price = 0, 999
    if len(prices) == 2:
        min_price, max_price = prices
    elif len(prices) == 1:
        max_price = prices[0]

    item_data = {"min": min_price, "max": max_price, "quality": quality}

    if mode == "add":
        items_to_search[item_name] = item_data
        await update.message.reply_text(f"✅ Добавлен: {item_name} от {min_price}€ до {max_price}€", reply_markup=main_keyboard())

    elif mode == "favorite":
        favorite_items.setdefault(user_id, {})[item_name] = item_data
        await update.message.reply_text(f"✅ В избранное: {item_name} от {min_price}€ до {max_price}€", reply_markup=main_keyboard())

    waiting_for_input.pop(user_id, None)

# Проверка соответствия качества
def match_quality(item_name, expected_quality):
    if not expected_quality:
        return True
    return expected_quality in item_name.lower()

# Сканирование
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

            if not min_price or "graffiti" in name.lower():
                continue

            name_set = normalize(name)
            min_price_f = float(min_price)

            # Общие предметы
            for item_name, rule in items_to_search.items():
                if normalize(item_name).issubset(name_set) and match_quality(name, rule.get("quality")):
                    if rule["min"] <= min_price_f <= rule["max"]:
                        found.append(f"{name} за {min_price}€\n🔗 {item_url}")
                        break

            # Избранное пользователя
            for fav_name, rule in favorite_items.get(user_id, {}).items():
                if normalize(fav_name).issubset(name_set) and match_quality(name, rule.get("quality")):
                    if rule["min"] <= min_price_f <= rule["max"]:
                        found.append(f"⭐ {name} за {min_price}€\n🔗 {item_url}")
                        break

    except Exception as e:
        logger.error(f"Ошибка при сканировании: {e}")
        await update_or_query.edit_message_text("Ошибка при сканировании.", reply_markup=main_keyboard())
        return

    msg = "\n\n".join(found) if found else "Ничего не найдено."
    await update_or_query.edit_message_text(msg, reply_markup=main_keyboard())

# Автоматическое сканирование
async def scheduled_scan(context: ContextTypes.DEFAULT_TYPE):
    found = []
    try:
        response = requests.get(API_URL)
        data = response.json()

        for entry in data:
            name = entry.get("market_hash_name", "")
            min_price = entry.get("min_price")
            item_url = entry.get("item_page", "")

            if not min_price or "graffiti" in name.lower():
                continue

            name_set = normalize(name)
            min_price_f = float(min_price)

            for user_id, favs in favorite_items.items():
                for fav_name, rule in favs.items():
                    if normalize(fav_name).issubset(name_set) and match_quality(name, rule.get("quality")):
                        if rule["min"] <= min_price_f <= rule["max"]:
                            found.append(f"⭐ {name} за {min_price}€\n🔗 {item_url}")
                            break

    except Exception as e:
        logger.error(f"Ошибка при авто-сканировании: {e}")
        return

    if found:
        msg = "Новые предметы:\n\n" + "\n\n".join(found)
        context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)

        for user_id in favorite_items:
            try:
                context.bot.send_message(chat_id=user_id, text=msg)
            except Exception as e:
                logger.warning(f"Не удалось отправить пользователю {user_id}: {e}")

# Планировщик
def start_scheduled_scan(app: Application):
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_scan, 'interval', minutes=2, args=[app])
    scheduler.start()

# Запуск бота
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    start_scheduled_scan(app)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
