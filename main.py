import time
from datetime import datetime

from telebot import types

from config import ADMIN_CHAT_ID
from logger import logger, read_last_log
from reminder import reminder_wait
from utils import bot, build_menu, create_err_msg, text_processor, choose_per, select_per
from utils import show_det, add_bot, help_msg, edit_msg, set_msg


# TODO: Сделать общую тайм зону GMT+0 и расчет сообщений по ней.
# TODO: Сделать поддержку английского
# TODO: Сделать префиксы и постфиксы сообщений
# КОМАНДЫ ------------------------------------------------
@bot.message_handler(commands=['start', 'help'])
def user_start(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if message.chat.type == 'private':
        name = message.from_user.first_name
        surname = message.from_user.last_name
        mess = help_msg(name=name, surname=surname)
    # Групповой чат
    else:
        mess = (f'Привет!'
                f'\n\nВы добавили в группу бот для напоминаний в Телеграм'
                f'\nТеперь вы можете управлять своими напоминаниями в этой группе'
                f'\n\nВсе необходимые команды доступны в персональном чате с ботом @{bot.get_me().username}')

    # Проверка на повторную регистрацию
    username = message.from_user.username if message.from_user.username else user_id
    title = message.chat.title if message.chat.title else 'Мой персональный чат'
    add_bot(chat_id, user_id, title, username)
    bot.send_message(chat_id, mess, parse_mode='HTML')


@bot.message_handler(content_types=['new_chat_title', 'new_chat_members', 'left_chat_member',
                                    'migrate_to_chat_id', 'migrate_from_chat_id'])
def handle_system_message(message):
    old_chat_id = message.migrate_from_chat_id
    new_chat_id = message.migrate_to_chat_id
    user_id = message.from_user.id
    username = message.from_user.username if message.from_user.username else user_id
    bot_id = bot.get_me().id
    chat_id = message.chat.id
    title = message.chat.title

    if message.content_type == 'new_chat_title':
        bot.user_action.update_title_group(chat_id=chat_id, title=title)
        logger.info(f'Group title {message.chat.id} changed to: {message.chat.title}')

    if message.new_chat_members is not None:
        for new_member in message.new_chat_members:
            if new_member.id == bot_id:
                add_bot(chat_id, user_id, title, username)
                logger.info(f'Add to group: {title} by user: {user_id} group ID: {chat_id}')

    if message.left_chat_member is not None and message.left_chat_member.id == bot_id:
        message = f'Бот удален из группы {title} пользователем @{username}'
        bot.user_action.set_status_by_chat_id(status='ERROR', edit=message, chat_id=chat_id)
        logger.info(f'Deleted from group: {title} by user: {user_id} group ID: {chat_id}')

    if old_chat_id and new_chat_id:
        message_migrate = f'Migrated group ID: {old_chat_id} to supergroup ID: {new_chat_id}'
        bot.user_action.edit_group_chat_id(new_chat_id=new_chat_id, old_chat_id=old_chat_id)
        logger.info(message_migrate)
        bot.telegram_client.post(method='sendMessage',
                                 params={'text': message_migrate,
                                         'chat_id': ADMIN_CHAT_ID})


@bot.message_handler(commands=['set'])
def user_set_menu(message: types.Message):
    if message.chat.type == 'private':
        set_msg(user_id=message.from_user.id, username=message.from_user.username)
    # Групповой чат
    else:
        mess = f'Управлять напоминаниями группового чата может только их автор с помощью персонального чата с ботом'
        bot.send_message(message.chat.id, mess, parse_mode='HTML')


@bot.message_handler(commands=['edit'])
def user_delete_menu(message: types.Message):
    if message.chat.type == 'private':
        edit_msg(message.from_user.id)
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
        # all_users_str = ' '.join(all_users)
        error_messages = bot.user_action.get_error_mess()
        count_all_users = len(all_users)
        count_active_users = bot.user_action.get_active_users()
        count_mess = bot.user_action.get_count_mess()
        mess = (f'<b><u>Bot Statistic and Status:</u></b>'
                f'\n\n<b>Uptime: </b> {str(uptime_bot).split(".")[0]}'
                f'\n<b>Messages: </b> {count_mess} <b> Errors: </b>{error_messages}'
                f'\n<b>Users: </b> {count_all_users} <b> Active: </b>{count_active_users}'
                # f'\n<b>Registered: </b> {all_users_str}'
                )
        bot.send_message(message.chat.id, mess, parse_mode='HTML')


@bot.message_handler(commands=['log'])
def user_get_status(message: types.Message):
    if message.chat.id == ADMIN_CHAT_ID:
        mess = read_last_log(lines=10)
        bot.send_message(message.chat.id, mess, parse_mode='HTML')


# СООБЩЕНИЯ -------------------------------------------------
@bot.message_handler(content_types=['text'])
def user_set_remind(message: types.Message):
    if message.chat.type == 'private':
        text_processor(message)
    #     print(f"Сообщение локального чата: {chat_type}")
    # if message.chat.type in ['group', 'supergroup']:
    #     print(f"Текущий chat_id: {chat_id}")
    #     print(f"Тип чата: {chat_type}")


# ВСЕ КНОПКИ ------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def user_set_chat(call: types.CallbackQuery):
    if call.data.startswith('MODIFY:'):
        base_id = int(call.data.partition(':')[2])
        remind = bot.user_action.get_message_by_id(base_id)
        if remind:
            mess = show_det(remind) + (f'\n\n<b>Желаете отредактировать, '
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
        mess = show_det(remind)
        if status_and_column == 'EDIT_DATE':
            mess += f'\n\n<b>Введите новую дату напоминания</b>'
            bot.edit_message_text(mess, call.message.chat.id, call.message.message_id, parse_mode='HTML')
        elif status_and_column == 'EDIT_PERIOD':
            select_per(user_id=call.message.chat.id, base_id=base_id)
        elif status_and_column == 'EDIT_TEXT':
            mess += f'\n\n<b>Введите новый текст сообщения</b>'
            bot.edit_message_text(mess, call.message.chat.id, call.message.message_id, parse_mode='HTML')

    elif call.data.startswith('PAUSE:'):
        base_id = int(call.data.partition(':')[2])
        remind = bot.user_action.get_message_by_id(base_id)
        if remind[10] == 'ACTIVE':
            bot.user_action.set_status_by_id('PAUSE', 'PAUSE', base_id)
            mess = f'Напоминание в группе "<b>{remind[3]}</b>" приостановлено'
        else:
            bot.user_action.set_status_by_id('ACTIVE', 'ACTIVE', base_id)
            mess = f'Напоминание в группе "<b>{remind[3]}</b>" активно'
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

        mess = choose_per(choose=choose, base_id=base_id)
        bot.edit_message_text(mess, call.message.chat.id, call.message.message_id, parse_mode='HTML')

    elif call.data.startswith('MSG_SET'):
        set_msg(user_id=call.message.chat.id, username=call.from_user.username)

    elif call.data.startswith('MSG_EDIT'):
        edit_msg(call.message.chat.id)

    elif call.data.startswith('MSG_HELP'):
        mess = help_msg(name=call.from_user.first_name, surname=call.from_user.last_name)
        bot.edit_message_text(mess, call.message.chat.id, call.message.message_id, parse_mode='HTML')
    else:
        bot.delete_message(call.message.chat.id, call.message.message_id)


# -----------------------------------------------------------
while True:
    bot_start_time = time.ctime()
    msg = f'{bot_start_time}: Start Time'
    logger.info(f'Start Bot')
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
        logger.error(f'{error_message}')
        bot.shutdown()
    time.sleep(5)
