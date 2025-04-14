import requests
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# 🧲 Названия предметов и их лимиты по цене (в евро)
TARGET_ITEMS = {
    "Talon Knife": 300,
    "Sport Gloves | Bronze Morph": 150
}

# Список уже отправленных товаров (по их ID)
sent_items = set()

async def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("Ошибка отправки в Telegram:", response.text)
    except Exception as e:
        print("Ошибка Telegram:", e)

async def check_items():
    try:
        headers = {"Accept-Encoding": "br"}
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
        found = False

        for item in items:
            market_name = item.get("market_hash_name", "")
            offers = item.get("items", [])

            for offer in offers:
                item_id = offer.get("id")
                price_eur = offer.get("price")

                if item_id in sent_items or price_eur is None:
                    continue

                print(f"Название: {market_name}, Цена: {price_eur:.2f} EUR")

                for keyword, max_price in TARGET_ITEMS.items():
                    if keyword.lower() in market_name.lower() and price_eur <= max_price:
                        message = f"🔔 Найдено:\n{market_name}\n💶 Цена: {price_eur:.2f} EUR"
                        print(message)
                        await send_telegram_message(message)
                        sent_items.add(item_id)
                        found = True
                        break

        if not found:
            print("Ничего не найдено.")
            await send_telegram_message("❗️ Не найдено товаров по запросу.")

    except Exception as e:
        error_msg = f"❗ Ошибка при выполнении скрипта: {e}"
        print(error_msg)
        await send_telegram_message(error_msg)

# Функция для обработки команды /start
async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("Поиск", callback_data='search')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Привет! Нажми на кнопку для поиска товаров.', reply_markup=reply_markup)

# Функция для обработки нажатия кнопки
async def button(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == 'search':
        await check_items()  # Ваш код для поиска товаров и отправки сообщений

# Основная функция
def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()
