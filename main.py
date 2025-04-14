import requests
import re
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Ваши настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# Ключевые слова и максимальные цены (в евро)
ITEMS_PRICE_LIMITS = {
    "Sport Gloves | Bronze Morph": 150,
    "Talon Knife": 300,
    "AWP | Asiimov (Battle-Scarred)": 75,
    "Skeleton Knife": 190
}

# Функция для отправки сообщений в Telegram
async def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("Ошибка отправки в Telegram:", response.text)
    except Exception as e:
        print("Ошибка Telegram:", e)

# Функция для поиска предметов
async def check_items():
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
            await send_telegram_message(error_text)
            return

        try:
            items = response.json()
        except Exception as e:
            print("Ошибка при парсинге JSON:", e)
            await send_telegram_message(f"❗️ Ошибка при парсинге JSON: {e}")
            return

        print(f"Получено {len(items)} товаров")

        matches_found = 0

        for item in items:
            market_name = item.get("market_hash_name", "")
            price = item.get("min_price", None)
            item_url = item.get("item_page", "")

            # Логирование для отладки
            print(f"Проверка товара: {market_name}, Цена: {price}, Ссылка: {item_url}")

            # Проверка на нужные товары
            if "Sport Gloves | Bronze Morph" in market_name:
                if price is not None and price <= ITEMS_PRICE_LIMITS["Sport Gloves | Bronze Morph"]:
                    message = f"🔔 Найдены перчатки:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(message)
                    await send_telegram_message(message)
                    matches_found += 1

            if "Talon Knife" in market_name:
                if price is not None and price <= ITEMS_PRICE_LIMITS["Talon Knife"]:
                    message = f"🔔 Найден нож Talon:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(message)
                    await send_telegram_message(message)
                    matches_found += 1

            if "Skeleton Knife" in market_name:
                if price is not None and price <= ITEMS_PRICE_LIMITS["Skeleton Knife"]:
                    message = f"🔔 Найден нож Skeleton:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(message)
                    await send_telegram_message(message)
                    matches_found += 1

        if matches_found == 0:
            print("Ничего не найдено.")
            await send_telegram_message("⚠️ Ничего не найдено из интересующих предметов.")

    except Exception as e:
        error_msg = f"❗ Ошибка при выполнении скрипта: {e}"
        print(error_msg)
        await send_telegram_message(error_msg)

# Функция для обработки команды /start
async def start(update: Update, context):
    await update.message.reply("Привет! Напиши название предмета и цену для поиска.")

# Функция для обработки сообщений от пользователей
async def handle_message(update: Update, context):
    user_message = update.message.text
    if user_message:
        try:
            # Разделение сообщения на название предмета и цену
            name_price = user_message.split(",")
            if len(name_price) == 2:
                item_name = name_price[0].strip()
                item_price = float(name_price[1].strip())
                ITEMS_PRICE_LIMITS[item_name] = item_price
                await update.message.reply(f"Теперь я буду искать {item_name} до {item_price} евро.")
            else:
                await update.message.reply("Неверный формат. Введите название и цену предмета через запятую.")
        except Exception as e:
            await update.message.reply(f"Ошибка: {e}")

# Основная функция для запуска бота
async def main():
    # Создание объекта Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация команд и обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота с использованием нового синтаксиса
    await application.run_polling()

# Запуск асинхронной функции
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
