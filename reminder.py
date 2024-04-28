import calendar
import threading
from datetime import datetime, timedelta

from dateutil import relativedelta
from telebot.apihelper import ApiException

from utils import user_action, bot


# Метод расчета времени ожидания до вызова таймера
def reminder_wait():
    timeout = 60
    actual_queue = user_action.get_actual_queue()
    need_update_queue = user_action.get_update_queue()
    delta = (datetime.strptime(actual_queue[0][3], '%Y-%m-%d %H:%M:%S') - datetime.now()).total_seconds() \
        if bool(actual_queue) else 0

    if 0 < delta < timeout:
        re_timer = threading.Timer(delta, reminder_send, actual_queue)
    elif need_update_queue:
        re_timer = threading.Timer(timeout, reminder_update_base, need_update_queue)
    else:
        re_timer = threading.Timer(timeout, reminder_send, [])

    if re_timer.is_alive():
        re_timer.cancel()
    re_timer.start()


# Метод рассылки сообщений
def reminder_send(*args):
    if args:
        for i in args:
            chat_id = i[1]
            message = f'🌟<b><u>Напоминание</u></b>:\n\n{i[6]}'
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
                bot.user_action.delete_event_by_id(base_id)

            elif period == 'MINUTE':
                next_date_time = last_up
                while next_date_time < datetime.now():
                    next_date_time += timedelta(minutes=int(factor))
                user_action.set_status_update(last_up, next_date_time, base_id)

            elif period == 'HOUR':
                next_date_time = last_up
                while next_date_time < datetime.now():
                    next_date_time += timedelta(hours=int(factor))
                user_action.set_status_update(last_up, next_date_time, base_id)

            elif period == 'WORKDAY':
                next_date = last_up_date
                while next_date <= datetime.now().date():
                    current_week_day = next_date.weekday() + 1
                    delta = 7 - current_week_day + int(factor[0])
                    for wd in factor:
                        if int(wd) > current_week_day:
                            delta = int(wd) - current_week_day
                            break
                    next_date += timedelta(days=delta)
                next_date_time = datetime.combine(next_date, last_up_time)
                user_action.set_status_update(last_up, next_date_time, base_id)

            elif period == 'DAILY':
                next_date_time = last_up
                while next_date_time < datetime.now():
                    next_date_time += timedelta(days=int(factor))
                user_action.set_status_update(last_up, next_date_time, base_id)

            elif period == 'WEEKLY':
                next_date_time = last_up
                while next_date_time < datetime.now():
                    next_date_time += timedelta(weeks=int(factor))
                user_action.set_status_update(last_up, next_date_time, base_id)

            elif period == 'MONTHLY':
                next_date = last_up_date
                while next_date <= datetime.now().date():
                    next_date += relativedelta.relativedelta(months=int(factor))

                max_next_day = calendar.monthrange(next_date.year, next_date.month)[1]
                max_next_date_str = f'{next_date.year}-{next_date.month}-{max_next_day} {last_up_time}'
                current_next_date_str = f'{next_date.year}-{next_date.month}-{up_day}  {last_up_time}'

                up_day_int = int(up_day)
                if up_day_int >= max_next_day:
                    next_date_time = datetime.strptime(max_next_date_str, '%Y-%m-%d %H:%M:%S')
                else:
                    next_date_time = datetime.strptime(current_next_date_str, '%Y-%m-%d %H:%M:%S')
                while next_date_time.weekday() > 4:  # 0-4 рабочие дни, 5-6 выходные
                    next_date_time -= timedelta(days=1)
                user_action.set_status_update(up_day_int, next_date_time, base_id)
    reminder_wait()
