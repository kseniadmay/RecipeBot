import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import re

from config import BOT_TOKEN, API_BASE_URL
from api_client import RecipeAPIClient
from keyboards import get_main_keyboard, get_recipe_keyboard, get_recipe_list_keyboard, get_notifications_keyboard

user_sessions = {}  # Словарь для хранения токенов: {user_id: {'token': '...', 'username': '...'}}

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# API клиент
api = RecipeAPIClient()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""

    user_name = update.effective_user.first_name

    # Проверяем, есть ли кириллица в имени
    if re.search('[а-яА-ЯёЁ]', user_name):
        greeting = f'Привет, {user_name}!'
    else:
        greeting = f'Hello there, {user_name}, sir!'

    welcome_text = (
        f'{greeting} 🧑‍🍳\n\n'
        'Я помогу тебе придумать, что приготовить.\n\n'
        'Выбери, что хочешь:'
    )

    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""

    help_text = (
        'Как пользоваться ботом? Нажми:\n\n'
        '🔍 Поиск рецептов - для поиска рецепта по слову\n\n'
        '🎲 Случайный рецепт - когда не знаешь, что приготовить\n\n'
        '⚡ Быстрые рецепты - рецепты, которые готовятся до 30 минут\n\n'
        '⭐ Избранное - чтобы посмотреть свои сохранённые рецепты\n\n'
        'Или просто напиши название блюда:'
    )

    await update.message.reply_text(help_text)


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /login"""

    await update.message.reply_text(
        '🔐 Авторизация\n\n'
        'Отправь данные в формате:\n'
        '`username password`\n\n'
        'Например:\n'
        '`demo demo1234`',
        parse_mode='Markdown'
    )
    context.user_data['waiting_for_login'] = True


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /register"""

    await update.message.reply_text(
        '📝 Регистрация\n\n'
        'Отправь данные в формате:\n'
        '`username email password`\n\n'
        'Например:\n'
        '`myuser user@example.com pass1234`',
        parse_mode='Markdown'
    )
    context.user_data['waiting_for_register'] = True


async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /logout"""

    user_id = update.effective_user.id

    if user_id in user_sessions:
        username = user_sessions[user_id].get('username', 'Пользователь')
        del user_sessions[user_id]
        await update.message.reply_text(
            f'👋 До свидания, {username}!\n'
            'Вы вышли из аккаунта',
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            'Вы не авторизованы',
            reply_markup=get_main_keyboard()
        )


def get_user_token(user_id: int) -> str:
    """Получить токен пользователя"""

    session = user_sessions.get(user_id)
    return session['token'] if session else None


def is_authenticated(user_id: int) -> bool:
    """Проверка авторизации"""

    return user_id in user_sessions


async def process_login(update: Update, credentials: str):
    """Обработка логина"""

    parts = credentials.split()

    if len(parts) != 2:
        await update.message.reply_text(
            'Неверный формат\n\n'
            'Используй формат: `username password`',
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return

    username, password = parts

    await update.message.reply_text('Авторизация...')

    success, data = api.login(username, password)

    if success:
        user_id = update.effective_user.id
        user_sessions[user_id] = {
            'token': api.token,
            'username': username
        }

        await update.message.reply_text(
            f'Добро пожаловать, {username}!\n\n'
            'Теперь ты можешь использовать избранное',
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            'Ошибка авторизации\n\n'
            'Проверь username и пароль\n'
            'Или зарегистрируйся: /register',
            reply_markup=get_main_keyboard()
        )


async def process_register(update: Update, credentials: str):
    """Обработка регистрации"""

    parts = credentials.split()

    if len(parts) != 3:
        await update.message.reply_text(
            'Неверный формат\n\n'
            'Используй формат: `username email password`',
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return

    username, email, password = parts

    await update.message.reply_text('Регистрация...')

    success, data = api.register(username, email, password)

    if success:
        user_id = update.effective_user.id
        user_sessions[user_id] = {
            'token': api.token,
            'username': username
        }

        await update.message.reply_text(
            f'Регистрация успешна\n\n'
            f'Добро пожаловать, {username}!',
            reply_markup=get_main_keyboard()
        )
    else:
        error_msg = data if isinstance(data, str) else str(data)
        await update.message.reply_text(
            f'Ошибка регистрации!\n\n{error_msg}',
            reply_markup=get_main_keyboard()
        )


async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка поиска рецепта"""

    await update.message.reply_text(
        'Напиши название блюда:',
        reply_markup=get_main_keyboard()
    )
    context.user_data['waiting_for_search'] = True


