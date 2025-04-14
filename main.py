import requests
from bs4 import BeautifulSoup
from telegram import Bot

# === ТВОИ ДАННЫЕ ===
TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
CHAT_ID = "388895285"
# ===================

# Настройка отслеживания
SKIN_NAME = "Talon Knife"  # Замени на название скина, за которым хочешь следить
URL = "https://skinport.com/market?cat=Knife&T=Talon%20Knife"  # Ссылка на страницу с нужными скинами
PRICE_LIMIT = 300  # Максимальная цена в евро

bot = Bot(token=TOKEN)

# Функция для парсинга
def check_price():
    try:
        response = requests.get(URL)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Найти все товары на странице
        items = soup.find_all('div', class_='ItemPreview-itemInfo')
        if not items:
            print("Не найдено товаров на странице.")
            return

        print(f"Полученные товары: {len(items)}")

        for item in items:
            # Извлечение информации о товаре
            price_tag = item.find('div', class_='ItemPreview-priceValue')
            name_tag = item.find('div', class_='ItemPreview-itemTitle')
            description_tag = item.find('div', class_='ItemPreview-itemText')

            price_text = price_tag.text.replace("€", "").replace(",", ".")
            try:
                price = float(price_text)
            except ValueError:
                continue  # Если цена некорректная, пропускаем

            name = name_tag.text
            description = description_tag.text

            print(f"Найден товар: {name} с ценой {price}")  # Логируем найденный товар

            if SKIN_NAME in name and price <= PRICE_LIMIT:
                bot.send_message(chat_id=CHAT_ID, text=f"💥 Найден {name} за {price}€\n{URL}")
                break
    except Exception as e:
        print(f"Ошибка: {e}")

# Запуск проверки с интервалом
while True:
    check_price()
    time.sleep(300)  # Проверка каждые 5 минут
