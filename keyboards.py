from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup


def get_main_keyboard():
    """Главная клавиатура"""

    keyboard = [
        ['🔍 Поиск рецептов', '🎲 Случайный рецепт'],
        ['⚡ Быстрые рецепты', '⭐ Избранное'],
        ['ℹ️ Помощь']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_recipe_keyboard(recipe_id):
    """Клавиатура для рецепта"""

    keyboard = [
        [
            InlineKeyboardButton('⭐ В избранное', callback_data=f'fav_{recipe_id}'),
            InlineKeyboardButton('🔙 Назад', callback_data='back')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_recipe_list_keyboard(recipes):
    """Клавиатура со списком рецептов"""

    keyboard = []

    for i, recipe in enumerate(recipes[:10], 1):
        keyboard.append([
            InlineKeyboardButton(
                f'{i}. {recipe['title']}',
                callback_data=f'recipe_{recipe['id']}'
            )
        ])

    return InlineKeyboardMarkup(keyboard)