async def handle_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Случайный рецепт"""

    await update.message.reply_text('Ищу случайный рецепт...')

    success, data = api.get_random_recipe()

    if success and data:
        await send_recipe(update, data)
    else:
        await update.message.reply_text(
            'Не удалось найти рецепт 🥺. Попробуй попозже?',
            reply_markup=get_main_keyboard()
        )


async def handle_quick_recipes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрые рецепты"""

    await update.message.reply_text('Ищу быстрые рецепты...')

    success, data = api.get_quick_recipes()

    if success and data:
        results = data.get('results', [])
        if results:
            await update.message.reply_text(
                'Быстрые рецепты до 30 минут.\n\nВыбери рецепт:',
                reply_markup=get_recipe_list_keyboard(results)
            )
        else:
            await update.message.reply_text(
                'Быстрые рецепты не найдены 🥺',
                reply_markup=get_main_keyboard()
            )
    else:
        await update.message.reply_text(
            'Ошибка при поиске рецептов 🥺',
            reply_markup=get_main_keyboard()
        )


async def handle_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Избранные рецепты"""
    user_id = update.effective_user.id

    if not is_authenticated(user_id):
        await update.message.reply_text(
            'Для использования избранного нужно авторизоваться\n\n'
            'Войди в аккаунт: /login\n'
            'Или зарегистрируйся: /register',
            reply_markup=get_main_keyboard()
        )
        return

        # Устанавливаем токен для API клиента
    api.token = get_user_token(user_id)

    await update.message.reply_text('Загружаю избранное...')

    success, data = api.get_favorites()

    if success and data:
        results = data.get('results', [])

        if results:
            text = f'Избранные рецепты ({len(results)}):\n\nВыбери рецепт:'
            await update.message.reply_text(
                text,
                reply_markup=get_recipe_list_keyboard(results)
            )
        else:
            await update.message.reply_text(
                'Нет ни одного сохранённого рецепта!\n\n'
                'Добавляй рецепты в избранное нажимая ⭐ под рецептом',
                reply_markup=get_main_keyboard()
            )
    else:
        await update.message.reply_text(
            'Ошибка при загрузке избранного 🥺',
            reply_markup=get_main_keyboard()
        )


async def handle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Управление email уведомлениями"""

    user_id = update.effective_user.id

    if not is_authenticated(user_id):
        await update.message.reply_text(
            'Для управления уведомлениями нужно авторизоваться\n\n'
            'Войди в аккаунт: /login\n'
            'Или зарегистрируйся: /register',
            reply_markup=get_main_keyboard()
        )
        return

    # Устанавливаем токен
    api.token = get_user_token(user_id)

    await update.message.reply_text('Загружаю настройки...')

    success, data = api.get_notification_settings()

    if success and data:
        is_enabled = data.get('email_notifications', False)

        status_emoji = '🔔' if is_enabled else '🔕'
        status_text = 'включены' if is_enabled else 'отключены'

        text = (
            f'{status_emoji} Email уведомления\n\n'
            f'Статус: {status_text}\n\n'
            f'Ежедневный дайджест с рецептами приходит на вашу почту каждый день в 13:00 МСК.\n\n'
            f'{"✅ Вы получаете дайджесты" if is_enabled else "❌ Вы не получаете дайджесты"}'
        )

        await update.message.reply_text(
            text,
            reply_markup=get_notifications_keyboard(is_enabled)
        )
    else:
        await update.message.reply_text(
            'Ошибка при загрузке настроек 🥺',
            reply_markup=get_main_keyboard()
        )


