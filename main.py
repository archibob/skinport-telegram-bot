import requests
from bs4 import BeautifulSoup
import time

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
BASE_URL = "https://skinport.com"

# 🧲 Ключевые слова и максимальные цены (в евро)
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
            "Accept-Encoding": "br",
            "User-Agent": "Mozilla/5.0"
        }

        # Получаем HTML-страницу
        response = requests.get(f"{BASE_URL}/items", headers=headers)
        print(f"Status Code: {response.status_code}")

        if response.status_code != 200:
            error_text = f"❌ Ошибка при запросе к Skinport: {response.status_code}\n{response.text}"
            print(error_text)
            send_telegram_message(error_text)
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        items = soup.find_all("div", class_="ItemPreview")
        print(f"Получено {len(items)} товаров")

        matches_found = 0

        for item in items:
            market_name = item.find("div", class_="ItemPreview-itemName").get_text(strip=True)
            price_text = item.find("div", class_="ItemPreview-priceValue")
            if price_text:
                price = price_text.find("div", class_="Tooltip-link").get_text(strip=True).replace('€', '').replace(',', '.')
                price = float(price)

                item_url = BASE_URL + item.find("a")["href"]

                print(f"Товар: {market_name}, Цена: {price}, Ссылка: {item_url}")

                # Проверка по критериям
                if price <= ITEMS_PRICE_LIMITS["Sport Gloves | Bronze Morph"] and "Sport Gloves | Bronze Morph" in market_name:
                    message = f"🔔 Найдены перчатки:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(message)
                    send_telegram_message(message)
                    matches_found += 1

                if "Talon Knife" in market_name and price <= ITEMS_PRICE_LIMITS["Talon Knife"]:
                    message = f"🔔 Найден нож:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(message)
                    send_telegram_message(message)
                    matches_found += 1

                if "AWP | Asiimov" in market_name and price <= ITEMS_PRICE_LIMITS["AWP | Asiimov (Battle-Scarred)"]:
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
