# Recipe Telegram Bot

Telegram-бот для поиска рецептов через [Recipe API](https://github.com/kseniadmay/recipeapi).  
Бот использует REST API для получения рецептов, поиска, случайных рекомендаций и управления избранным.

Backend API проекта:
https://github.com/kseniadmay/RecipeAPI

## Live Demo

**Telegram бот:** [@recipeapibot](https://t.me/recipeapibot)

## Стек технологий

Python 3.14  
python-telegram-bot 22.6  
requests

## Возможности

🔍 **Поиск рецептов** по названию или ингредиентам  
🎲 **Случайный рецепт** для вдохновения или чтобы не придумывать, что готовить  
⚡ **Быстрые рецепты** до 30 минут  
⭐ **Избранное** - сохранение любимых рецептов  
🔐 **Авторизация** через API

## Команды

`/start` - запуск бота  
`/help` - справка  
`/login` - авторизация  
`/register` - регистрация  
`/logout` - выход из аккаунта

## Локальный запуск (для разработки)

### 1. Клонирование репозитория
```bash
git clone https://github.com/kseniadmay/RecipeBot.git
cd RecipeBot
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка переменных окружения

Создайте файл `.env` на основе шаблона:
```bash
cp .env.example .env
```
После этого замените значения переменных на собственные

### 4. Запуск бота
```bash
python bot.py
```

## Структура
```
RecipeBot/              # Корень репозитория
├── bot.py              # Главный файл бота
├── api_client.py       # Клиент для Recipe API
├── config.py           # Конфигурация и переменные окружения
├── keyboards.py        # Telegram клавиатуры
├── requirements.txt    # Зависимости
├── Dockerfile          # Docker образ
├── docker-compose.yml  # Docker Compose конфигурация
├── .env.example        # Пример переменных окружения
└── README.md           # Документация
```

## Связанные проекты

Бот использует [Recipe API](https://github.com/kseniadmay/RecipeAPI) для получения данных о рецептах.

## Автор

GitHub: [@kseniadmay](https://github.com/kseniadmay)  
Email: kseniadmay@gmail.com

## Лицензия

MIT License