async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE, current_status: bool):
    """Переключение email уведомлений"""

    query = update.callback_query
    user_id = update.effective_user.id

    if not is_authenticated(user_id):
        await query.message.reply_text(
            'Ошибка авторизации',
            reply_markup=get_main_keyboard()
        )
        return

    # Устанавливаем токен
    api.token = get_user_token(user_id)

    # Переключаем статус
    new_status = not current_status

    success, data = api.update_notification_settings(new_status)

    if success and data:
        is_enabled = data.get('email_notifications', False)

        status_emoji = '🔔' if is_enabled else '🔕'
        status_text = 'включены' if is_enabled else 'отключены'
        success_msg = '✅ Уведомления включены!' if is_enabled else '✅ Уведомления отключены!'

        text = (
            f'{status_emoji} Email уведомления\n\n'
            f'Статус: {status_text}\n\n'
            f'{success_msg}\n\n'
            f'Ежедневный дайджест с рецептами приходит на вашу почту каждый день в 13:00 МСК.\n\n'
            f'{"✅ Вы получаете дайджесты" if is_enabled else "❌ Вы не получаете дайджесты"}'
        )

        await query.message.edit_text(
            text,
            reply_markup=get_notifications_keyboard(is_enabled)
        )

        await query.answer(success_msg)
    else:
        await query.answer('Ошибка')
        await query.message.reply_text(
            'Не удалось изменить настройки 🥺',
            reply_markup=get_main_keyboard()
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""

    text = update.message.text
    user_id = update.effective_user.id

    # Обработка кнопок главного меню
    if text == '🔍 Поиск рецептов':
        await handle_search(update, context)
        return
    elif text == '🎲 Случайный рецепт':
        await handle_random(update, context)
        return
    elif text == '⚡ Быстрые рецепты':
        await handle_quick_recipes(update, context)
        return
    elif text == '⭐ Избранное':
        await handle_favorites(update, context)
        return
    elif text == '🔔 Уведомления':
        await handle_notifications(update, context)
        return
    elif text == 'ℹ️ Помощь':
        await help_command(update, context)
        return

    # Обработка логина
    if context.user_data.get('waiting_for_login'):
        context.user_data['waiting_for_login'] = False
        await process_login(update, text)
        return

    # Обработка регистрации
    if context.user_data.get('waiting_for_register'):
        context.user_data['waiting_for_register'] = False
        await process_register(update, text)
        return

    # Если ожидаем поисковый запрос
    if context.user_data.get('waiting_for_search'):
        context.user_data['waiting_for_search'] = False
        await search_recipes(update, text)
        return

    # Или просто ищем по тексту
    await search_recipes(update, text)


async def search_recipes(update: Update, query: str):
    """Поиск рецептов по запросу"""

    await update.message.reply_text(f'Ищу рецепты: {query.lower()}...')

    success, data = api.search_recipes(query)

    if success and data:
        results = data.get('results', [])

        if results:
            await update.message.reply_text(
                f'Найдено рецептов: {len(results)}\n\nВыбери рецепт:',
                reply_markup=get_recipe_list_keyboard(results)
            )
        else:
            await update.message.reply_text(
                'Рецепты не найдены 🥺. Попробуй другой запрос?',
                reply_markup=get_main_keyboard()
            )
    else:
        await update.message.reply_text(
            'Ошибка при поиске 🥺. Попробуй позже?',
            reply_markup=get_main_keyboard()
        )


async def send_recipe(update: Update, recipe: dict):
    """Отправка рецепта пользователю"""

    # Формируем краткий текст для caption (до 1024 символов)
    caption = f'🍳 **{recipe["title"]}**\n\n'
    caption += f'{recipe["description"]}\n\n'
    caption += '═══════════════════\n'
    caption += f'⏱️ Время: **{recipe["cook_time"]} мин**\n'
    caption += f'👥 Порций: **{recipe["servings"]}**\n'

    # Сложность
    difficulty_map = {
        'easy': 'Легко',
        'medium': 'Средне',
        'hard': 'Сложно'
    }
    difficulty = difficulty_map.get(recipe.get('difficulty', 'medium'), 'Средне')
    caption += f'⭐ Сложность: **{difficulty}**'

    # Формируем ПОЛНЫЙ текст с ингредиентами и шагами
    full_text = ''

    # Ингредиенты
    if recipe.get('ingredients'):
        full_text += '\n\n📋 **ИНГРЕДИЕНТЫ:**\n'
        for ing in recipe['ingredients']:
            # Форматируем количество
            amount = ing['amount']
            if isinstance(amount, float) and amount.is_integer():
                amount = int(amount)

            unit = ing.get('unit', '')
            if unit:
                full_text += f'  • {ing["name"]} — {amount} {unit}\n'
            else:
                full_text += f'  • {ing["name"]} — {amount}\n'

    # Шаги приготовления
    if recipe.get('steps'):
        full_text += '\n👨‍🍳 **ПРИГОТОВЛЕНИЕ:**\n'
        for step in recipe['steps']:
            full_text += f'\n**{step["order"]}.** {step["description"]}\n'

    # Если есть изображение
    image_url = recipe.get('image')

    if image_url:
        # Преобразуем относительный путь в абсолютный URL
        if not image_url.startswith('http'):
            from config import API_BASE_URL
            if API_BASE_URL.endswith('/api'):
                base_url = API_BASE_URL[:-4]
            else:
                base_url = API_BASE_URL
            image_url = f'{base_url}{image_url}'

        # Отправляем фото с кратким caption
        try:
            if update.callback_query:
                await update.callback_query.message.delete()
                # Отправляем фото
                await update.callback_query.message.reply_photo(
                    photo=image_url,
                    caption=caption,
                    parse_mode='Markdown'
                )
                # Отправляем полный текст отдельным сообщением
                await update.callback_query.message.reply_text(
                    full_text,
                    reply_markup=get_recipe_keyboard(recipe['id']),
                    parse_mode='Markdown'
                )
            else:
                # Отправляем фото
                await update.message.reply_photo(
                    photo=image_url,
                    caption=caption,
                    parse_mode='Markdown'
                )
                # Отправляем полный текст отдельным сообщением
                await update.message.reply_text(
                    full_text,
                    reply_markup=get_recipe_keyboard(recipe['id']),
                    parse_mode='Markdown'
                )

        except Exception as e:
            logger.error(f'Ошибка при отправке фото: {e}')
            # Если не удалось отправить фото, отправляем всё текстом
            complete_text = caption + full_text
            if update.callback_query:
                await update.callback_query.message.edit_text(
                    complete_text,
                    reply_markup=get_recipe_keyboard(recipe['id']),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    complete_text,
                    reply_markup=get_recipe_keyboard(recipe['id']),
                    parse_mode='Markdown'
                )

    else:
        # Нет фото - отправляем всё текстом
        complete_text = caption + full_text
        if update.callback_query:
            await update.callback_query.message.edit_text(
                complete_text,
                reply_markup=get_recipe_keyboard(recipe['id']),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                complete_text,
                reply_markup=get_recipe_keyboard(recipe['id']),
                parse_mode='Markdown'
            )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback кнопок"""

    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = update.effective_user.id

    # Отображение рецепта
    if data.startswith('recipe_'):
        recipe_id = data.split('_')[1]
        success, recipe = api.get_recipe(recipe_id)

        if success and recipe:
            await send_recipe(update, recipe)
        else:
            await query.message.reply_text(
                'Не удалось загрузить рецепт 🥺',
                reply_markup=get_main_keyboard()
            )

    # Добавление в избранное
    elif data.startswith('fav_'):
        if not is_authenticated(user_id):
            await query.message.reply_text(
                'Чтобы использовать избранное войди в аккаунт: /login',
                reply_markup=get_main_keyboard()
            )
            return

        recipe_id = data.split('_')[1]

        # Устанавливаем токен
        api.token = get_user_token(user_id)

        success, result = api.add_to_favorites(recipe_id)

        if success:
            await query.answer('Добавлено в избранное!')
            await query.message.reply_text(
                'Рецепт добавлен в избранное!\n\n'
                'Смотри все избранные: нажми ⭐ Избранное',
                reply_markup=get_main_keyboard()
            )
        else:
            await query.answer('Ошибка')
            await query.message.reply_text(
                'Не удалось добавить в избранное 🥺',
                reply_markup=get_main_keyboard()
            )

    # Переключение уведомлений
    elif data.startswith('toggle_notifications_'):
        current_status = data.split('_')[-1] == 'True'
        await toggle_notifications(update, context, current_status)

    # Назад
    elif data == 'back':
        await query.message.reply_text(
            'Главное меню:',
            reply_markup=get_main_keyboard()
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""

    logger.error(f'Update {update} caused error {context.error}')


def main():
    """Запуск бота"""

    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('login', login_command))
    application.add_handler(CommandHandler('register', register_command))
    application.add_handler(CommandHandler('logout', logout_command))

    # Обработчик callback кнопок
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Обработчик текстовых сообщений
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # Обработчик ошибок
    application.add_error_handler(error_handler)

    # Запускаем бота
    logger.info('🚀 Бот запущен!')
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
