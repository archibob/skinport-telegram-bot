import requests
from bs4 import BeautifulSoup
import time

# Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"

# Ссылка на AWP Asiimov Battle-Scarred
SKINPORT_URL = "https://skinport.com/ru/market?cat=Rifle&item=Asiimov&type=AWP&exterior=1&sort=price&order=asc"

# Максимально допустимая цена
PRICE_LIMIT = 75

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("Ошибка отправки в Telegram:", response.text)
    except Exception as e:
        print("Ошибка Telegram:", e)

def check_asiimovs():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        response = requests.get(SKINPORT_URL, headers=headers)
        if response.status_code != 200:
            print(f"Ошибка запроса: {response.status_code}")
            send_telegram_message(f"❌ Ошибка загрузки страницы Skinport: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.select("a[href^='/item/awp-asiimov-battle-scarred']")

        if not items:
            print("❗️Не найдено ни одного элемента на странице.")
            send_telegram_message("❗️ AWP Asiimov (BS) не найден на странице.")
            return

        found = False
        for item in items:
            price_tag = item.select_one(".item__price span")
            if price_tag:
                price_text = price_tag.text.replace("€", "").replace(",", ".").strip()
                try:
                    price = float(price_text)
                    if price <= PRICE_LIMIT:
                        item_url = "https://skinport.com" + item["href"]
                        message = f"🔔 AWP | Asiimov (Battle-Scarred)\n💶 Цена: {price} EUR\n🔗 {item_url}"
                        print(message)
                        send_telegram_message(message)
                        found = True
                except ValueError:
                    continue

        if not found:
            print("Ничего не найдено.")
            send_telegram_message("⚠️ Нет AWP Asiimov (BS) по нужной цене.")

    except Exception as e:
        print("Ошибка при парсинге:", e)
        send_telegram_message(f"❗ Ошибка при парсинге страницы: {e}")

# Основной цикл
while True:
    check_asiimovs()
    time.sleep(120)  # Пауза 2 минуты

