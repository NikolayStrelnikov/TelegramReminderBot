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
        bot.reply_to(message, f'Вы ввели некорректные дату и время,'
                              f'\nпример: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
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
def get_text_period(period: str, factor: str):
    text_days = ''
    count = ' ' + factor if factor.isdigit() and int(factor) > 1 else ''
    if period == 'ONETIME':
        text_days = 'один раз'
    elif period == 'MINUTE':
        text_days = f'каждую{count} минуту'
    elif period == 'HOUR':
        text_days = f'каждый{count} час'
    elif period == 'WORKDAY':
        days = {1: 'пн', 2: 'вт', 3: 'ср', 4: 'чт', 5: 'пт', 6: 'сб', 7: 'вс'}
        factor = [int(i) for i in str(check_workday(factor))]
        factor.sort()
        if factor == [1, 2, 3, 4, 5]:
            text_days = 'по всем рабочим дням'
        elif factor == [6, 7]:
            text_days = 'по выходным'
        elif factor == [1, 2, 3, 4, 5, 6, 7]:
            text_days = 'каждый день'
        elif factor == [0]:
            text_days = '<b>ошибочный</b>'
        else:
            text_days = 'по ' + ', '.join([days[i] for i in factor])
    elif period == 'DAILY':
        text_days = f'каждый{count} день'
    elif period == 'WEEKLY':
        text_days = f'каждую{count} неделю'
    elif period == 'MONTHLY':
        text_days = f'каждый{count} месяц'
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
    [base_id, step] = user_action.get_last_edit_status(user_id)[0]  # GET+

    if step == 'NEW':
        # записали сообщение в базу
        user_action.set_text(message.html_text, base_id)  # SET+
        mess = f"Введите дату и время напоминания в формате DD-MM-YYYY hh:mm"
        bot.send_message(chat_id, mess, parse_mode='HTML')

    elif step == 'TEXT':
        message_date_time = valid_date(message)

        if message_date_time:
            last_up = message_date_time.day
            user_action.set_date(last_up, message_date_time, base_id)  # SET+

            select_period(user_id=user_id, base_id=base_id)

    elif step == 'FACTOR':
        step_factor(factor=message.text, chat_id=chat_id, base_id=base_id)

    elif step == 'PAUSE':
        sub_step = user_action.get_sub_step(base_id)  # GET+
        if sub_step == 'EDIT_DATE':
            message_date_time = valid_date(message)
            if message_date_time:
                last_up = message_date_time.day
                user_action.set_edit_date(last_up, message_date_time, base_id)  # SET+
                mess = f'Установлены новые дата и время напоминания: {message_date_time.strftime("%d.%m.%Y %H:%M")}'
                bot.send_message(message.chat.id, mess, parse_mode='HTML')

        elif sub_step == 'EDIT_TEXT':
            user_action.set_edit_text(message.html_text, base_id)  # SET+
            mess = f'Текст напоминания обновлён'
            bot.send_message(message.chat.id, mess, parse_mode='HTML')

        elif sub_step == 'EDIT_FACTOR':
            step_factor(factor=message.text, chat_id=chat_id, base_id=base_id)


def step_factor(factor: str, chat_id: int, base_id: int):
    remind = user_action.get_message_by_id(base_id)  # GET+
    period = remind[7]
    cd = datetime.strptime(remind[6], "%Y-%m-%d %H:%M:%S")
    mess = f'Вы ввели не целое число. Попробуйте еще раз'
    start_mess = f'Напоминание в группе <b>{remind[3]}</b> установлено и будет повторяться '
    end_mess = f'\nВремя следующего напоминания: {cd.strftime("%d.%m.%Y %H:%M")}'
    if period == 'WORKDAY':
        result = check_workday(factor)
        if result:
            user_action.set_active(result, base_id)  # SET+
            mess = start_mess + '<b>' + get_text_period(period, str(result)) + '</b>' + end_mess
        else:
            mess = f'Вы не ввели ни одной цифры от 1 до 7, обозначающих дни недели. Попробуйте еще раз'
    elif period == 'DAILY':
        # проверяем что это число и оно не меньше 1 и не больше 366
        try:
            val = int(factor)
            if 0 < val < 367:
                user_action.set_active(val, base_id)  # SET+
                mess = start_mess + '<b>' + get_text_period(period, factor) + '</b>' + end_mess
            else:
                mess = f'Число должно быть от 1 до 366'
        except ValueError:
            pass
    elif period == 'WEEKLY':
        # проверяем, что это число и оно не больше 366/7=53
        try:
            val = int(factor)
            if 0 < val < 53:
                user_action.set_active(val, base_id)  # SET+
                mess = start_mess + '<b>' + get_text_period(period, factor) + '</b>' + end_mess
            else:
                mess = f"Число должно быть от 1 до 52"
        except ValueError:
            pass
    elif period == 'MONTHLY':
        # проверяем, что это число и оно не больше 12
        try:
            val = int(factor)
            if 0 < val < 13:
                user_action.set_active(val, base_id)  # SET+
                mess = start_mess + '<b>' + get_text_period(period, factor) + '</b>' + end_mess
            else:
                mess = f'Число должно быть от 1 до 12'
        except ValueError:
            pass
    else:
        mess = 'Вы нашли ошибку 2 в Боте. Напишите автору, он будет очень благодарен'
    bot.send_message(chat_id, mess, parse_mode='HTML')


def check_workday(factor: str):
    # проверяем что заданы цифры (1,2,3,4,5,6,7), пишем фактор в базу
    val = sorted(set(factor))
    result = ''
    for i in val:
        if i in ["1", "2", "3", "4", "5", "6", "7"]:
            result = result + i
    return int(result) if result else 0


def choose_period(choose: str, base_id: int):
    mess = f'Введите период между регулярными напоминаниями'
    if choose == 'ONETIME':
        # проверяем в зависимости от выбора choose
        user_action.set_active(factor=1, db_id=base_id)  # SET+
        mess = f'Напоминание от бота придет вам {get_text_period(choose, "1")}'
    elif choose == 'WORKDAY':
        mess += ('\n1 - повторение по понедельникам в указанное вами время,'
                 '\n2,4 - повторение по вторникам и четвергам,'
                 '\n1,2,3,4,5 - повторение по будням')
    elif choose == 'DAILY':
        mess += ('\n1 - повторение ежедневно в указанное вами время,'
                 '\n2 - каждый второй день и т.д.')
    elif choose == 'WEEKLY':
        mess += ('\n1 - повторение еженедельно в указанное вами время и день недели,'
                 '\n2 - каждую вторую неделю и т.д.')
    elif choose == 'MONTHLY':
        mess += ('1 - повторение ежемесячно в указанное вами время и число месяца,'
                 '\n2 - каждый второй месяц и т.д.'
                 '\nЕсли выбранного числа не будет в месяце, то сообщение придёт в последний день'
                 '\nЕсли число выпадет на выходной, то сообщение придёт в пятницу')
    else:
        mess = 'Вы нашли ошибку 1 в Боте. Напишите автору, он будет очень благодарен'
    return mess


def select_period(user_id: int, base_id: int):
    keyboard = types.InlineKeyboardMarkup()
    button_list = [
        types.InlineKeyboardButton(text='Один раз. Без повторов', callback_data=f'PERIOD:ONETIME:{base_id}'),
        types.InlineKeyboardButton(text='Ввести дни недели', callback_data=f'PERIOD:WORKDAY:{base_id}'),
        types.InlineKeyboardButton(text='Каждый Х день', callback_data=f'PERIOD:DAILY:{base_id}'),
        types.InlineKeyboardButton(text='Каждую Х неделю', callback_data=f'PERIOD:WEEKLY:{base_id}'),
        types.InlineKeyboardButton(text='Каждый Х месяц', callback_data=f'PERIOD:MONTHLY:{base_id}')
    ]
    keyboard.add(*button_list)
    reply_markup = types.InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
    mess = f'Выберите периодичность и частоту напоминаний бота'

    #
    last_mess_id = user_action.get_last_mess_id(user_id)  # GET-
    if last_mess_id:
        try:
            bot.delete_message(user_id, last_mess_id)
        except ApiTelegramException:
            pass
    new_message = bot.send_message(user_id, mess, parse_mode='HTML', reply_markup=reply_markup)
    user_action.set_last_mess_id(new_message.message_id, user_id)  # SET-


def show_details(remind):
    cd = datetime.strptime(remind[6], "%Y-%m-%d %H:%M:%S")
    status = remind[10] + ' - <b>' + remind[11] + '</b>' if remind[10] == 'ERROR' else remind[10]

    result = (f'<b>Группа: </b>{remind[3]}'
              f'\n<b>Дата: </b>{cd.strftime("%d.%m.%Y")}'
              f'\n<b>Период: </b>{get_text_period(remind[7], remind[8])} в {cd.strftime("%H:%M")}'
              f'\n<b>Статус: </b>{status}'
              f'\n<b>Сообщение: </b>\n{remind[9]}')
    return result
