import calendar
import threading
from datetime import datetime, timedelta

from dateutil import relativedelta

from config import ADMIN_CHAT_ID
from logger import logger
from utils import bot, check_workday

remind_timer = None


# Метод расчета времени ожидания до вызова таймера
def reminder_wait():
    global remind_timer

    timeout = 60
    actual_queue = bot.user_action.get_actual_queue()
    # logger.debug(f'actual_queue {actual_queue}')
    need_update_queue = bot.user_action.get_update_queue()
    delta = (datetime.strptime(actual_queue[0][3], '%Y-%m-%d %H:%M:%S') - datetime.now()).total_seconds() \
        if bool(actual_queue) else 0

    # Если текущий таймер активен, отменяем его
    if remind_timer and remind_timer.is_alive():
        # logger.debug(f'Stop timer {timeout, delta}')
        remind_timer.cancel()

    # Создаем и запускаем новый таймер
    if 0 < delta < timeout:
        remind_timer = threading.Timer(delta, reminder_send, actual_queue)
        logger.debug(f'Remind: {delta, actual_queue}')
    elif need_update_queue:
        remind_timer = threading.Timer(timeout, reminder_update_base, need_update_queue)
        logger.debug(f'Update: {timeout, need_update_queue}')
    else:
        remind_timer = threading.Timer(timeout, reminder_send, [])

    remind_timer.start()


