import telebot

from actions import UserActions
from clients.telegram_client import TelegramClient
from clients.db_client import SQLiteClient


# -----------------------------------------------------------
# КОНСТАНТЫ
TOKEN = ''  # Ключ бота
BASE_URL = 'https://api.telegram.org'
ADMIN_CHAT_ID = 0  # ID Чата админа для контроля ошибок
DATABASE = 'db/remind.db'  # Файл с базой данных SQL


# -----------------------------------------------------------
# BASE
class MyBot(telebot.TeleBot):
    def __init__(self, client: TelegramClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telegram_client = client
        self.user_action = user_action

    def setup_resources(self):
        self.user_action.setup()

    def shutdown_resources(self):
        self.user_action.shutdown()

    def shutdown(self):
        self.shutdown_resources()


telegram_client = TelegramClient(token=TOKEN, base_url=BASE_URL)
user_action = UserActions(SQLiteClient(DATABASE))
bot = MyBot(token=TOKEN, client=telegram_client)
