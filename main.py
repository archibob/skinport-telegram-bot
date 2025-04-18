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

items_to_search = {}
favorite_items = {}  # Избранные предметы
waiting_for_input = {}

def normalize(text):
    text = re.sub(r'\(.*?\)', '', text)
    text = text.lower().replace("-", " ").replace("|", " ").strip()
    return set(text.split())

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить", callback_data="add")],
        [InlineKeyboardButton("📋 Список", callback_data="list")],
        [InlineKeyboardButton("🔍 Сканировать", callback_data="scan")],
        [InlineKeyboardButton("⭐ Избранное", callback_data="fav_list")],
        [InlineKeyboardButton("➕ В избранное", callback_data="fav_add")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите действие:", reply_markup=get_main_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "add":
        waiting_for_input[user_id] = "add"
        await query.edit_message_text("Введите название предмета и (необязательно) цену:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]]))
    elif query.data == "fav_add":  # Кнопка добавления в избранное
        waiting_for_input[user_id] = "favorite"
        await query.edit_message_text("Введите название предмета и (необязательно) цену для добавления в избранное:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]]))
    elif query.data == "list":
        if not items_to_search:
            await query.edit_message_text("Список пуст.", reply_markup=get_main_keyboard())
            return
        keyboard = [
            [InlineKeyboardButton(f"❌ {name}", callback_data=f"delete|{name}") for name in items_to_search.keys()]
        ]
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
        await query.edit_message_text("Ваши предметы:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data.startswith("delete|"):
        name = query.data.split("|", 1)[1]
        if name in items_to_search:
            del items_to_search[name]
            await query.edit_message_text(f"Удалено: {name}", reply_markup=get_main_keyboard())
    elif query.data == "scan":
        await scan(query, context)
    elif query.data == "fav_list":  # Избранное
        user_favorites = favorite_items.get(user_id, {})
        if not user_favorites:
            await query.edit_message_text("Избранное пусто.", reply_markup=get_main_keyboard())
            return
        keyboard = [
            [InlineKeyboardButton(f"❌ {name}", callback_data=f"remove_favorite|{name}") for name in user_favorites.keys()]
        ]
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back")])
        await query.edit_message_text("Ваши избранные предметы:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data.startswith("remove_favorite|"):
        name = query.data.split("|", 1)[1]
        if user_id in favorite_items and name in favorite_items[user_id]:
            del favorite_items[user_id][name]
            await query.edit_message_text(f"Удалено из избранного: {name}", reply_markup=get_main_keyboard())
    elif query.data == "back":
        await query.edit_message_text("Выберите действие:", reply_markup=get_main_keyboard())

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if waiting_for_input.get(user_id) == "add":
        parts = update.message.text.strip().split()
        if not parts:
            await update.message.reply_text("Название не распознано.", reply_markup=get_main_keyboard())
            return

        prices = []
        while parts and re.match(r"^\d+([.,]\d+)?$", parts[-1]):
            prices.insert(0, float(parts.pop().replace(",", ".")))

        item_name = " ".join(parts).lower()
        if not item_name:
            await update.message.reply_text("Название не распознано.", reply_markup=get_main_keyboard())
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
            reply_markup=get_main_keyboard()
        )
        del waiting_for_input[user_id]

    elif waiting_for_input.get(user_id) == "favorite":
        parts = update.message.text.strip().split()
        if not parts:
            await update.message.reply_text("Название не распознано.", reply_markup=get_main_keyboard())
            return

        prices = []
        while parts and re.match(r"^\d+([.,]\d+)?$", parts[-1]):
            prices.insert(0, float(parts.pop().replace(",", ".")))

        item_name = " ".join(parts).lower()
        if not item_name:
            await update.message.reply_text("Название не распознано.", reply_markup=get_main_keyboard())
            return

        if len(prices) == 2:
            min_price, max_price = prices
        elif len(prices) == 1:
            min_price, max_price = 0, prices[0]
        else:
            min_price, max_price = 0, 999

        if user_id not in favorite_items:
            favorite_items[user_id] = {}

        favorite_items[user_id][item_name] = {"min": min_price, "max": max_price}
        await update.message.reply_text(
            f"✅ Добавлен в избранное: {item_name} от {min_price}€ до {max_price}€",
            reply_markup=get_main_keyboard()
        )
        del waiting_for_input[user_id]

async def scan(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    user_id = update_or_query.from_user.id  # Получаем ID текущего пользователя
    found = []
    url = API_URL

    try:
        response = requests.get(url)
        data = response.json()

        for entry in data:
            name = entry.get("market_hash_name", "")
            min_price = entry.get("min_price")
            item_url = entry.get("item_page", "")

            if "graffiti" in name.lower():
                continue

            name_set = normalize(name)

            # Проверяем обычные предметы
            for item_name, price_range in items_to_search.items():
                item_set = normalize(item_name)
                if item_set.issubset(name_set) and min_price:
                    min_price_f = float(min_price)
                    if price_range["min"] <= min_price_f <= price_range["max"]:
                        found.append(f"{name} за {min_price}€\n🔗 {item_url}")
                        break

            # Проверяем избранные предметы только для текущего пользователя
            if user_id in favorite_items:
                for item_name, price_range in favorite_items[user_id].items():
                    item_set = normalize(item_name)
                    if item_set.issubset(name_set) and min_price:
                        min_price_f = float(min_price)
                        if price_range["min"] <= min_price_f <= price_range["max"]:
                            found.append(f"⭐ Избранное: {name} за {min_price}€\n🔗 {item_url}")
                            break

    except Exception as e:
        logger.error(f"Ошибка при сканировании: {e}")
        await update_or_query.edit_message_text("Произошла ошибка при сканировании.", reply_markup=get_main_keyboard())
        return

    if found:
        await update_or_query.edit_message_text("Найдены предметы:\n\n" + "\n\n".join(found), reply_markup=get_main_keyboard())
    else:
        await update_or_query.edit_message_text("Ничего не найдено.", reply_markup=get_main_keyboard())

# Функция для регулярного сканирования по расписанию
async def scheduled_scan(context):
    found = []
    url = API_URL

    try:
        response = requests.get(url)
        data = response.json()

        for entry in data:
            name = entry.get("market_hash_name", "")
            min_price = entry.get("min_price")
            item_url = entry.get("item_page", "")

            if "graffiti" in name.lower():
                continue

            name_set = normalize(name)

            # Проверяем обычные предметы
            for item_name, price_range in items_to_search.items():
                item_set = normalize(item_name)
                if item_set.issubset(name_set) and min_price:
                    min_price_f = float(min_price)
                    if price_range["min"] <= min_price_f <= price_range["max"]:
                        found.append(f"{name} за {min_price}€\n🔗 {item_url}")
                        break

            # Проверяем избранные предметы только для каждого пользователя
            for user_id, user_favorites in favorite_items.items():
                for item_name, price_range in user_favorites.items():
                    item_set = normalize(item_name)
                    if item_set.issubset(name_set) and min_price:
                        min_price_f = float(min_price)
                        if price_range["min"] <= min_price_f <= price_range["max"]:
                            found.append(f"⭐ Избранное: {name} за {min_price}€\n🔗 {item_url}")
                            break

    except Exception as e:
        logger.error(f"Ошибка при сканировании: {e}")
        return

    if found:
        context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="Найдены предметы:\n\n" + "\n\n".join(found))
    else:
        context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="Ничего не найдено.")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Регулярное сканирование каждую минуту
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_scan, 'interval', minutes=2, args=[application.bot])  # Передаем объект бота
    scheduler.start()

    application.run_polling()

if __name__ == "__main__":
    main()
