import asyncio
import logging
import json
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from collections import defaultdict

TELEGRAM_BOT_TOKEN = "8095985098:AAGmSZ1JZFunP2un1392Uh4gUg7LY3AjD6A"
TELEGRAM_CHAT_ID = "388895285"

logging.basicConfig(level=logging.INFO)

user_favorites = defaultdict(list)
notified_items = set()

HEADERS = {
    "Accept": "application/json"
}

def get_skinport_items(name):
    response = requests.get(f'https://api.skinport.com/v1/items?app_id=730&currency=EUR', headers=HEADERS)
    if response.status_code != 200:
        return []
    items = response.json()
    return [item for item in items if name.lower() in item['market_hash_name'].lower()]

async def send_notification(item, user_id, context: ContextTypes.DEFAULT_TYPE):
    item_id = f"{item['market_hash_name']}_{item['price']}_{item['item_id']}"
    if item_id in notified_items:
        return
    notified_items.add(item_id)

    message = (
        f"Найден предмет:\n"
        f"Название: {item['market_hash_name']}\n"
        f"Цена: {item['price']} EUR\n"
        f"[Открыть на Skinport](https://skinport.com/item/{item['item_id']})"
    )

    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=message,
        parse_mode='Markdown'
    )

async def scheduled_scan():
    for user_id, items in user_favorites.items():
        for fav in items:
            market_items = get_skinport_items(fav["name"])
            for item in market_items:
                if (
                    item["price"] <= fav["max_price"] and
                    fav["quality"].lower() in item["market_hash_name"].lower()
                ):
                    await send_notification(item, user_id, app.bot.context)

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Идёт сканирование...")
    await scheduled_scan()
    await update.message.reply_text("Сканирование завершено.")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Использование: /add <название> <макс_цена> <качество>")
        return

    name = args[0]
    try:
        max_price = float(args[1])
    except ValueError:
        await update.message.reply_text("Макс_цена должна быть числом.")
        return

    quality = ' '.join(args[2:])
    user_id = update.effective_user.id

    user_favorites[user_id].append({
        "name": name,
        "max_price": max_price,
        "quality": quality
    })

    await update.message.reply_text(f"Добавлен предмет: {name}, до {max_price} EUR, качество: {quality}")

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    favorites = user_favorites[user_id]

    if not favorites:
        await update.message.reply_text("У вас нет избранных предметов.")
        return

    keyboard = [
        [InlineKeyboardButton(f"{fav['name']} ({fav['quality']})", callback_data=str(i))]
        for i, fav in enumerate(favorites)
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите предмет для удаления:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    index = int(query.data)

    try:
        removed = user_favorites[user_id].pop(index)
        await query.edit_message_text(f"Удалён: {removed['name']} ({removed['quality']})")
    except IndexError:
        await query.edit_message_text("Ошибка: предмет не найден.")

async def list_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    favorites = user_favorites[user_id]

    if not favorites:
        await update.message.reply_text("У вас нет избранных предметов.")
        return

    text = "Ваши избранные предметы:\n"
    for i, fav in enumerate(favorites, 1):
        text += f"{i}. {fav['name']} ({fav['quality']}) — до {fav['max_price']} EUR\n"

    await update.message.reply_text(text)

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.bot.context = app

    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("list", list_favorites))
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(CallbackQueryHandler(button))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_scan, "interval", minutes=2)
    scheduler.start()

    print("Бот запущен")
    app.run_polling()
