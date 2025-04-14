def check_items():
    try:
        headers = {
            "Accept-Encoding": "br",
            "User-Agent": "Mozilla/5.0"
        }
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

        matches_found = 0

        for item in items:
            market_name = item.get("market_hash_name", "")
            price = item.get("min_price", None)
            item_url = item.get("item_page", "")

            # Логирование для отладки
            print(f"Проверка товара: {market_name}, Цена: {price}, Ссылка: {item_url}")

            # Проверка на Sport Gloves | Bronze Morph
            if re.search(r"Sport\s*Gloves\s*\|\s*Bronze\s*Morph", market_name, re.IGNORECASE):
                print(f"Совпадение для перчаток: {market_name}")
                if price is not None and price <= ITEMS_PRICE_LIMITS["Sport Gloves | Bronze Morph"]:
                    message = f"🔔 Найдены перчатки:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(message)  # Для отладки
                    send_telegram_message(message)
                    matches_found += 1

            # Проверка на Talon Knife
            if "talon knife" in market_name.lower():
                if price is not None and price <= ITEMS_PRICE_LIMITS["Talon Knife"]:
                    message = f"🔔 Найден нож:\n{market_name}\n💶 Цена: {price} EUR\n🔗 {item_url}"
                    print(message)
                    send_telegram_message(message)
                    matches_found += 1

            # Проверка на AWP | Asiimov (Battle-Scarred)
            if re.search(r"AWP\s*\|\s*Asiimov", market_name, re.IGNORECASE):
                if "Battle-Scarred" in market_name and price is not None and price <= ITEMS_PRICE_LIMITS["AWP | Asiimov (Battle-Scarred)"]:
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
