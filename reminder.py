from config import user_action, bot
import threading
import calendar
from datetime import datetime, timedelta
from dateutil import relativedelta
from dateutil.parser import parse, parserinfo
from telebot.apihelper import ApiException


# Метод расчета времени ожидания до вызова таймера
def reminder_wait():
    timeout = 60
    actual_queue = user_action.get_actual_queue()
    delta = (datetime.strptime(actual_queue[0][3], '%Y-%m-%d %H:%M:%S') - datetime.now()).total_seconds() \
        if bool(actual_queue) else 0
    need_update_queue = user_action.get_update_queue()
    # print(datetime.now(), f'{delta} - секунд до следующего запуска сообщения, '
    #                       f'если меньше {timeout}, пишем в экземпляр таймера')

    if 0 < delta < timeout:
        re_timer = threading.Timer(delta, reminder_send, actual_queue)
        # если есть что послать, создаем напоминания
        # print(datetime.now(), 'ПОШЛЕМ ЭТО', delta, actual_queue)
    elif need_update_queue:
        re_timer = threading.Timer(timeout, reminder_update_base, need_update_queue)
        # если есть что обновить в базе, создаем обновления
        # print(datetime.now(), 'ОБНОВИМ БАЗУ', timeout, need_update_queue)
    else:
        re_timer = threading.Timer(timeout, reminder_send, [])
        # если не посылаем и не обновляем данных, то просто перезапускаем таймер
        # print(datetime.now(), 'НИЧЕГО НЕ ПОШЛШЕМ, ОБНОВИМ ТАЙМЕР')

    # Проверим, не запущен ли таймер после краша бота, возможно это его остановит
    if re_timer.is_alive():
        re_timer.cancel()
    re_timer.start()


# Метод рассылки сообщений
def reminder_send(*args):
    if args:
        for i in args:
            chat_id = i[1]
            message = f'<b><u>🌟Напоминание:</u></b>\n\n{i[6]}'
            try:
                bot.send_message(chat_id, message, 'html')
            except ApiException as e:
                if e.result.status_code == 403:
                    if ('bot was blocked by the user' in e.result.text
                            or 'bot can\'t initiate conversation with a user' in e.result.text
                            or 'user is deactivated' in e.result.text):
                        bot.user_action.delete_all_by_user_id(chat_id)
                    elif ('bot was kicked from the group chat' in e.result.text
                          or 'bot was blocked by the channel' in e.result.text):
                        bot.user_action.delete_all_by_chat_id(chat_id)
                else:
                    raise e
    reminder_update_base(*args)


# Метод обновления дат в базе данных
def reminder_update_base(*args):
    if args:
        for i in args:
            base_id = i[0]
            up_day = i[2]
            last_up = datetime.strptime(i[3], '%Y-%m-%d %H:%M:%S')
            last_up_date = last_up.date()
            last_up_time = last_up.time()
            period = i[4]
            factor = i[5]

            if period == 'ONETIME':
                # разовые вообще удалять надо
                # next_date = 0
                # user_action.set_status_update(last_up, next_date, base_id)
                bot.user_action.delete_event_by_id(base_id)

            elif period == 'MINUTE':
                next_date = last_up
                while next_date < datetime.now():
                    next_date += timedelta(minutes=int(factor))
                user_action.set_status_update(last_up, next_date, base_id)

            elif period == 'HOUR':
                next_date = last_up
                while next_date < datetime.now():
                    next_date += timedelta(hours=int(factor))
                user_action.set_status_update(last_up, next_date, base_id)

            elif period == 'WORKDAY':
                current_week_day = last_up_date.weekday() + 1
                delta = 7 - current_week_day + int(factor[0])
                for wd in factor:
                    if int(wd) > current_week_day:
                        delta = int(wd) - current_week_day
                        break
                next_date = datetime.combine((last_up_date + timedelta(days=delta)), last_up_time)
                user_action.set_status_update(last_up, next_date, base_id)

            elif period == 'DAILY':
                next_date = datetime.combine((last_up_date + timedelta(days=int(factor))), last_up_time)
                user_action.set_status_update(last_up, next_date, base_id)

            elif period == 'WEEKLY':
                next_date = datetime.combine((last_up_date + timedelta(weeks=int(factor))), last_up_time)
                user_action.set_status_update(last_up, next_date, base_id)

            elif period == 'MONTHLY':
                next_date = last_up_date + relativedelta.relativedelta(months=int(factor))
                max_next_day = calendar.monthrange(next_date.year, next_date.month)[1]
                max_next_date = f'{next_date.year}-{next_date.month}-{max_next_day} {last_up_time}'
                up_day_int = int(up_day)
                if up_day_int >= max_next_day:
                    next_date_time = datetime.strptime(max_next_date, '%Y-%m-%d %H:%M:%S')
                else:
                    next_date_time = datetime.combine(next_date, last_up_time)
                user_action.set_status_update(up_day_int, next_date_time, base_id)
    reminder_wait()


# Метод проверки даты-времени
def valid_date(message):
    try:
        # date_time = datetime.strptime(message.text, '%Y-%m-%d %H:%M')
        date_time = parse(message.text, dayfirst=True, fuzzy=False, parserinfo=RussianParserInfo())
        if date_time < datetime.now():
            bot.reply_to(message, f'Введены дата и/или время в прошлом: {date_time} \nПопробуйте еще раз')
            return False
        elif date_time > datetime(2099, 12, 31):
            bot.reply_to(message, f'Ограничимся напоминаниями в нашем веке до 2099 года? \nПопробуйте еще раз')
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


# Метод активации сообщения
def reminder_set_active(factor, user_id):
    bot.user_action.set_active(factor, user_id)


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
