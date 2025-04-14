import requests
from bs4 import BeautifulSoup
import re
import time

TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
BASE_URL = "https://skinport.com/ru/market?cat=Rifle&item=Asiimov&type=AWP&exterior=1&sort=price&order=asc"

ITEMS_PRICE_LIMITS = {
    "Sport Gloves | Bronze Morph": 150,
    "Talon Knife": 300,
    "AWP | Asiimov (Battle-Scarred)": 75
}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("Ошибка отправки в Telegram:", response.text)
    except Exception as e:
        print("Ошибка Telegram:", e)

def check_items():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(BASE_URL, headers=headers)
        if response.status_code != 200:
            error_text = f"❌ Ошибка при запросе к Skinport: {response.status_code}\n{response.text}"
            print(error_text)
            send_telegram_message(error_text)
            return

        # Парсинг HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Ищем все товары
        items = soup.find_all("div", class_="ItemInfo__name")

        matches_found = 0
        for item in items:
            market_name = item.get_text(strip=True)
            item_url = item.find_parent('a')['href']
            price = float(item.find_next('div', class_="ItemInfo__price").get_text(strip=True).replace("€", "").replace(",", "."))
            
            print(f"Товар: {market_name}, Цена: {price}, Ссылка: {item_url}")

            if price is not None:
                # Проверка для "Sport Gloves | Bronze Morph"
                if re.search(r"Sport Gloves\s*\|\s*Bronze Morph", market_name) and price <= ITEMS_PRICE_LIMITS["Sport Gloves | Bronze Morph"]:
                    message = f"🔔 Найдены перчатки:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(message)
                    send_telegram_message(message)
                    matches_found += 1

                # Talon Knife
                if "talon knife" in market_name.lower() and price <= ITEMS_PRICE_LIMITS["Talon Knife"]:
                    message = f"🔔 Найден нож:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(message)
                    send_telegram_message(message)
                    matches_found += 1

                # AWP | Asiimov (Battle-Scarred)
                if re.search(r"AWP\s*\|\s*Asiimov", market_name, re.IGNORECASE) and "Battle-Scarred" in market_name:
                    if price <= ITEMS_PRICE_LIMITS["AWP | Asiimov (Battle-Scarred)"]:
                        message = f"🔔 Найдена AWP Asiimov (Battle-Scarred):\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
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
while True:
    check_items()
    time.sleep(120)  # Пауза 2 минуты
