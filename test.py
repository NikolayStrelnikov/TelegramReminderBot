import sqlite3
import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

bot = telebot.TeleBot('7128855265:AAHm6dcVmg8PCJkmOJOSPPb2iCv697VdicQ')


@bot.message_handler(commands=['start'])
def start_message(message):
    conn = sqlite3.connect('db/remind.db')
    cursor = conn.cursor()

    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Button 1', callback_data='1')
    btn2 = types.InlineKeyboardButton('Button 2', callback_data='2')
    markup.add(btn1, btn2)

    cursor.execute("SELECT MAX(MESS_ID) FROM reminders WHERE STATUS='REGISTER' AND USER_ID = ?", (message.from_user.id,))
    row = cursor.fetchone()
    if row[0]:
        print(row)
        print(row[0])
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=row[0])
        except ApiTelegramException:
            pass

    new_message = bot.send_message(message.chat.id, 'Привет, ты написал мне /start', reply_markup=markup)
    cursor.execute("UPDATE reminders SET MESS_ID = ? WHERE STATUS='REGISTER' AND USER_ID = ?",
                   (new_message.message_id, message.from_user.id))
    conn.commit()

    cursor.close()
    conn.close()


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        if call.data == '1':
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text="You clicked Button 1",
                                  reply_markup=None)
        elif call.data == '2':
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id,
                                  text="You clicked Button 2",
                                  reply_markup=None)


bot.polling()
