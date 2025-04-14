import requests
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

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

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("Ошибка отправки в Telegram:", response.text)
    except Exception as e:
        print("Ошибка Telegram:", e)

def start(update, context):
    """Начальный обработчик команды /start. Отправляет кнопку для поиска."""
    keyboard = [
        [InlineKeyboardButton("Поиск", callback_data='search')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Нажмите кнопку, чтобы начать поиск товаров.", reply_markup=reply_markup)

def button(update, context):
    """Обрабатываем нажатие на кнопку 'Поиск'."""
    query = update.callback_query
    query.answer()

    # Выполняем поиск товаров
    check_items()

    query.edit_message_text(text="Поиск завершен. Результаты отправлены в чат.")

def check_items():
    """Функция поиска товаров по фильтрам и отправки результата в Telegram."""
    try:
        headers = {"Accept-Encoding": "br"}
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

        found = False
        for item in items:
            market_name = item.get("market_hash_name", "")
            offers = item.get("items", [])

            if not offers:  # Если у товара нет предложений, пропускаем
                continue

            print(f"Проверяется товар: {market_name}")

            for offer in offers:
                item_id = offer.get("id")
                price_eur = offer.get("price")

                if price_eur is None:
                    continue

                print(f"    Цена товара: {price_eur} EUR")

                for keyword, max_price in TARGET_ITEMS.items():
                    if keyword.lower() in market_name.lower():
                        if price_eur <= max_price:
                            message = f"🔔 Найдено:\n{market_name}\n💶 Цена: {price_eur} EUR"
                            print(message)
                            send_telegram_message(message)
                            found = True
                            break

        if not found:
            print("Ничего не найдено.")
            send_telegram_message("❗️ Не найдено товаров по запросу.")

    except Exception as e:
        error_msg = f"❗ Ошибка при выполнении скрипта: {e}"
        print(error_msg)
        send_telegram_message(error_msg)

def main():
    """Запускаем бота."""
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
