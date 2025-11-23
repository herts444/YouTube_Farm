# ДЕПЛОЙ НА СЕРВЕР - ГОТОВО К ЗАПУСКУ!

## Код залит на GitHub
Репозиторий: https://github.com/herts444/YouTube_Farm

## Быстрый деплой (скопируй и выполни)

Открой **новый терминал** и выполни эту команду:

```bash
ssh root@89.116.23.236
```

Пароль: `Beeck1337@@@`

После подключения выполни:

```bash
cd /root && \
git clone https://github.com/herts444/YouTube_Farm.git && \
cd YouTube_Farm && \
cp .env.example .env && \
echo "Repository cloned! Configure .env file:" && \
echo "Edit with: nano .env" && \
echo "Then run: docker-compose up -d --build"
```

## Или выполни по шагам:

### 1. Подключись к серверу
```bash
ssh root@89.116.23.236
```
Пароль: `Beeck1337@@@`

### 2. Клонируй репозиторий
```bash
cd /root
git clone https://github.com/herts444/YouTube_Farm.git
cd YouTube_Farm
```

### 3. Настрой .env файл
```bash
cp .env.example .env
nano .env
```

Заполни:
- `TELEGRAM_BOT_TOKEN` - твой токен от @BotFather
- `OPENAI_API_KEY` - ключ от OpenAI
- `ELEVEN_API_KEY` - ключ от ElevenLabs
- остальные настройки по необходимости

Сохрани: `Ctrl+O`, `Enter`, выйди: `Ctrl+X`

### 4. Запусти бота
```bash
docker-compose up -d --build
```

### 5. Проверь статус
```bash
docker-compose ps
docker-compose logs -f
```

## Полезные команды

### Перезапуск
```bash
cd /root/YouTube_Farm
docker-compose restart
```

### Просмотр логов
```bash
docker-compose logs -f youtube_farm_bot
```

### Остановка
```bash
docker-compose down
```

### Обновление кода
```bash
cd /root/YouTube_Farm
git pull origin main
docker-compose up -d --build
```

### Полная переустановка
```bash
cd /root/YouTube_Farm
docker-compose down -v
docker-compose up -d --build
```

## Структура проекта на сервере

```
/root/YouTube_Farm/
├── main.py              # Основной файл бота
├── handlers/            # Обработчики команд
├── utils/               # Утилиты и движки
├── docker-compose.yml   # Docker конфигурация
├── Dockerfile           # Docker образ
├── .env                 # Настройки (создай из .env.example)
└── outputs/             # Сгенерированные видео
```

## Если Docker не установлен

```bash
# Установка Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# Установка Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Проверка
docker --version
docker-compose --version
```

## Автоматический скрипт (если хочешь)

Сохрани это как `deploy.sh` на сервере и запусти `bash deploy.sh`:

```bash
#!/bin/bash
set -e

cd /root

if [ -d "YouTube_Farm" ]; then
    echo "Updating repository..."
    cd YouTube_Farm
    git pull origin main
else
    echo "Cloning repository..."
    git clone https://github.com/herts444/YouTube_Farm.git
    cd YouTube_Farm
fi

if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env - configure it with your API keys!"
    echo "Run: nano .env"
    exit 0
fi

docker-compose down 2>/dev/null || true
docker-compose up -d --build

echo ""
echo "Deployment complete!"
echo "Check status: docker-compose ps"
echo "View logs: docker-compose logs -f"
```

Сделай исполняемым: `chmod +x deploy.sh`

Запусти: `./deploy.sh`

---

**ВАЖНО:** Не забудь настроить .env файл перед запуском бота!
