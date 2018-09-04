import telebot
import config
import time
import os
bot = telebot.TeleBot(config.access_token)


@bot.message_handler(commands=['ges'])
def ff(message):
    bot.send_voice(message.chat.id, "AwADAgADLAQAAnsUCEjRTr3YEWakAAEC")


@bot.message_handler(commands=['test'])
def find_file_ids(message):
    count = 0
    for file in os.listdir('music/'):
        if file.split('.')[-1] == 'ogg':
            f = open('music/'+file, 'rb')
            msg = bot.send_voice(message.chat.id, f, None)
            count += 1
            # А теперь отправим вслед за файлом его file_id
            bot.send_message(message.chat.id, msg.voice.file_id, reply_to_message_id=msg.message_id)
            print(msg.voice.file_id + " " + str(count))
        time.sleep(11)


if __name__ == '__main__':
    bot.polling(none_stop=True)
