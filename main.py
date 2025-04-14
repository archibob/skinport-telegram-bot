import requests
import time
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Ключевые слова и максимальные цены (в евро)
ITEMS_PRICE_LIMITS = {
    "Sport Gloves | Bronze Morph": 150,
    "Talon Knife": 300,
    "AWP | Asiimov (Battle-Scarred)": 75
}

# Список предметов для отслеживания
tracked_items = list(ITEMS_PRICE_LIMITS.keys())

def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("Ошибка отправки в Telegram:", response.text)
    except Exception as e:
        print("Ошибка Telegram:", e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я готов искать предметы для тебя! Используй /add <item>, /remove <item> и /list для управления предметами.")

async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        item_name = " ".join(context.args)
        if item_name not in tracked_items:
            tracked_items.append(item_name)
            await update.message.reply_text(f"Добавлен предмет для отслеживания: {item_name}")
        else:
            await update.message.reply_text(f"Предмет {item_name} уже отслеживается.")
    else:
        await update.message.reply_text("Пожалуйста, укажите название предмета для добавления.")

async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        item_name = " ".join(context.args)
        if item_name in tracked_items:
            tracked_items.remove(item_name)
            await update.message.reply_text(f"Удален предмет из отслеживания: {item_name}")
        else:
            await update.message.reply_text(f"Предмет {item_name} не найден в списке.")
    else:
        await update.message.reply_text("Пожалуйста, укажите название предмета для удаления.")

async def list_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if tracked_items:
        items = "\n".join(tracked_items)
        await update.message.reply_text(f"Список отслеживаемых предметов:\n{items}")
    else:
        await update.message.reply_text("Нет предметов для отслеживания.")

def check_items():
    try:
        headers = {
            "Accept-Encoding": "br",
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(API_URL, headers=headers)
        print(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            error_text = f"❌ Ошибка при запросе к Skinport: {response.status_code}\n{response.text}"
            print(error_text)
            send_telegram_message(error_text)
            return

        try:
            items = response.json()
        except Exception as e:
            print("Ошибка при парсинге JSON:", e)
            send_telegram_message(f"❗️ Ошибка при парсинге JSON: {e}")
            return

        print(f"Получено {len(items)} товаров")

        matches_found = 0

        for item in items:
            market_name = item.get("market_hash_name", "")
            price = item.get("min_price", None)
            item_url = item.get("item_page", "")

            # Логирование для отладки
            print(f"Проверка товара: {market_name}, Цена: {price}, Ссылка: {item_url}")

            # Проверка на отслеживаемые предметы
            for tracked_item in tracked_items:
                if re.search(tracked_item, market_name, re.IGNORECASE):
                    print(f"Найдено соответствие для: {market_name}")
                    if price is not None and price <= ITEMS_PRICE_LIMITS.get(tracked_item, 0):
                        message = f"🔔 Найден предмет:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                        print(message)
                        send_telegram_message(message)
                        matches_found += 1

        if matches_found == 0:
            print("Ничего не найдено.")
            send_telegram_message("⚠️ Ничего не найдено из интересующих предметов.")

    except Exception as e:
        error_msg = f"❗ Ошибка при выполнении скрипта: {e}"
        print(error_msg)
        send_telegram_message(error_msg)

# 🔁 Запуск в цикле
async def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_item))
    application.add_handler(CommandHandler("remove", remove_item))
    application.add_handler(CommandHandler("list", list_items))

    # Запуск бота
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

    # Периодический запуск функции проверки товаров
    while True:
        check_items()
        time.sleep(120)  # Пауза 2 минуты
