FROM python:3.9-slim

# Устанавливаем необходимые системные зависимости для Chromium
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    chromium \
    libx11-dev \
    libxcomposite-dev \
    libxdamage-dev \
    libxi-dev \
    libxtst-dev \
    libnss3-dev \
    libgdk-pixbuf2.0-dev \
    libatk-bridge2.0-dev \
    libgtk-3-dev \
    libappindicator3-dev \
    xorg-server-xvfb \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем pip и зависимости Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копируем весь код проекта
COPY . /app/

# Устанавливаем рабочую директорию
WORKDIR /app

# Запуск приложения
CMD ["python", "main.py"]
