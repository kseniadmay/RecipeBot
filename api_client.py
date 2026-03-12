import requests
from config import API_BASE_URL


class RecipeAPIClient:
    """Клиент для работы с Recipe API"""

    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
        self.token = None

    def register(self, username, email, password):
        """Регистрация пользователя"""

        url = f'{self.base_url}/auth/register/'
        data = {
            'username': username,
            'email': email,
            'password': password,
            'password2': password
        }

        try:
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 201:
                result = response.json()
                self.token = result.get('access')
                return True, result
            return False, response.json()
        except Exception as e:
            return False, str(e)

    def login(self, username, password):
        """Логин пользователя"""

        url = f'{self.base_url}/auth/login/'
        data = {
            'username': username,
            'password': password
        }

        try:
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('access')
                return True, result
            return False, response.json()
        except Exception as e:
            return False, str(e)

    def search_recipes(self, query):
        """Поиск рецептов"""

        url = f'{self.base_url}/recipes/'
        params = {'search': query}

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return True, response.json()
            return False, None
        except Exception as e:
            return False, str(e)

    def get_recipe(self, recipe_id):
        """Получить рецепт"""

        url = f'{self.base_url}/recipes/{recipe_id}/'

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return True, response.json()
            return False, None
        except Exception as e:
            return False, str(e)

    def get_random_recipe(self):
        """Получить случайный рецепт"""

        url = f'{self.base_url}/recipes/random/'

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return True, response.json()
            return False, None
        except Exception as e:
            return False, str(e)

    def get_quick_recipes(self):
        """Получить быстрые рецепты до 30 минут"""

        url = f'{self.base_url}/recipes/quick_recipes/'

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return True, response.json()
            return False, None
        except Exception as e:
            return False, str(e)

    def add_to_favorites(self, recipe_id):
        """Добавить рецепт в избранное"""

        if not self.token:
            return False, 'Not authenticated'

        url = f'{self.base_url}/recipes/{recipe_id}/add_to_favorites/'
        headers = {'Authorization': f'Bearer {self.token}'}

        try:
            response = requests.post(url, headers=headers, timeout=10)
            if response.status_code in [200, 201]:
                return True, response.json()
            return False, response.json()
        except Exception as e:
            return False, str(e)

    def get_favorites(self):
        """получить избранные рецепты"""

        if not self.token:
            return False, 'Not authenticated'

        url = f'{self.base_url}/recipes/favorites/'
        headers = {'Authorization': f'Bearer {self.token}'}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return True, response.json()
            return False, None
        except Exception as e:
            return False, str(e)
