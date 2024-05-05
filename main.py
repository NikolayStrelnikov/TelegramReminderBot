import time
from datetime import datetime

from telebot import types
from telebot.apihelper import ApiTelegramException

from config import ADMIN_CHAT_ID
from logger import logger
from reminder import reminder_wait
from utils import bot, build_menu, create_err_msg, text_processor, choose_period, select_period, show_details


# КОМАНДЫ ------------------------------------------------
@bot.message_handler(commands=['start', 'help'])
def user_start(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if chat_id == user_id:
        name = message.from_user.first_name
        surname = message.from_user.last_name
        mess = (f'Привет! <b>{name if name else ""} {surname if surname else ""} </b>'
                f'\nЭто бот для напоминаний в Телеграм'
                f'\nЧтобы управлять напоминаниями в группе:'
                f'\n  1. Добавьте в группу бота '
                f'\n  2. Отправьте в этой группе боту команду /start@AlfaReminderBot'
                f'\n\nЧтобы создать напоминание, введите команду /set'
                f'\nНапоминания создаются для любого чата, где вы уже стартовали бота'
                f'\nЧтобы редактировать или удалить напоминание, введите команду /edit')
    # Групповой чат
    else:
        mess = (f'Привет!'
                f'\nВы добавили в группу бот для напоминаний в Телеграм'
                f'\nТеперь вы можете управлять своими напоминаниями в этой группе'
                f'\nВсе необходимые команды доступны в персональном чате с ботом')

    # Проверка на повторную регистрацию
    username = message.from_user.username if message.from_user.username else user_id
    title = message.chat.title if message.chat.title else 'Мой персональный чат'
    if bot.user_action.check_create_user(user_id, chat_id):
        bot.user_action.set_new_user(chat_id=chat_id, user_id=user_id, title=title, username=username)
    else:
        bot.user_action.update_exist_user(chat_id=chat_id, user_id=user_id, title=title, username=username)
    bot.send_message(chat_id, mess, parse_mode='HTML')


@bot.message_handler(commands=['set'])
def user_set_menu(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if chat_id == user_id:
        groups = bot.user_action.get_groups(user_id)
        keyboard = types.InlineKeyboardMarkup()
        button_list = []
        for i in groups:
            button_list.append(types.InlineKeyboardButton(text=i[1], callback_data=f'CREATE:{i[0]}'))
        keyboard.add(*button_list)
        # n_cols = 1 is for single column and multiple rows
        reply_markup = types.InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
        mess = f'Выберите чат, где вы хотите создать напоминание'

        last_mess_id = bot.user_action.get_last_mess_id(user_id)
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
        bot.send_message(chat_id, mess, parse_mode='HTML')


@bot.message_handler(commands=['edit'])
def user_delete_menu(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if chat_id == user_id:
        all_reminds = bot.user_action.get_all_active(user_id)
        last_mess_id = bot.user_action.get_last_mess_id(user_id)
        bot.user_action.delete_update_event(user_id)

        if all_reminds:
            # Преобразование строки в объект datetime
            for i in range(len(all_reminds)):
                all_reminds[i] = (all_reminds[i][:2] +
                                  (datetime.strptime(all_reminds[i][2], "%Y-%m-%d %H:%M:%S"),) +
                                  all_reminds[i][3:])
            # Сортировка по дате
            all_reminds.sort(key=lambda x: x[2])
        keyboard = types.InlineKeyboardMarkup()
        button_list = []
        for i in all_reminds:
            if i[3] == 'PAUSE':
                actual = '⏸'
                if i[4] == 'EDIT_DATE':
                    actual = '⏰'
                elif i[4] == 'EDIT_PERIOD':
                    actual = '💫'
                elif i[4] == 'EDIT_TEXT':
                    actual = '✏️'
            elif i[3] == 'ERROR':
                actual = '⚠️'
            else:
                actual = i[2].strftime("%d.%m.%Y")
            button_list.append(types.InlineKeyboardButton(text=f'{actual} : {i[1]}', callback_data=f'MODIFY:{i[0]}'))
        if button_list:
            button_list.append(types.InlineKeyboardButton(text='⬅️  Отмена', callback_data='CANCEL'))
        keyboard.add(*button_list)
        reply_markup = types.InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
        mess = f'Выберите напоминание, которое хотите изменить или удалить' if all_reminds \
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
        bot.send_message(chat_id, mess, parse_mode='HTML')


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


# СООБЩЕНИЯ -------------------------------------------------
@bot.message_handler(content_types=['text'])
def user_set_remind(message: types.Message):
    if message.chat.id == message.from_user.id:
        text_processor(message)


# ВСЕ КНОПКИ ------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def user_set_chat(call: types.CallbackQuery):
    if call.data.startswith('MODIFY:'):
        base_id = int(call.data.partition(':')[2])
        remind = bot.user_action.get_message_by_id(base_id)
        if remind:
            mess = show_details(remind) + (f'\n\n<b>Желаете отредактировать, '
                                           f'{"остановить" if remind[10] == "ACTIVE" else "активировать"} '
                                           f'или удалить напоминание?</b>')

            keyboard = types.InlineKeyboardMarkup()
            button_list = [
                types.InlineKeyboardButton(text='⏰  Дата/Время', callback_data=f'EDIT_DATE:{base_id}'),
                types.InlineKeyboardButton(text='💫  Период', callback_data=f'EDIT_PERIOD:{base_id}'),
                types.InlineKeyboardButton(text='✏️  Текст', callback_data=f'EDIT_TEXT:{base_id}'),
                types.InlineKeyboardButton(text=f'{"⏸  Стоп" if remind[10] == "ACTIVE" else "▶️  Старт"}',
                                           callback_data=f'PAUSE:{base_id}'),
                types.InlineKeyboardButton(text='🗑  Удалить', callback_data=f'PRE_DEL:{base_id}'),
                types.InlineKeyboardButton(text='⬅️  Отмена', callback_data='CANCEL')
            ]
            keyboard.add(*button_list)
            reply_markup = types.InlineKeyboardMarkup(build_menu(button_list, n_cols=2))

            bot.edit_message_text(mess, call.message.chat.id, call.message.message_id,
                                  reply_markup=reply_markup, parse_mode='HTML')
        else:
            bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data.startswith('EDIT_'):
        status_and_column = call.data.partition(':')[0]
        base_id = int(call.data.partition(':')[2])
        bot.user_action.set_status_by_id('PAUSE', status_and_column, base_id)
        remind = bot.user_action.get_message_by_id(base_id)
        mess = show_details(remind)
        if status_and_column == 'EDIT_DATE':
            mess += f'\n\n<b>Введите новую дату напоминания</b>'
            bot.edit_message_text(mess, call.message.chat.id, call.message.message_id, parse_mode='HTML')
        elif status_and_column == 'EDIT_PERIOD':
            select_period(user_id=call.message.chat.id, base_id=base_id)
        elif status_and_column == 'EDIT_TEXT':
            mess += f'\n\n<b>Введите новый текст сообщения</b>'
            bot.edit_message_text(mess, call.message.chat.id, call.message.message_id, parse_mode='HTML')

    elif call.data.startswith('PAUSE:'):
        base_id = int(call.data.partition(':')[2])
        remind = bot.user_action.get_message_by_id(base_id)
        if remind[10] == 'ACTIVE':
            bot.user_action.set_status_by_id('PAUSE', 'PAUSE', base_id)
            mess = f'Напоминание в группе <b>{remind[3]}</b> приостановлено'
        else:
            bot.user_action.set_status_by_id('ACTIVE', 'ACTIVE', base_id)
            mess = f'Напоминание в группе <b>{remind[3]}</b> активно'
            if remind[10] == 'ERROR':
                mess += f'\nНеобходимо исправить ошибку: <b>{remind[11]}</b>'
            else:
                date_time = datetime.strptime(remind[6], "%Y-%m-%d %H:%M:%S")
                next_date = ' будет обновлено автоматически через минуту'
                if date_time > datetime.now():
                    next_date = ': ' + date_time.strftime('%d.%m.%Y %H:%M')
                mess += '\nВремя следующего сообщения' + next_date
        bot.edit_message_text(mess, call.message.chat.id, call.message.message_id, parse_mode='HTML')

    elif call.data.startswith('PRE_DEL:'):
        base_id = int(call.data.partition(':')[2])
        mess = f'Подтвердите удаление события'
        keyboard = types.InlineKeyboardMarkup()
        button_list = [
            types.InlineKeyboardButton(text='🗑 Подтвердить', callback_data=f'DELETE:{base_id}'),
            types.InlineKeyboardButton(text='◀️ Отменить', callback_data=f'CANCEL')
        ]
        keyboard.add(*button_list)
        reply_markup = types.InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
        bot.edit_message_text(mess, call.message.chat.id, call.message.message_id,
                              reply_markup=reply_markup, parse_mode='HTML')

    elif call.data.startswith('DELETE:'):
        base_id = int(call.data.partition(':')[2])
        bot.user_action.delete_event_by_id(base_id)
        mess = f'Напоминание удалено'
        bot.edit_message_text(mess, call.message.chat.id, call.message.message_id, parse_mode='HTML')

    elif call.data.startswith('CREATE:'):
        chosen_chat_id = int(call.data.partition(':')[2])
        user_id = call.message.chat.id  # call возвращает id бота, берем чат

        # создает запись NEW !!!
        bot.user_action.set_new_event(chat_id=chosen_chat_id, user_id=user_id)
        mess = f'Введите текст напоминания'
        bot.edit_message_text(mess, call.message.chat.id, call.message.message_id, parse_mode='HTML')

    elif call.data.startswith('PERIOD:'):
        # user_id = call.message.chat.id
        choose = tuple(call.data.split(':'))[1]
        base_id = int(tuple(call.data.split(':'))[2])
        # записали периодичность в базу
        bot.user_action.set_period(period=choose, db_id=base_id)

        mess = choose_period(choose=choose, base_id=base_id)
        bot.edit_message_text(mess, call.message.chat.id, call.message.message_id, parse_mode='HTML')

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
