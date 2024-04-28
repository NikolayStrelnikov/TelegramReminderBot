from datetime import datetime

import telebot
from dateutil.parser import parse, parserinfo
from telebot import types
from telebot.apihelper import ApiTelegramException

from actions import UserActions
from clients.db_client import SQLiteClient
from clients.telegram_client import TelegramClient
from config import TOKEN, BASE_URL, DATABASE


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


# Метод проверки даты-времени
def valid_date(message: types.Message):
    try:
        date_time = parse(message.text, dayfirst=True, fuzzy=False, parserinfo=RussianParserInfo())
        if date_time < datetime.now():
            text = (f'Введены дата и/или время в прошлом: {date_time.strftime("%d.%m.%Y %H:%M")} '
                    f'\nПопробуйте еще раз')
            bot.reply_to(message, text)
            return False
        elif date_time > datetime(datetime.now().year + 3, 12, 31):
            text = (f'Введена дата в далёком будущем: {date_time.strftime("%d.%m.%Y %H:%M")}'
                    f'\nОграничимся событиями на 3 года вперед?'
                    f'\nПопробуйте еще раз')
            bot.reply_to(message, text)
        else:
            return date_time
    except ValueError:
        bot.reply_to(message, f'Вы ввели некорректные дату и время,\n'
                              f'пример: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
        return False


# Метод формирования МЕНЮ
def build_menu(buttons, n_cols: int, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


# Метод расчета дней недели для чата
def get_weekdays(days_number):
    days = {1: 'пн', 2: 'вт', 3: 'ср', 4: 'чт', 5: 'пт', 6: 'сб', 7: 'вс'}
    days_number = [int(i) for i in str(days_number)]
    days_number.sort()
    if days_number == [1, 2, 3, 4, 5]:
        text_days = 'всем рабочим дням'
    elif days_number == [6, 7]:
        text_days = 'выходным'
    else:
        text_days = ', '.join([days[i] for i in days_number])
    return text_days


# Обрабатываем Exception
def create_err_msg(err: Exception) -> str:
    current_date = datetime.now().strftime('%H:%M:%S %d/%m/%y')
    err_mess = f'Ошибка бота. Время: {current_date}\n{err.__class__}:\n{err}'
    return err_mess


class RussianParserInfo(parserinfo):
    MONTHS = [('Янв', 'Январь', 'Января', 'Jan', 'January'),
              ('Фев', 'Февраль', 'Февраля', 'Feb', 'February'),
              ('Мар', 'Март', 'Марта', 'Mar', 'March'),
              ('Апр', 'Апрель', 'Апреля', 'Apr', 'April'),
              ('Май', 'Май', 'Мая', 'May'),
              ('Июнь', 'Июнь', 'Июня', 'Jun', 'June'),
              ('Июль', 'Июль', 'Июля', 'Jul', 'July'),
              ('Авг', 'Август', 'Августа', 'Aug', 'August'),
              ('Сент', 'Сентябрь', 'Сентября', 'Sep', 'September'),
              ('Окт', 'Октябрь', 'Октября', 'Oct', 'October'),
              ('Ноя', 'Ноябрь', 'Ноября', 'Nov', 'November'),
              ('Дек', 'Декабрь', 'Декабря', 'Dec', 'December')]

    PERTAIN = ['г.', 'г', 'of']

    WEEKDAYS = [('Пн', 'Понедельник', 'Mon', 'Monday'),
                ('Вт', 'Вторник', 'Tue', 'Tuesday'),
                ('Ср', 'Среда', 'Wed', 'Wednesday'),
                ('Чт', 'Четверг', 'Thu', 'Thursday'),
                ('Пт', 'Пятница', 'Fri', 'Friday'),
                ('Сб', 'Суббота', 'Sat', 'Saturday'),
                ('Вс', 'Воскресенье', 'Sun', 'Sunday')]

    HMS = [('ч', 'час', 'часа', 'часов', 'h', 'hour', 'hours'),
           ('м', 'мин', 'минута', 'минуты', 'минут', 'm', 'min', 'minute', 'minutes'),
           ('с', 'сек', 'секунда', 'секунды', 'секунд', 's', 'sec', 'second', 'seconds')]


def text_processor(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    step = bot.user_action.get_current_status(user_id)
    if step == 'NEW':
        # записали сообщение в базу
        bot.user_action.set_text(message.html_text, chat_id)
        mess = f"Введите дату и время напоминания в формате DD-MM-YYYY hh:mm"
        bot.send_message(chat_id, mess, parse_mode='HTML')
    elif step == 'TEXT':
        message_date_time = valid_date(message)
        last_mess_id = bot.user_action.get_last_mess_id(user_id)

        if message_date_time:
            last_up = message_date_time.day
            bot.user_action.set_date(last_up, message_date_time, user_id)

            keyboard = types.InlineKeyboardMarkup()
            button_list = [
                types.InlineKeyboardButton(text='Один раз. Без повторов', callback_data='ONETIME'),
                types.InlineKeyboardButton(text='Ввести дни недели', callback_data='WORKDAY'),
                types.InlineKeyboardButton(text='Каждый Х день', callback_data='DAILY'),
                types.InlineKeyboardButton(text='Каждую Х неделю', callback_data='WEEKLY'),
                types.InlineKeyboardButton(text='Каждый Х месяц', callback_data='MONTHLY')
            ]
            keyboard.add(*button_list)
            reply_markup = types.InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
            mess = f'Выберите периодичность и частоту напоминаний бота'

            if last_mess_id:
                try:
                    bot.delete_message(chat_id, last_mess_id)
                except ApiTelegramException:
                    pass
            new_message = bot.send_message(chat_id, mess, parse_mode='HTML', reply_markup=reply_markup)
            bot.user_action.set_last_mess_id(new_message.message_id, user_id)
    elif step == 'FACTOR':
        factor = message.text
        choose = bot.user_action.get_period(user_id)
        mess = f"Вы ввели не целое число. Попробуйте еще раз"

        if choose == 'WORKDAY':
            # проверяем что заданы цифры (1,2,3,4,5,6,7), пишем фактор в базу...
            val = sorted(set(factor))
            result = ''
            for i in val:
                if i in ["1", "2", "3", "4", "5", "6", "7"]:
                    result = result + i
            if result:
                bot.user_action.set_active(int(result), user_id)
                mess = f'Напоминание установлено и будет повторяться по <b>{get_weekdays(result)}</b>'
            else:
                mess = f'Вы не ввели ни одной цифры от 1 до 7, обозначающих дни недели. Попробуйте еще раз'
        elif choose == 'DAILY':
            # проверяем что это число и оно не меньше 1 и не больше 366
            try:
                val = int(factor)
                if 0 < val < 367:
                    bot.user_action.set_active(val, user_id)
                    mess = (f"Напоминание установлено и будет повторяться "
                            f"<b>каждый {val if val > 1 else ''} день</b>")
                else:
                    mess = f"Число должно быть от 1 до 366"
            except ValueError:
                pass
        elif choose == 'WEEKLY':
            # проверяем, что это число и оно не больше 366/7=53
            try:
                val = int(factor)
                if 0 < val < 53:
                    bot.user_action.set_active(val, user_id)
                    mess = (f"Напоминание установлено и будет повторяться "
                            f"<b>каждую {val if val > 1 else ''} неделю</b>")
                else:
                    mess = f"Число должно быть от 1 до 52"
            except ValueError:
                pass
        elif choose == 'MONTHLY':
            # проверяем, что это число и оно не больше 12
            try:
                val = int(factor)
                if 0 < val < 13:
                    bot.user_action.set_active(val, user_id)
                    mess = (f"Напоминание установлено и будет повторяться "
                            f"<b>каждый {val if val > 1 else ''} месяц</b>")
                else:
                    mess = f"Число должно быть от 1 до 12"
            except ValueError:
                pass
        else:
            mess = 'Вы нашли ошибку 2 в Боте. Напишите автору, он будет очень благодарен'
        bot.send_message(chat_id, mess, parse_mode='HTML')
