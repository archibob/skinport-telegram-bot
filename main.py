from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
from telegram import Bot

# === ТВОИ ДАННЫЕ ===
TOKEN = "8095985098:AAG0DtGHnzq5wXuwo2YlsdpflRvNHuG6glU"
CHAT_ID = "388895285"

# Настройки отслеживания
SKIN_NAME = "Talon Knife"  # Замени на название скина, за которым хочешь следить
URL = "https://skinport.com/market?cat=Knife&T=Talon%20Knife"  # Ссылка на страницу с нужными скинами
PRICE_LIMIT = 300  # Максимальная цена в евро

bot = Bot(token=TOKEN)

# Настройка ChromeDriver
chrome_options = Options()
chrome_options.add_argument("--headless")  # Запуск в фоновом режиме, без интерфейса
chrome_driver_path = "/path/to/chromedriver"  # Укажи путь к твоему chromedriver

def check_price():
    try:
        # Инициализация драйвера
        driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)
        driver.get(URL)

        # Даем время на загрузку страницы (можно увеличить время, если страница медленная)
        time.sleep(5)

        # Найти все элементы с товарами
        items = driver.find_elements(By.CLASS_NAME, "ItemPreview-itemInfo")

        if not items:
            print("Не найдено товаров на странице.")
            driver.quit()
            return

        print(f"Полученные товары: {len(items)}")

        for item in items:
            price_tag = item.find_element(By.CLASS_NAME, "ItemPreview-priceValue")
            name_tag = item.find_element(By.CLASS_NAME, "ItemPreview-itemTitle")
            description_tag = item.find_element(By.CLASS_NAME, "ItemPreview-itemText")

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

        driver.quit()
    except Exception as e:
        print(f"Ошибка: {e}")

# Запуск проверки с интервалом
while True:
    check_price()
    time.sleep(300)  # Проверка каждые 5 минут
