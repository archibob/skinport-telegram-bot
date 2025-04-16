FROM python:3.9-slim

# Устанавливаем необходимые системные зависимости
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем необходимые библиотеки
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копируем код
COPY . /app/

WORKDIR /app

# Запускаем приложение
CMD ["python", "main.py"]
 
