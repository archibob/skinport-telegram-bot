RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    chromium-browser \
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
