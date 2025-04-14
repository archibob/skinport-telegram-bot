import requests
import time
from bs4 import BeautifulSoup
from telegram import Bot

# === ТВОИ ДАННЫЕ ===
TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
CHAT_ID = "388895285"
# ===================

# Настройки отслеживания
SKIN_NAME = "Talon Knife"
URL = "https://skinport.com/market?cat=Knife&T=Talon%20Knife"
PRICE_LIMIT = 300  # Евро

bot = Bot(token=TOKEN)

def check_price():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(URL, headers=headers)
        response.raise_for_status()  # Проверка на успешный ответ от сайта
        soup = BeautifulSoup(response.text, "html.parser")

        items = soup.find_all("div", class_="item-outer")
        print(f"Полученные товары: {len(items)}")  # Логируем количество товаров

        if not items:
            print("Не найдено товаров на странице.")
            return

        for item in items:
            price_tag = item.find("div", class_="item-price")
            name_tag = item.find("div", class_="item-name")

            if not price_tag or not name_tag:
                continue

            price_text = price_tag.get_text(strip=True).replace("€", "").replace(",", ".")
            try:
                price = float(price_text)
            except ValueError:
                continue  # Если цена некорректная, пропускаем

            name = name_tag.get_text(strip=True)

            print(f"Найден товар: {name} с ценой {price}")  # Логируем найденный товар

            if SKIN_NAME in name and price <= PRICE_LIMIT:
                bot.send_message(chat_id=CHAT_ID, text=f"💥 Найден {name} за {price}€\n{URL}")
                break
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

while True:
    check_price()
    time.sleep(300)  # Проверка каждые 5 минут

