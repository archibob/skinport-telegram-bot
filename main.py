import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = "8095985098:AAGmSZ1JZFunP2un1392Uh4gUg7LY3AjD6A"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальные словари для хранения данных по пользователям
user_states = {}
items_to_search = {}
favorite_items = {}

# Кнопки главного меню
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить в список", callback_data="add_to_list")],
        [InlineKeyboardButton("⭐ Добавить в избранное", callback_data="add_to_favorites")],
        [InlineKeyboardButton("📜 Список", callback_data="list")],
        [InlineKeyboardButton("⭐ Избранное", callback_data="favorites")],  # Кнопка для избранного
        [InlineKeyboardButton("🔍 Сканировать", callback_data="scan")]
    ])

# Кнопки для сканирования
def get_scan_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Повторить сканирование", callback_data="scan")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
    ])

# Кнопки для удаления
def get_delete_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Удалить", callback_data="delete")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
    ])

# Обработчик /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Выбери действие:", reply_markup=get_main_keyboard())

# Обработка нажатий на кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "add_to_list":
        user_states[user_id] = "awaiting_item_name_list"
        await query.edit_message_text("Введите название предмета для добавления в список:")
    elif query.data == "add_to_favorites":
        user_states[user_id] = "awaiting_item_name_favorites"
        await query.edit_message_text("Введите название предмета для добавления в избранное:")
    elif query.data == "list":
        user_items = items_to_search.get(user_id, {})
        if not user_items:
            await query.edit_message_text("Список пуст.", reply_markup=get_main_keyboard())
            return
        keyboard = [
            [InlineKeyboardButton(f"❌ {name}", callback_data=f"delete|{name}")] for name in user_items
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
        await query.edit_message_text("Отслеживаемые предметы:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "favorites":
        user_favs = favorite_items.get(user_id, {})
        if not user_favs:
            await query.edit_message_text("Избранное пусто.", reply_markup=get_main_keyboard())
            return
        keyboard = [
            [InlineKeyboardButton(f"❌ {name}", callback_data=f"delete_fav|{name}")] for name in user_favs
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
        await query.edit_message_text("Избранные предметы:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "scan":
        await scan(update, context)
    elif query.data.startswith("delete|"):
        name = query.data.split("|", 1)[1]
        if user_id in items_to_search and name in items_to_search[user_id]:
            del items_to_search[user_id][name]
            await query.edit_message_text(f"Удалено: {name}", reply_markup=get_main_keyboard())
    elif query.data.startswith("delete_fav|"):  # Обработка удаления из избранного
        name = query.data.split("|", 1)[1]
        if user_id in favorite_items and name in favorite_items[user_id]:
            del favorite_items[user_id][name]
            await query.edit_message_text(f"Удалено из избранного: {name}", reply_markup=get_main_keyboard())
    elif query.data == "back":
        await query.edit_message_text("Главное меню:", reply_markup=get_main_keyboard())

# Обработка сообщений (добавление предмета)
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    state = user_states.get(user_id)

    if state == "awaiting_item_name_list":
        context.user_data["item_name"] = update.message.text
        user_states[user_id] = "awaiting_price_range_list"
        await update.message.reply_text("Введите минимальную и максимальную цену через пробел (например: 50 120):")
    elif state == "awaiting_item_name_favorites":
        context.user_data["item_name"] = update.message.text
        user_states[user_id] = "awaiting_price_range_favorites"
        await update.message.reply_text("Введите минимальную и максимальную цену через пробел (например: 50 120):")
    elif state == "awaiting_price_range_list":
        try:
            min_price, max_price = map(float, update.message.text.split())
            item_name = context.user_data["item_name"]
            if user_id not in items_to_search:
                items_to_search[user_id] = {}
            items_to_search[user_id][item_name] = {"min": min_price, "max": max_price}

            user_states[user_id] = None
            await update.message.reply_text(f"Добавлено в список: {item_name} ({min_price}-{max_price}€)", reply_markup=get_main_keyboard())
        except:
            await update.message.reply_text("Ошибка формата. Введите цены через пробел (например: 50 120).")
    elif state == "awaiting_price_range_favorites":
        try:
            min_price, max_price = map(float, update.message.text.split())
            item_name = context.user_data["item_name"]
            if user_id not in favorite_items:
                favorite_items[user_id] = {}
            favorite_items[user_id][item_name] = {"min": min_price, "max": max_price}

            user_states[user_id] = None
            await update.message.reply_text(f"Добавлено в избранное: {item_name} ({min_price}-{max_price}€)", reply_markup=get_main_keyboard())
        except:
            await update.message.reply_text("Ошибка формата. Введите цены через пробел (например: 50 120).")

# Сканирование по команде
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_items = items_to_search.get(user_id, {})
    user_favs = favorite_items.get(user_id, {})
    url = API_URL
    found = []

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

            # Поиск в обычных
            for item_name, price_range in user_items.items():
                item_set = normalize(item_name)
                if item_set.issubset(name_set) and min_price:
                    min_price_f = float(min_price)
                    if price_range["min"] <= min_price_f <= price_range["max"]:
                        found.append(f"{name} за {min_price}€\n🔗 {item_url}")
                        break

            # Поиск в избранных
            for item_name, price_range in user_favs.items():
                item_set = normalize(item_name)
                if item_set.issubset(name_set) and min_price:
                    min_price_f = float(min_price)
                    if price_range["min"] <= min_price_f <= price_range["max"]:
                        found.append(f"⭐ Избранное: {name} за {min_price}€\n🔗 {item_url}")
                        break

        if found:
            await context.bot.send_message(chat_id=user_id, text="Найдено:\n\n" + "\n\n".join(found), reply_markup=get_scan_keyboard())
        else:
            await context.bot.send_message(chat_id=user_id, text="Ничего не найдено.", reply_markup=get_scan_keyboard())
    except Exception as e:
        logger.error(f"Ошибка при сканировании: {e}")
        await context.bot.send_message(chat_id=user_id, text="Произошла ошибка при сканировании.")

# Автоматическое сканирование каждые 2 минуты
async def scheduled_scan(application):
    url = API_URL
    try:
        response = requests.get(url)
        data = response.json()

        for user_id, user_favs in favorite_items.items():
            user_found = []
            user_items = items_to_search.get(user_id, {})

            for entry in data:
                name = entry.get("market_hash_name", "")
                min_price = entry.get("min_price")
                item_url = entry.get("item_page", "")

                if "graffiti" in name.lower():
                    continue

                name_set = normalize(name)

                for item_name, price_range in user_items.items():
                    item_set = normalize(item_name)
                    if item_set.issubset(name_set) and min_price:
                        min_price_f = float(min_price)
                        if price_range["min"] <= min_price_f <= price_range["max"]:
                            user_found.append(f"{name} за {min_price}€\n🔗 {item_url}")
                            break

                for item_name, price_range in user_favs.items():
                    item_set = normalize(item_name)
                    if item_set.issubset(name_set) and min_price:
                        min_price_f = float(min_price)
                        if price_range["min"] <= min_price_f <= price_range["max"]:
                            user_found.append(f"⭐ Избранное: {name} за {min_price}€\n🔗 {item_url}")
                            break

            if user_found:
                await application.bot.send_message(chat_id=user_id, text="Найдены предметы:\n\n" + "\n\n".join(user_found))

    except Exception as e:
        logger.error(f"Ошибка при scheduled scan: {e}")

# Запуск бота
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_scan, 'interval', minutes=2, args=[application])
    scheduler.start()

    application.run_polling()

if __name__ == "__main__":
    main()
