import logging
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# Токен и ID чата
TELEGRAM_BOT_TOKEN = "8095985098:AAGmSZ1JZFunP2un1392Uh4gUg7LY3AjD6A"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://api.skinport.com/v1/items?app_id=730&currency=EUR"

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Хранилище отслеживаемых предметов
items_to_search = {}

# Функция нормализации названий (с удалением ненужных символов)
def normalize(text):
    text = re.sub(r'\(.*?\)', '', text)  # Убираем модификаторы состояния, например (Well-Worn)
    text = text.lower().replace("-", " ").replace("|", " ").strip()  # Преобразуем в нижний регистр и заменяем тире и вертикальные черты на пробелы
    normalized_text = set(text.split())  # Разделяем по пробелам
    logger.info(f"Нормализованный текст: {normalized_text}")
    return normalized_text

# Отправка сообщения в Telegram
async def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            logger.error(f"Ошибка отправки в Telegram: {response.text}")
    except Exception as e:
        logger.error(f"Ошибка Telegram: {e}")

# Создание кнопок
def create_buttons():
    buttons = [
        [InlineKeyboardButton("Добавить предмет", callback_data="add")],
        [InlineKeyboardButton("Удалить предмет", callback_data="remove")],
        [InlineKeyboardButton("Показать список отслеживаемых", callback_data="search")],
        [InlineKeyboardButton("Ручной поиск", callback_data="scan")],
    ]
    return InlineKeyboardMarkup(buttons)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "Привет! Я бот для поиска предметов на Skinport.\n"
        "Нажмите кнопку, чтобы выполнить команду."
    )
    await update.message.reply_text(message, reply_markup=create_buttons())

# Команда /add
async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()  # Ожидаем нажатие
    await update.callback_query.edit_message_text("Введите название предмета и цену, например:\n/add <название> <макс_цена>")

# Команда /remove
async def remove_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()  # Ожидаем нажатие
    await update.callback_query.edit_message_text("Введите название предмета, чтобы удалить.")

# Команда /search
async def search_items(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not items_to_search:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Список отслеживаемых предметов пуст.")
        return

    message = "Отслеживаемые предметы:\n"
    for item, price_range in items_to_search.items():
        message += f"- {item} от {price_range['min']}€ до {price_range['max']}€\n"
    
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(message)

# Команда /scan
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    found = []
    url = API_URL

    try:
        response = requests.get(url)
        data = response.json()
        logger.info(f"Получено {len(data)} предметов от API")

        for entry in data:
            name = entry.get("market_hash_name", "")
            min_price = entry.get("min_price")
            item_url = entry.get("item_page", "")

            # Пропускаем граффити и подобное
            if "graffiti" in name.lower():
                continue

            logger.info(f"Проверка предмета: {name} с ценой {min_price}€")

            name_set = normalize(name)

            for item_name, price_range in items_to_search.items():
                item_set = normalize(item_name)
                if item_set.issubset(name_set) and min_price:
                    min_price_f = float(min_price)
                    if price_range["min"] <= min_price_f <= price_range["max"]:
                        found.append(f"{name} за {min_price}€\n🔗 {item_url}")
                        break

    except Exception as e:
        logger.error(f"Ошибка при сканировании: {e}")
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Произошла ошибка при сканировании.")
        return

    if found:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Найдены предметы:\n\n" + "\n\n".join(found))
    else:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Ничего не найдено.")

# Запуск бота
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(add_item, pattern="^add$"))
    app.add_handler(CallbackQueryHandler(remove_item, pattern="^remove$"))
    app.add_handler(CallbackQueryHandler(search_items, pattern="^search$"))
    app.add_handler(CallbackQueryHandler(scan, pattern="^scan$"))

    logger.info("Бот запускается...")
    app.run_polling()

if __name__ == '__main__':
    main()
