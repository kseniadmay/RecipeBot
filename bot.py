import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import re

from config import BOT_TOKEN
from api_client import RecipeAPIClient
from keyboards import get_main_keyboard, get_recipe_keyboard, get_recipe_list_keyboard

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
        '🔍 Поиск рецептов — если хочешь ввести слово, по которому ищешь рецепт\n\n'
        '🎲 Случайный рецепт — если хочешь получить случайный рецепт и не думать\n\n'
        '⚡ Быстрые рецепты — если хочешь посмотреть рецепты, которые готовятся до 30 минут\n\n'
        '⭐ Избранное — если хочешь посмотреть свои сохранённые рецепты\n\n'
        'Или просто напиши название блюда:'
    )

    await update.message.reply_text(help_text)


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

    # Сделать авторизацию
    await update.message.reply_text(
        'Функция избранного сейчас в разработке!\n'
        'Скоро добавлю возможность сохранять любимые рецепты',
        reply_markup=get_main_keyboard()
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""

    text = update.message.text

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
    elif text == 'ℹ️ Помощь':
        await help_command(update, context)
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

    # Формируем текст рецепта
    text = f'🍳 {recipe['title']}\n\n'
    text += f'📝 {recipe['description']}\n\n'
    text += f'⏱️ Время: {recipe['cook_time']} минут\n'
    text += f'👥 Порций: {recipe['servings']}\n'
    text += f'⭐ Сложность: {recipe.get('difficulty', 'Средняя')}\n'

    # Ингредиенты
    if recipe.get('ingredients'):
        text += '\n📋 Ингредиенты:\n'
        for ing in recipe['ingredients']:
            text += f'• {ing['name']} — {ing['amount']} {ing['unit']}\n'

    # Шаги
    if recipe.get('steps'):
        text += '\n👨‍🍳 Приготовление:\n'
        for step in recipe['steps']:
            text += f'{step['order']}. {step['description']}\n'

    # Отправляем
    if update.callback_query:
        await update.callback_query.message.edit_text(
            text,
            reply_markup=get_recipe_keyboard(recipe['id'])
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=get_recipe_keyboard(recipe['id'])
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback кнопок"""

    query = update.callback_query
    await query.answer()

    data = query.data

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
        # Сделать авторизацию
        await query.message.reply_text(
            'Функция избранного скоро будет доступна!',
            reply_markup=get_main_keyboard()
        )

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
