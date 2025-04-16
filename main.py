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
favorite_items = {}  # Здесь теперь будем хранить избранные предметы для каждого пользователя
waiting_for_input = {}

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

    if query.data == "add":
        waiting_for_input[user_id] = "add"
        await query.edit_message_text("Введите название предмета, качество (необязательно) и (необязательно) цену:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]]))
    elif query.data == "add_favorite":  
        waiting_for_input[user_id] = "favorite"
        await query.edit_message_text("Введите название предмета, качество (необязательно) и (необязательно) цену для добавления в избранное:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back")]]))
    elif query.data == "list":
        if not items_to_search:
            await query.edit_message_text("Список пуст.", reply_markup=main_keyboard())
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
            await query.edit_message_text(f"Удалено: {name}", reply_markup=main_keyboard())
    elif query.data == "scan":
        await scan(query, context)
    elif query.data == "favorites":
        user_favorites = favorite_items.get(user_id, {})
        if not user_favorites:
            await query.edit_message_text("Избранное пусто.", reply_markup=main_keyboard())
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
            await query.edit_message_text(f"Удалено из избранного: {name}", reply_markup=main_keyboard())
    elif query.data == "back":
        await query.edit_message_text("Выберите действие:", reply_markup=main_keyboard())

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if waiting_for_input.get(user_id) == "add":
        parts = update.message.text.strip().split()
        if not parts:
            await update.message.reply_text("Название не распознано.", reply_markup=main_keyboard())
            return

        prices = []
        quality = None
        while parts and re.match(r"^\d+([.,]\d+)?$", parts[-1]):
            prices.insert(0, float(parts.pop().replace(",", ".")))

        if parts and re.match(r"^(factory new|minimal wear|field tested|well worn|battle scarred)$", parts[-1].lower()):
            quality = parts.pop()

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

        item_data = {"min": min_price, "max": max_price}
        if quality:
            item_data["quality"] = quality

        items_to_search[item_name] = item_data
        await update.message.reply_text(
            f"✅ Добавлен: {item_name} от {min_price}€ до {max_price}€ (Качество: {quality if quality else 'не указано'})",
            reply_markup=main_keyboard()
        )
        del waiting_for_input[user_id]

    elif waiting_for_input.get(user_id) == "favorite":
        parts = update.message.text.strip().split()
        if not parts:
            await update.message.reply_text("Название не распознано.", reply_markup=main_keyboard())
            return

        prices = []
        quality = None
        while parts and re.match(r"^\d+([.,]\d+)?$", parts[-1]):
            prices.insert(0, float(parts.pop().replace(",", ".")))

        if parts and re.match(r"^(factory new|minimal wear|field tested|well worn|battle scarred)$", parts[-1].lower()):
            quality = parts.pop()

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

        if user_id not in favorite_items:
            favorite_items[user_id] = {}

        favorite_items[user_id][item_name] = {"min": min_price, "max": max_price, "quality": quality}
        await update.message.reply_text(
            f"✅ Добавлен в избранное: {item_name} от {min_price}€ до {max_price}€ (Качество: {quality if quality else 'не указано'})",
            reply_markup=main_keyboard()
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
            item_quality = entry.get("quality", "").lower()

            if "graffiti" in name.lower():
                continue

            name_set = normalize(name)

            # Проверяем обычные предметы
            for item_name, price_range in items_to_search.items():
                item_set = normalize(item_name)
                if item_set.issubset(name_set) and min_price:
                    min_price_f = float(min_price)
                    if price_range["min"] <= min_price_f <= price_range["max"]:
                        if "quality" in price_range:
                            if price_range["quality"] and item_quality != price_range["quality"]:
                                continue
                        found.append(f"{name} за {min_price}€\n🔗 {item_url}")
                        break

            # Проверяем избранные предметы только для текущего пользователя
            if user_id in favorite_items:
                for item_name, price_range in favorite_items[user_id].items():
                    item_set = normalize(item_name)
                    if item_set.issubset(name_set) and min_price:
                        min_price_f = float(min_price)
                        if price_range["min"] <= min_price_f <= price_range["max"]:
                            if "quality" in price_range:
                                if price_range["quality"] and item_quality != price_range["quality"]:
                                    continue
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
