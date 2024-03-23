from config import *
from reminder import reminder_wait, reminder_set_active, valid_date, build_menu, create_err_msg
# from logging import getLogger, StreamHandler
from telebot import types

prev_message = None


@bot.message_handler(commands=['start', 'help'])
def user_start(message: types.Message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username
    status = 'REGISTER'
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
    create_new = bot.user_action.create_new(status, user_id, chat_id)
    if create_new:
        bot.user_action.set_register(
            chat_id=chat_id,
            user_id=user_id,
            username=username,
            status=status,
            title=title)
    bot.send_message(message.chat.id, mess, 'html')


@bot.message_handler(commands=['set'])
def user_chat_menu(message: types.Message):
    global prev_message
    chat_id = message.chat.id
    user_id = message.from_user.id
    groups = user_action.get_groups(user_id)
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
        if prev_message:
            bot.delete_message(chat_id=chat_id, message_id=prev_message.message_id)
        mess = f'Выберите чат, где вы хотите создать напоминание'
        prev_message = bot.send_message(chat_id, mess, reply_markup=reply_markup)


@bot.message_handler(commands=['delete'])
def user_chat_menu(message: types.Message):
    global prev_message
    chat_id = message.chat.id
    user_id = message.from_user.id
    reminds = user_action.get_all_active(user_id)
    if chat_id == user_id:
        keyboard = types.InlineKeyboardMarkup()
        button_list = []
        for i in reminds:
            button_list.append(types.InlineKeyboardButton(text=i[1], callback_data=f'DELETE:{i[0]}'))
        keyboard.add(*button_list)
        reply_markup = types.InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
        if prev_message:
            bot.delete_message(chat_id=chat_id, message_id=prev_message.message_id)
        mess = f'Выберите напоминание, которое хотите удалить' if reminds \
            else f'Вы еще не создали ни одного напоминания, воспользуйтесь командой /set'
        prev_message = bot.send_message(chat_id, mess, reply_markup=reply_markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('DELETE:'))
def delete_by_id(call: types.CallbackQuery):
    base_id = int(call.data.partition(':')[2])
    mess = f'Напоминание удалено'
    bot.edit_message_text(mess, call.message.chat.id, call.message.message_id)
    bot.user_action.delete_event_by_id(base_id)


@bot.callback_query_handler(func=lambda call: True & bot.user_action.get_all_count_status(call.message.chat.id) == 0)
def user_set_chat(call: types.CallbackQuery):
    chat_id = int(call.data)
    # создадим один новый черновик
    bot.user_action.set_new_event(chat_id)
    mess = f'О чем вам напомнить?'
    bot.edit_message_text(mess, call.message.chat.id, call.message.message_id)


@bot.message_handler(func=lambda message: bot.user_action.get_count_status(message.from_user.id, 'NEW') == 1)
def user_set_remind(message: types.Message):
    # записали сообщение в базу
    bot.user_action.set_remind(message.html_text, message.chat.id)
    mess = f'Введите дату и время напоминания в формате DD-MM-YYYY hh:mm'
    bot.send_message(message.chat.id, mess, 'html')


@bot.message_handler(func=lambda message: bot.user_action.get_count_status(message.from_user.id, 'TEXT') == 1)
def user_set_date_time(message: types.Message):
    global prev_message
    user_id = message.from_user.id
    chat_id = message.chat.id
    message_date_time = valid_date(message)

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
        if prev_message:
            bot.delete_message(chat_id=chat_id, message_id=prev_message.message_id)
        mess = f'Выберите периодичность и частоту напоминаний бота'
        prev_message = bot.send_message(message.chat.id, mess, 'html', reply_markup=reply_markup)
        bot.user_action.set_time(message.from_user.id)


@bot.callback_query_handler(
    func=lambda call: True & bot.user_action.get_count_status(call.message.chat.id, 'PERIOD') == 1)
def user_set_period(call: types.CallbackQuery):
    message = call.message
    user_id = message.chat.id
    choose = call.data

    # записали периодичность в базу
    bot.user_action.set_period(choose, user_id)
    mess = f'Введите период между регулярными напоминаниями\n'
    if choose == 'ONETIME':
        # проверяем в зависимости от выбора choose
        reminder_set_active(factor='0', user_id=user_id)
        mess = 'Напоминание от бота придет вам один раз'
    elif choose == 'WORKDAY':
        # TOD: как сделать выбор дней недели?
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
                 '2 - каждый второй месяц и т.д.')

    bot.edit_message_text(mess, message.chat.id, message.message_id)


@bot.message_handler(func=lambda message: bot.user_action.get_count_status(message.from_user.id, 'FACTOR') == 1)
def user_set_factor(message: types.Message):
    user_id = message.from_user.id
    factor = message.text
    choose = bot.user_action.get_period(user_id)

    if choose == 'WORKDAY':
        # GOOD: проверяем что заданы цифры (1,2,3,4,5,6,7), пишем фактор в базу...
        val = sorted(set(factor))
        result = ''
        for i in val:
            if i in ["1", "2", "3", "4", "5", "6", "7"]:
                result = result + i
        reminder_set_active(result, user_id)
        mess = f'Напоминание будет повторяться по дням недели: {result}'
        bot.send_message(message.chat.id, mess, 'html')

    elif choose == 'DAILY':
        # GOOD: проверяем что это число и оно не меньше 1 и не больше 366
        try:
            val = int(factor)
            if 0 < val < 367:
                reminder_set_active(val, user_id)
                bot.send_message(message.chat.id,
                                 f"Напоминание будет приходить каждый {val if val > 1 else ''} день", "html")
            else:
                bot.send_message(message.chat.id, 'Число должно быть от 1 до 366', 'html')
        except ValueError:
            bot.send_message(message.chat.id, 'Вы ввели не целое число, попробуйте еще раз', 'html')

    elif choose == 'WEEKLY':
        # проверяем, что это число и оно не больше 366/7=53
        try:
            val = int(factor)
            if 0 < val < 53:
                reminder_set_active(val, user_id)
                bot.send_message(message.chat.id,
                                 f"Напоминание будет приходить каждую {val if val > 1 else ''} неделю", "html")
            else:
                bot.send_message(message.chat.id, 'Число должно быть от 1 до 52', 'html')
        except ValueError:
            bot.send_message(message.chat.id, 'Вы ввели не целое число, попробуйте еще раз', 'html')

    elif choose == 'MONTHLY':
        # проверяем, что это число и оно не больше 12
        try:
            val = int(factor)
            if 0 < val < 13:
                reminder_set_active(val, user_id)
                bot.send_message(message.chat.id,
                                 f"Напоминание будет приходить каждый {val if val > 1 else ''} месяц", "html")
            else:
                bot.send_message(message.chat.id, 'Число должно быть от 1 до 12', 'html')
        except ValueError:
            bot.send_message(message.chat.id, 'Вы ввели не целое число, попробуйте еще раз', 'html')


# -----------------------------------------------------------
# Создаем логирование
# logger = getLogger(__name__)
# logger.addHandler(StreamHandler())
# logger.setLevel('INFO')


# Обернули ошибки запуска
while True:
    try:
        bot.setup_resources()
        reminder_wait()
        bot.polling()
    except Exception as error:
        error_message = create_err_msg(error)
        bot.telegram_client.post(method='sendMessage',
                                 params={'text': error_message,
                                         'chat_id': ADMIN_CHAT_ID})
        # logger.error(error_message)
        bot.shutdown()
