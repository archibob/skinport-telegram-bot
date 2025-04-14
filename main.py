from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import requests

# 🔧 Настройки
TELEGRAM_BOT_TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
TELEGRAM_CHAT_ID = "388895285"
API_URL = "https://skinport.com/ru/market?cat=Rifle&item=Asiimov&type=AWP&exterior=1&sort=price&order=asc"

# 🧲 Ключевые слова и максимальные цены (в евро)
ITEMS_PRICE_LIMITS = {
    "Sport Gloves | Bronze Morph": 150,  # Максимальная цена для этих перчаток
    "Talon Knife": 300,  # Максимальная цена для ножей
    "AWP | Asiimov (Battle-Scarred)": 75  # Максимальная цена для AWP Asiimov (Battle-Scarred)
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
        # Настроим Selenium WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(API_URL)
        time.sleep(5)  # Ожидание загрузки страницы

        # Получим HTML контент страницы после рендеринга
        html = driver.page_source

        # Теперь парсим полученный HTML
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all("div", class_="item-card")

        print(f"Найдено товаров: {len(items)}")

        found = False
        for item in items:
            market_name = item.find("span", class_="item-title").text.strip()  # Название предмета
            price = item.find("span", class_="item-price").text.strip().replace("€", "").strip()  # Цена товара
            price = float(price) if price else 0
            item_url = "https://skinport.com" + item.find("a", class_="item-card-link")["href"]  # Ссылка на товар

            # Логируем товар для отладки
            print(f"Товар: {market_name}, Цена: {price}, Ссылка: {item_url}")

            # Проверка для "Sport Gloves | Bronze Morph"
            if price is not None:
                if re.search(r"Sport Gloves\s*\|\s*Bronze Morph", market_name) and price <= ITEMS_PRICE_LIMITS["Sport Gloves | Bronze Morph"]:
                    message = f"🔔 Найден предмет:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(f"Найден товар: {message}")
                    send_telegram_message(message)
                    found = True

                # Логика для поиска ножей Talon Knife
                elif "talon knife" in market_name.lower() and price <= ITEMS_PRICE_LIMITS["Talon Knife"]:
                    message = f"🔔 Найден нож:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(f"Найден нож: {message}")
                    send_telegram_message(message)
                    found = True

                # Логика для поиска AWP Asiimov (Battle-Scarred)
                if re.search(r"AWP\s*\|\s*Asiimov", market_name, re.IGNORECASE) and "Battle-Scarred" in market_name:
                    print(f"Проверка AWP Asiimov: {market_name} с ценой {price} евро")
                    if price <= ITEMS_PRICE_LIMITS["AWP | Asiimov (Battle-Scarred)"]:
                        message = f"🔔 Найден AWP Asiimov (Battle-Scarred):\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                        print(f"Найден AWP Asiimov: {message}")
                        send_telegram_message(message)
                        found = True

        if not found:
            print("Ничего не найдено.")
            send_telegram_message("⚠️ Ничего не найдено из интересующих предметов.")

        driver.quit()  # Закрываем браузер после выполнения

    except Exception as e:
        error_msg = f"❗ Ошибка при выполнении скрипта: {e}"
        print(error_msg)
        send_telegram_message(error_msg)

# 🔁 Запуск в цикле
while True:
    check_items()
    time.sleep(120)  # Пауза 2 минуты
