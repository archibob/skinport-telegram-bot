from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# Обновлённая команда /scan
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from_name = " ".join(context.args).lower().strip() if context.args else None

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1920, 1080)

    try:
        url = "https://skinport.com/market?app=730"
        if from_name:
            url += f"&q={from_name.replace(' ', '%20')}"

        driver.get(url)
        time.sleep(5)  # Ждём загрузки

        items = driver.find_elements(By.CSS_SELECTOR, "a.css-164ys2a")  # каждый предмет
        logger.info(f"Найдено {len(items)} предметов на странице")

        found = []

        for item in items:
            try:
                name = item.find_element(By.CSS_SELECTOR, ".Line-clamp-2 span").text
                price = item.find_element(By.CSS_SELECTOR, ".font-bold").text.replace("€", "").replace(",", ".")
                url = item.get_attribute("href")
                price_float = float(price)

                logger.info(f"Проверка предмета: {name} за {price_float}€")

                # если есть отслеживаемые
                for item_name, price_range in items_to_search.items():
                    if normalize(item_name).issubset(normalize(name)):
                        if price_range["min"] <= price_float <= price_range["max"]:
                            found.append(f"{name} за {price_float}€\n🔗 {url}")
                            break

                # если ручной поиск /scan <название> 123
                if from_name:
                    if normalize(from_name).issubset(normalize(name)):
                        found.append(f"{name} за {price_float}€\n🔗 {url}")

            except Exception as e:
                logger.warning(f"Ошибка при обработке одного предмета: {e}")
                continue

        if found:
            await update.message.reply_text("Найдены предметы:\n\n" + "\n\n".join(found))
        else:
            await update.message.reply_text("Ничего не найдено.")

    except Exception as e:
        logger.error(f"Ошибка при сканировании через Selenium: {e}")
        await update.message.reply_text("Произошла ошибка при сканировании.")
    finally:
        driver.quit()
