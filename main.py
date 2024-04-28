import time
from datetime import datetime

from telebot import types
from telebot.apihelper import ApiTelegramException

from config import ADMIN_CHAT_ID
from logger import logger
from reminder import reminder_wait
from utils import bot, build_menu, create_err_msg, text_processor


# КОМАНДЫ -----------------------------------------------------------
@bot.message_handler(commands=['start', 'help'])
def user_start(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else user_id
    title = message.chat.title if message.chat.title else 'Мой персональный чат'

    # Персональный чат
    if chat_id == user_id:
        mess = (f'Привет! <b>{username} </b>'
                f'\nЭто бот для напоминаний в Телеграм'
                f'\nЧтобы управлять напоминаниями в группе:'
                f'\n  1. Добавьте в группу бота '
                f'\n  2. Отправьте в этой группе боту команду /start@AlfaReminderBot'
                f'\n\nЧтобы создать напоминание, введите команду /set'
                f'\nНапоминания создаются для любого чата, где вы уже стартовали бота'
                f'\nЧтобы удалить напоминание, введите команду /delete')
    # Групповой чат
    else:
        mess = (f'Привет!'
                f'\nВы добавили в группу бот для напоминаний в Телеграм'
                f'\nТеперь вы можете управлять своими напоминаниями в этой группе'
                f'\nВсе необходимые команды доступны в персональном чате с ботом')

    # Проверка на повторную регистрацию
    create_new = bot.user_action.create_new(user_id, chat_id)
    if create_new:
        bot.user_action.set_new_user(chat_id=chat_id, user_id=user_id, title=title, username=username)
    bot.send_message(chat_id, mess, parse_mode='HTML')


@bot.message_handler(commands=['set'])
def user_set_menu(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    groups = bot.user_action.get_groups(user_id)
    last_mess_id = bot.user_action.get_last_mess_id(user_id)
    if chat_id == user_id:
        # удалим все предыдущие черновики этого пользователя
        bot.user_action.delete_event(user_id)

        keyboard = types.InlineKeyboardMarkup()
        button_list = []
        for i in groups:
            button_list.append(types.InlineKeyboardButton(text=i[1], callback_data=i[0]))
        keyboard.add(*button_list)
        # n_cols = 1 is for single column and multiple rows
        reply_markup = types.InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
        mess = f'Выберите чат, где вы хотите создать напоминание'

        if last_mess_id:
            try:
                bot.delete_message(chat_id, last_mess_id)
            except ApiTelegramException:
                pass
        new_message = bot.send_message(chat_id, mess, parse_mode='HTML', reply_markup=reply_markup)
        bot.user_action.set_last_mess_id(new_message.message_id, user_id)

    # Групповой чат
    else:
        mess = f'Управлять напоминаниями группового чата может только их автор с помощью персонального чата с ботом'
        bot.send_message(message.chat.id, mess, parse_mode='HTML')


@bot.message_handler(commands=['delete'])
def user_delete_menu(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    reminds = bot.user_action.get_all_active(user_id)
    last_mess_id = bot.user_action.get_last_mess_id(user_id)
    if chat_id == user_id:
        keyboard = types.InlineKeyboardMarkup()
        button_list = []
        for i in reminds:
            button_list.append(types.InlineKeyboardButton(text=i[1], callback_data=f'DELETE:{i[0]}'))
        keyboard.add(*button_list)
        reply_markup = types.InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
        mess = f'Выберите напоминание, которое хотите удалить' if reminds \
            else f'Вы еще не создали ни одного напоминания, воспользуйтесь командой /set'

        if last_mess_id:
            try:
                bot.delete_message(chat_id, last_mess_id)
            except ApiTelegramException:
                pass
        new_message = bot.send_message(chat_id, mess, parse_mode='HTML', reply_markup=reply_markup)
        bot.user_action.set_last_mess_id(new_message.message_id, user_id)

    # Групповой чат
    else:
        mess = f'Управлять напоминаниями группового чата может только их автор с помощью персонального чата с ботом'
        bot.send_message(message.chat.id, mess, parse_mode='HTML')


@bot.message_handler(commands=['status'])
def user_get_status(message: types.Message):
    if message.chat.id == ADMIN_CHAT_ID:
        start_time = datetime.strptime(bot_start_time, "%a %b %d %H:%M:%S %Y")
        uptime_bot = datetime.now() - start_time
        all_users = bot.user_action.get_all_users()
        all_users_str = ' '.join(all_users)
        count_all_users = len(all_users)
        count_active_users = bot.user_action.get_active_users()
        count_mess = bot.user_action.get_count_mess()
        mess = (f'<b><u>Bot Statistic and Status:</u></b>'
                f'\n\n<b>Uptime: </b> {str(uptime_bot).split(".")[0]}'
                f'\n<b>Messages: </b> {count_mess}'
                f'\n<b>Users: </b> {count_all_users} <b> Active: </b>{count_active_users}'
                f'\n<b>Registered: </b> {all_users_str}')
        bot.send_message(message.chat.id, mess, parse_mode='HTML')


# СООБЩЕНИЯ -----------------------------------------------------------
@bot.message_handler(content_types=['text'])
def user_set_remind(message: types.Message):
    if message.chat.id == message.from_user.id:
        text_processor(message)
    else:
        mess = (f'Необходимо отключить доступ бота к сообщениям группового чата \n'
                f'Управлять напоминаниями группового чата может только их автор с помощью персонального чата с ботом')
        bot.send_message(message.chat.id, mess, parse_mode='HTML')


# КНОПКИ -----------------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def user_set_chat(call: types.CallbackQuery):
    step = bot.user_action.get_current_status(call.message.chat.id)
    if call.data.startswith('DELETE:'):
        base_id = int(call.data.partition(':')[2])
        bot.user_action.delete_event_by_id(base_id)
        mess = f'Напоминание удалено'
        bot.edit_message_text(mess, call.message.chat.id, call.message.message_id)
    elif step not in ['NEW', 'TEXT', 'PERIOD', 'FACTOR']:
        chat_id = int(call.data)
        user_id = call.message.chat.id  # call возвращает id бота, берем чат
        bot.user_action.set_new_event(chat_id=chat_id, user_id=user_id)
        mess = f"О чём вам напомнить?"
        bot.edit_message_text(mess, call.message.chat.id, call.message.message_id)
    elif step == 'PERIOD':
        message = call.message
        user_id = message.chat.id
        choose = call.data

        # записали периодичность в базу
        bot.user_action.set_period(choose, user_id)
        mess = f'Введите период между регулярными напоминаниями\n'
        if choose == 'ONETIME':
            # проверяем в зависимости от выбора choose
            bot.user_action.set_active(factor='0', user_id=user_id)
            mess = 'Напоминание от бота придет вам один раз'
        elif choose == 'WORKDAY':
            mess += ('1 - повторение по понедельникам в указанное вами время,\n'
                     '2,4 - повторение по вторникам и четвергам,\n'
                     '1,2,3,4,5 - повторение по будням')
        elif choose == 'DAILY':
            mess += ('1 - повторение ежедневно в указанное вами время,\n'
                     '2 - каждый второй день и т.д.')
        elif choose == 'WEEKLY':
            mess += ('1 - повторение еженедельно в указанное вами время и день недели,\n'
                     '2 - каждую вторую неделю и т.д.')
        elif choose == 'MONTHLY':
            mess += ('1 - повторение ежемесячно в указанное вами время и число месяца,\n'
                     '2 - каждый второй месяц и т.д.\n'
                     'Если выбранного числа не будет в месяце, то сообщение придёт в последний день\n'
                     'Если число выпадет на выходной, то сообщение придёт в пятницу')
        else:
            mess = 'Вы нашли ошибку 1 в Боте. Напишите автору, он будет очень благодарен'

        bot.edit_message_text(mess, message.chat.id, message.message_id)
    else:
        bot.delete_message(call.message.chat.id, call.message.message_id)


# -----------------------------------------------------------
while True:
    bot_start_time = time.ctime()
    msg = f'{bot_start_time}: Start Time'
    logger.info(msg)
    bot.telegram_client.post(method='sendMessage',
                             params={'text': msg,
                                     'chat_id': ADMIN_CHAT_ID})
    try:
        bot.setup_resources()
        reminder_wait()
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as error:
        error_message = create_err_msg(error)
        bot.telegram_client.post(method='sendMessage',
                                 params={'text': error_message,
                                         'chat_id': ADMIN_CHAT_ID})
        logger.error(error_message)
        bot.shutdown()
    time.sleep(5)