# Метод рассылки сообщений
def reminder_send(*args):
    if args:
        for i in args:
            base_id = i[0]
            chat_id = i[1]
            message = f'🌟<b><u>Напоминание</u></b>:\n\n{i[6]}'
            try:
                bot.send_message(chat_id, message, 'html')
            except Exception as e:
                logger.error(f'Error Exception: {e}')
                message_error = f'{i}\n\n{e}'
                bot.telegram_client.post(method='sendMessage',
                                         params={'text': message_error,
                                                 'chat_id': ADMIN_CHAT_ID})
                bot.user_action.set_status_by_id('ERROR', str(e), base_id)

                # if e.result.status_code == 403:
                #     if ('bot was blocked by the user' in e.result.text
                #             or 'bot can\'t initiate conversation with a user' in e.result.text
                #             or 'user is deactivated' in e.result.text):
                #         error_message = logger.error(f'Error Blocked: {chat_id}')
                #         bot.telegram_client.post(method='sendMessage',
                #                                  params={'text': error_message,
                #                                          'chat_id': ADMIN_CHAT_ID})
                #         bot.user_action.delete_all_by_user_id(chat_id)
                #     elif ('bot was kicked from the group chat' in e.result.text
                #           or 'bot was blocked by the channel' in e.result.text):
                #         error_message = logger.error(f'Error Kicked: {chat_id}')
                #         bot.telegram_client.post(method='sendMessage',
                #                                  params={'text': error_message,
                #                                          'chat_id': ADMIN_CHAT_ID})
                #         bot.user_action.delete_all_by_chat_id(chat_id)
                # elif e.result.status_code == 400:
                #     if 'group chat was upgraded to a supergroup chat' in e.result.text:
                #         logger.error(f'Error ID Group: {chat_id}')
                #         # Получение нового идентификатора чата
                #         updates = bot.get_updates()
                #         for update in updates:
                #             if update.message and update.message.migrate_to_chat_id:
                #                 new_chat_id = update.message.migrate_to_chat_id
                #                 error_message = logger.error(f'New/Old Group chat ID: {new_chat_id, chat_id}')
                #                 bot.telegram_client.post(method='sendMessage',
                #                                          params={'text': error_message,
                #                                                  'chat_id': ADMIN_CHAT_ID})
                #                 # Сохраните новый идентификатор чата и используйте его в будущем
                #                 bot.user_action.set_edit_chat_id(new_chat_id, chat_id)
                #
                #                 # chat_id = new_chat_id
                #                 bot.send_message(new_chat_id, message, 'html')
                #                 # break
                # else:
                #     logger.error(f'Error ApiException: {e}')
                #     bot.telegram_client.post(method='sendMessage',
                #                              params={'text': e,
                #                                      'chat_id': ADMIN_CHAT_ID})
                #     raise e

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

            if factor.isdigit() and int(factor) > 0:
                factor_i = int(factor)
                check_factor = check_workday(factor)
                if period == 'ONETIME':
                    bot.user_action.delete_event_by_id(base_id)

                elif period == 'MINUTE':
                    if factor_i < 1000:
                        next_date_time = last_up
                        while next_date_time < datetime.now():
                            next_date_time += timedelta(minutes=factor_i)
                        bot.user_action.set_status_update(last_up, next_date_time, base_id)
                    else:
                        err_mess = 'период в минутах более 1000'
                        bot.user_action.set_status_by_id('ERROR', err_mess, base_id)

                elif period == 'HOUR':
                    if factor_i < 1000:
                        next_date_time = last_up
                        while next_date_time < datetime.now():
                            next_date_time += timedelta(hours=factor_i)
                        bot.user_action.set_status_update(last_up, next_date_time, base_id)
                    else:
                        err_mess = 'период в часах более 1000'
                        bot.user_action.set_status_by_id('ERROR', err_mess, base_id)

                elif period == 'WORKDAY':
                    if check_factor:
                        next_date = last_up_date
                        while next_date <= datetime.now().date():
                            current_week_day = next_date.weekday() + 1
                            delta = 7 - current_week_day + int(str(check_factor)[0])
                            for week_day in str(check_factor):
                                if int(week_day) > current_week_day:
                                    delta = int(week_day) - current_week_day
                                    break
                            next_date += timedelta(days=delta)
                        next_date_time = datetime.combine(next_date, last_up_time)
                        bot.user_action.set_status_update(last_up, next_date_time, base_id)
                    else:
                        err_mess = 'не определены дни недели'
                        bot.user_action.set_status_by_id('ERROR', err_mess, base_id)

                elif period == 'DAILY':
                    if factor_i < 367:
                        next_date_time = last_up
                        while next_date_time < datetime.now():
                            next_date_time += timedelta(days=factor_i)
                        bot.user_action.set_status_update(last_up, next_date_time, base_id)
                    else:
                        err_mess = 'период в днях более 366'
                        bot.user_action.set_status_by_id('ERROR', err_mess, base_id)

                elif period == 'WEEKLY':
                    if factor_i < 53:
                        next_date_time = last_up
                        while next_date_time < datetime.now():
                            next_date_time += timedelta(weeks=factor_i)
                        bot.user_action.set_status_update(last_up, next_date_time, base_id)
                    else:
                        err_mess = 'период в неделях более 52'
                        bot.user_action.set_status_by_id('ERROR', err_mess, base_id)

                elif period == 'MONTHLY':
                    if factor_i < 13:
                        next_date = last_up_date
                        while next_date <= datetime.now().date():
                            next_date += relativedelta.relativedelta(months=factor_i)

                        max_next_day = calendar.monthrange(next_date.year, next_date.month)[1]
                        max_next_date_str = f'{next_date.year}-{next_date.month}-{max_next_day} {last_up_time}'
                        current_next_date_str = f'{next_date.year}-{next_date.month}-{up_day}  {last_up_time}'

                        # TODO: Предварительно проверять что там число. А то будет исключение
                        up_day_int = int(up_day)
                        if up_day_int >= max_next_day:
                            next_date_time = datetime.strptime(max_next_date_str, '%Y-%m-%d %H:%M:%S')
                        else:
                            next_date_time = datetime.strptime(current_next_date_str, '%Y-%m-%d %H:%M:%S')

                        while next_date_time.weekday() > 4:  # 0-4 рабочие дни, 5-6 выходные
                            if next_date_time.day == 1:
                                next_date_time += timedelta(days=1)
                                if next_date_time.weekday() > 4:
                                    next_date_time += timedelta(days=1)
                            else:
                                next_date_time -= timedelta(days=1)

                        bot.user_action.set_status_update(up_day_int, next_date_time, base_id)
                    else:
                        err_mess = 'период в месяцах более 12'
                        bot.user_action.set_status_by_id('ERROR', err_mess, base_id)

                else:
                    err_mess = 'невозможно рассчитать период'
                    bot.user_action.set_status_by_id('ERROR', err_mess, base_id)
            else:
                err_mess = 'ошибка расчета периода'
                bot.user_action.set_status_by_id('ERROR', err_mess, base_id)
    reminder_wait()
