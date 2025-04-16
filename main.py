import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
import asyncio

logging.basicConfig(level=logging.INFO)
TELEGRAM_BOT_TOKEN = "8095985098:AAGmSZ1JZFunP2un1392Uh4gUg7LY3AjD6A"

# Отслеживаемые и избранные предметы
items_to_track = {}  # {item_name: {"min": 0, "max": 100}}
favorites = {}       # {item_name: {"min": 0, "max": 150}}

# ==== UI ====

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить", callback_data="add_item")],
        [InlineKeyboardButton("📄 Список", callback_data="show_list")],
        [InlineKeyboardButton("⭐ Избранные", callback_data="show_favorites")],
        [InlineKeyboardButton("🔍 Сканировать", callback_data="scan")],
    ])

def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад", callback_data="main_menu")]
    ])

def list_keyboard(items, prefix):
    buttons = []
    for name in items.keys():
        buttons.append([InlineKeyboardButton(f"❌ {name}", callback_data=f"remove_{prefix}_{name}")])
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

# ==== Команды ====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для отслеживания предметов Skinport.", reply_markup=main_keyboard())

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("Сканирую...", reply_markup=back_keyboard())
    else:
        await update.message.reply_text("Сканирую...", reply_markup=back_keyboard())

    # Тут имитируем результат поиска (в реальности будет Selenium или API)
    found_items = [
        {"name": "Sport Gloves | Bronze Morph", "price": 145.0},
        {"name": "Karambit | Doppler", "price": 290.0},
    ]

    for item in found_items:
        name = item["name"]
        price = item["price"]
        msg = f"🧤 Найден предмет: {name} — {price}€"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ В избранное", callback_data=f"fav_add_{name}_{price}")],
        ])

        if query:
            await context.bot.send_message(chat_id=query.message.chat.id, text=msg, reply_markup=keyboard)
        else:
            await update.message.reply_text(msg, reply_markup=keyboard)

# ==== Обработка кнопок ====

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "main_menu":
        await query.edit_message_text("Главное меню:", reply_markup=main_keyboard())

    elif query.data == "add_item":
        context.user_data["awaiting_item"] = True
        await query.edit_message_text("Введите название предмета и максимальную цену (например: `AWP Asiimov 100`)", parse_mode="Markdown")

    elif query.data == "show_list":
        if items_to_track:
            await query.edit_message_text("📄 Ваш список отслеживания:", reply_markup=list_keyboard(items_to_track, "item"))
        else:
            await query.edit_message_text("Список пуст.", reply_markup=back_keyboard())

    elif query.data == "show_favorites":
        if favorites:
            await query.edit_message_text("⭐ Избранные предметы:", reply_markup=list_keyboard(favorites, "fav"))
        else:
            await query.edit_message_text("Список избранного пуст.", reply_markup=back_keyboard())

    elif query.data == "scan":
        await scan(update, context)

    elif query.data.startswith("remove_item_"):
        name = query.data.removeprefix("remove_item_")
        if name in items_to_track:
            del items_to_track[name]
        await query.edit_message_text("📄 Ваш список отслеживания:", reply_markup=list_keyboard(items_to_track, "item"))

    elif query.data.startswith("remove_fav_"):
        name = query.data.removeprefix("remove_fav_")
        if name in favorites:
            del favorites[name]
        await query.edit_message_text("⭐ Избранные предметы:", reply_markup=list_keyboard(favorites, "fav"))

    elif query.data.startswith("fav_add_"):
        _, name, price = query.data.split("_", 2)
        full_name = name.replace("%20", " ")  # если были пробелы
        try:
            favorites[full_name] = {"min": 0, "max": float(price)}
            await query.edit_message_text(f"⭐ {full_name} добавлен в избранное!", reply_markup=back_keyboard())
        except ValueError:
            await query.edit_message_text("Ошибка при добавлении в избранное.", reply_markup=back_keyboard())

# ==== Сообщения ====

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_item"):
        parts = update.message.text.rsplit(" ", 1)
        if len(parts) != 2:
            await update.message.reply_text("Формат: <название> <макс. цена>")
            return

        name, max_price_str = parts
        try:
            max_price = float(max_price_str.replace(",", "."))
        except ValueError:
            await update.message.reply_text("Неверная цена.")
            return

        items_to_track[name.lower()] = {"min": 0, "max": max_price}
        context.user_data["awaiting_item"] = False
        await update.message.reply_text(f"✅ Добавлен: {name} до {max_price}€", reply_markup=main_keyboard())

# ==== Команда /fav ====

async def add_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Формат: /fav <название> <макс. цена>")
        return

    *name_parts, max_price_str = context.args
    name = " ".join(name_parts)

    try:
        max_price = float(max_price_str.replace(",", "."))
    except ValueError:
        await update.message.reply_text("Некорректная цена.")
        return

    favorites[name.lower()] = {"min": 0, "max": max_price}
    await update.message.reply_text(f"⭐ Добавлено в избранное: {name} до {max_price}€", reply_markup=main_keyboard())

# ==== main ====

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("fav", add_favorite))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
