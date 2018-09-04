import threading
import os
import xlsxwriter
import config
import telebot
import dbsqlite
import usersBD
import datetime
import random
import time
import shelve
from telebot import types

bot = telebot.TeleBot(config.access_token)
db = usersBD.db
users_db = usersBD.UsersDB(db)

session = dbsqlite.s
learn_words = shelve.open("learn_words", flag='c')
ref_link = 'https://telegram.me/{}?start={}'


@bot.message_handler(commands=['ref'])
def get_my_ref(message):
    bot_name = 'RussianLanguageBot'
    bot.reply_to(message, text=ref_link.format(bot_name, message.chat.id))


def get_markup_for_language():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("English")
    # markup.row('Русский')
    return markup


def set_language(message):
    user_ID = message.from_user.id
    if message.text in config.language:
        users_db.set_settings(user_ID, {'language': message.text})
        menu(user_ID)
    else:
        print("set language falsh")
        menu(user_ID)


def generate_markup(murkup, texts, language):
    count = 0
    elems = texts[language]['elems']
    if len(elems) % 2 == 0:
        while count < len(elems) - 1:
            murkup.row(elems[count], elems[count + 1])
            count += 2
    else:
        while count < len(elems) - 1:
            murkup.row(elems[count], elems[count + 1])
            count += 2
        murkup.row(elems[count])

    return murkup


def set_data(user_ID, subscription):
    date = users_db.get_param(user_ID, 'subscription')
    if date <= datetime.datetime.now():
        users_db.set_settings(user_ID, {'subscription': datetime.datetime.now() + datetime.timedelta(days=subscription)})
    else:
        users_db.set_settings(user_ID, {'subscription': date + datetime.timedelta(days=subscription)})


@bot.message_handler(commands=['level'])
def level(message):
    user_ID = message.from_user.id
    language = users_db.get_param(user_ID, 'language')
    texts = config.levels
    markup = generate_markup(types.ReplyKeyboardMarkup(resize_keyboard=True), texts, language)
    msg = bot.send_message(message.chat.id, texts[language]['text'], reply_markup=markup)
    bot.register_next_step_handler(msg, setting_level)


@bot.message_handler(commands=['download'])
def download(message):
    user_ID = message.from_user.id
    language = users_db.get_param(user_ID, 'language')
    data = []
    if users_db.get_param(user_ID, 'account') != 'premium':
        buy_premium_account(user_ID)
    else:
        f = xlsxwriter.Workbook('{user_ID}.xlsx'.format(user_ID=user_ID))
        worksheet = f.add_worksheet()
        for word in users_db.get_param(user_ID, 'words'):
            old_word = session.query(dbsqlite.Words).filter(dbsqlite.Words.word == word).one()
            if language == "English":
                translate = old_word.translate_eng
            elif language == "Persian":
                translate = old_word.translate_pers
            data.append([word, translate])
        row = 0
        col = 0
        for item, cost in data:
            worksheet.write(row, col, item)
            worksheet.write(row, col + 1, cost)
            row += 1
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 25)
        f.close()
        f = open('{user_ID}.xlsx'.format(user_ID=user_ID), "rb")
        bot.send_document(user_ID, f)
        f.close()
        os.remove("{user_ID}.xlsx".format(user_ID=user_ID))
        menu(user_ID)


@bot.message_handler(commands=['language'])
def choose_language(message):
    language = users_db.get_param(message.from_user.id, 'language')
    markup = get_markup_for_language()
    msg = bot.send_message(message.chat.id, config.choose_language[language], reply_markup=markup)
    bot.register_next_step_handler(msg, set_language)


@bot.message_handler(commands=['start'])
def start(message):
    user_ID = message.from_user.id
    splited = message.text.split()
    if users_db.get_param(user_ID, 'user_ID') is None:
        users_db.create_new_user({'user_ID': user_ID, 'language': "English", 'account': 'normal',
                                  'level': "2", 'count': 7, 'today': 0, 'subscription': datetime.datetime.utcnow(),
                                  'last_answer': datetime.datetime.utcnow(), 'words': [], 'vocabulary': []})
        if len(splited) >= 2:
            set_data(user_ID, 3)
            users_db.set_settings(int(splited[1]), {'account': 'premium'})
            print(splited[0] + " " + splited[1])
        print("YO")
        if message.text == config.levels['English']['elems'][0]:
            users_db.set_settings(user_ID, {'level': "1"})
            learn_words[str(user_ID)] = session.query(dbsqlite.Words).filter(
                dbsqlite.Words.level <= users_db.get_param(user_ID, 'level')).all()
            learn_words.close()

        markup = get_markup_for_language()
        msg = bot.send_message(message.chat.id, config.first_message, reply_markup=markup)
        bot.register_next_step_handler(msg, choose_type_learning)
    else:
        menu(user_ID)


def choose_type_learning(message):
    user_ID = message.from_user.id
    if message.text in config.language:
        users_db.set_settings(user_ID, {'language': message.text})
        language = message.text
    else:
        print(message.text + " choose type learning falsh")
        language = users_db.get_param(user_ID, 'language')

    texts = config.choose_type_of_learning
    markup = generate_markup(types.ReplyKeyboardMarkup(resize_keyboard=True), texts, language)
    msg = bot.send_message(message.chat.id, texts[language]['text'], reply_markup=markup)
    bot.register_next_step_handler(msg, choose_level)


def choose_level(message):
    texts = config.levels
    language = users_db.get_param(message.from_user.id, 'language')
    if message.text in config.choose_type_of_learning[language]['elems']:
        markup = generate_markup(types.ReplyKeyboardMarkup(resize_keyboard=True), texts, language)
        msg = bot.send_message(message.chat.id, texts[language]['text'], reply_markup=markup)
        bot.register_next_step_handler(msg, setting_level)
    else:
        print(message.text + " it is falsh")
        menu(message.from_user.id)


def setting_level(message):
    learn_words = shelve.open("learn_words", flag='c')
    user_ID = message.from_user.id
    language = users_db.get_param(user_ID, 'language')
    if message.text == config.levels[language]['elems'][0]:
        users_db.set_settings(user_ID, {'level': "1"})
        learn_words[str(user_ID)] = session.query(dbsqlite.Words).filter(
            dbsqlite.Words.level <= users_db.get_param(user_ID, 'level')).all()
        learn_words.close()
        menu(user_ID)
    elif message.text == config.levels[language]['elems'][1]:
        users_db.set_settings(user_ID, {'level': "2"})
        learn_words[str(user_ID)] = session.query(dbsqlite.Words).filter(
            dbsqlite.Words.level <= users_db.get_param(user_ID, 'level')).all()
        learn_words.close()
        menu(user_ID)
    elif message.text == config.levels[language]['elems'][2]:
        users_db.set_settings(user_ID, {'level': "4"})
        learn_words[str(user_ID)] = session.query(dbsqlite.Words).filter(
            dbsqlite.Words.level == users_db.get_param(user_ID, 'level')).all()
        learn_words.close()
        menu(user_ID)
    # elif message.text == config.levels[language]['elems'][3]:
    # texts = config.choose_type_of_learning
    # msg = bot.send_message(message.chat.id, 'Back')
    # bot.register_next_step_handler(msg, choose_type_learning)
    else:
        menu(user_ID)


def menu(user_ID):
    texts = config.menu
    language = users_db.get_param(user_ID, 'language')
    date = users_db.get_param(user_ID, 'subscription')
    if datetime.datetime.now() > date:
        users_db.set_settings(user_ID, {'account': 'normal'})
    markup = generate_markup(types.ReplyKeyboardMarkup(resize_keyboard=True), texts, language)
    msg = bot.send_message(user_ID, config.menu[language]['text'], reply_markup=markup)
    bot.register_next_step_handler(msg, route)


def route(message):
    language = users_db.get_param(message.from_user.id, 'language')
    if message.text in config.menu[language]['elems']:
        if config.menu[language]['elems'].index(message.text) == 0:
            get_repeat(message.from_user.id)
        elif config.menu[language]['elems'].index(message.text) == 1:
            learning_words(message.from_user.id)
        elif config.menu[language]['elems'].index(message.text) == 2:
            statistic(message.from_user.id)
        elif config.menu[language]['elems'].index(message.text) == 3:
            commands(message.from_user.id)
    else:
        menu(message.from_user.id)


def gen_answers(rand_words):
    answers = {}
    for i in rand_words:
        answers[i] = [session.query(dbsqlite.Words).filter(dbsqlite.Words.word == i).one().translate_eng]
        while len(answers[i]) != 3:
            rand_word = rand_words[random.randrange(len(rand_words))]
            a = session.query(dbsqlite.Words).filter(dbsqlite.Words.word == rand_word).one().translate_eng
            if a not in answers[i]:
                answers[i].append(a)
        swap = random.randrange(len(answers[i]))
        answers[i][0], answers[i][swap] = answers[i][swap], answers[i][0]

    return answers


def get_repeat(user_ID):
    language = users_db.get_param(user_ID, 'language')
    list_repeat_words = users_db.get_param(user_ID, 'words')
    print(len(list_repeat_words))
    if len(list_repeat_words) == 0:
        bot.send_message(user_ID, config.get_repeat_text[language])
        menu(user_ID)
    elif len(list_repeat_words) <= 7:
        rand_words = list_repeat_words
        markup = generate_markup(types.ReplyKeyboardMarkup(resize_keyboard=True), config.repeat_type, language)
        answers = gen_answers(rand_words)
        msg = bot.send_message(user_ID, config.repeat_type[language]['text'], reply_markup=markup)
        bot.register_next_step_handler(msg, repeat_route, answers, rand_words)
    elif len(list_repeat_words) <= 14:
        rand_words = list_repeat_words
        markup = generate_markup(types.ReplyKeyboardMarkup(resize_keyboard=True), config.repeat_type, language)
        answers = gen_answers(rand_words)
        msg = bot.send_message(user_ID, config.repeat_type[language]['text'], reply_markup=markup)
        bot.register_next_step_handler(msg, repeat_route, answers, rand_words)
    else:
        rand_words = list_repeat_words[-7:]
        while len(rand_words) != 14:
            rand_word = list_repeat_words[random.randrange(len(rand_words))]
            if rand_word not in rand_words:
                rand_words.append(rand_word)
                print('add ' + rand_word)
        print(rand_words)
        markup = generate_markup(types.ReplyKeyboardMarkup(resize_keyboard=True), config.repeat_type, language)
        answers = gen_answers(rand_words)
        msg = bot.send_message(user_ID, config.repeat_type[language]['text'], reply_markup=markup)
        bot.register_next_step_handler(msg, repeat_route, answers, rand_words)


def repeat_route(message, answers, rand_words):
    if message.text == "Choose":
        repeat_words(answers, message.from_user.id, rand_words, choose=True)
    elif message.text == "Writing":
        repeat_words(answers, message.from_user.id, rand_words, writing=True)


def repeat_words(answers, user_ID, rand_words, choose=None, writing=None):
    language = users_db.get_param(user_ID, 'language')
    if len(rand_words) > 0:
        rand_word = rand_words[random.randrange(len(rand_words))]
        rand_words.remove(rand_word)
        word = session.query(dbsqlite.Words).filter(dbsqlite.Words.word == rand_word).one()
        if choose is True:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            print(word.word)
            print(answers[word.word])
            markup.row(answers[word.word][0])
            markup.row(answers[word.word][1])
            markup.row(answers[word.word][2])
            msg = bot.send_message(user_ID, rand_word, reply_markup=markup)
            bot.register_next_step_handler(msg, check_word, word, answers, rand_words, choose)
        else:
            msg = bot.send_message(user_ID, rand_word)
            bot.register_next_step_handler(msg, check_word, word, answers, rand_words)
    else:
        bot.send_message(user_ID, "\U0001F31F *{train_end}* \U0001F31F".format(train_end=config.traning_end[language]),
                         parse_mode="Markdown")
        menu(user_ID)


def check_word(message, word_val, answers, rand_words, choose=None):
    language = users_db.get_param(message.from_user.id, 'language')
    user_ID = message.from_user.id
    if language == "English":
        translate = word_val.translate_eng
        example = word_val.example_eng
    elif language == "Persian":
        translate = word_val.translate_pers
        example = word_val.example_pers
    if message.text == translate:
        bot.send_message(user_ID, "\U0001F44D*{answer}*".format(answer=config.check_word[language][0]),
                         parse_mode="Markdown")
    else:
        bot.send_message(user_ID, "\U0001F534*{answer}*\n"
                                  "*{word}* - {translate_eng}\n"
                                  "[{transcription}]\n"
                                  "_- {example}_\n"
                                  "_- {example_eng}_".format(answer=config.check_word[language][1], word=word_val.word,
                                                             translate_eng=translate,
                                                             transcription=word_val.transcription,
                                                             example=word_val.example,
                                                             example_eng=example), parse_mode="Markdown")
        if len(word_val.audio) > 3:
            bot.send_voice(user_ID, word_val.audio)
        else:
            bot.send_message(user_ID, "not audio")
    repeat_words(answers, message.from_user.id, rand_words, choose)
    pass


def learning_words(user_ID):
    language = users_db.get_param(user_ID, 'language')
    date = users_db.get_param(user_ID, 'last_answer')
    if datetime.datetime.now() > date + datetime.timedelta(days=1):
        users_db.set_settings(user_ID, {'count': 7})
    count = users_db.get_param(user_ID, 'count')
    if count > 0:
        markup = generate_markup(types.ReplyKeyboardMarkup(resize_keyboard=True), config.answer, language)
        flag = True
        while flag:
            learn_words = shelve.open("learn_words", flag='c')
            if len(learn_words[str(user_ID)]) > 0:
                value = random.randrange(len(learn_words[str(user_ID)]))
                print(value)
                new_word = learn_words[str(user_ID)][value]
                print(new_word.word)
                if new_word.word not in users_db.get_param(user_ID, 'words') and new_word.word not in users_db.get_param(user_ID, 'vocabulary'):
                    if language == "English":
                        translate = new_word.translate_eng
                        example = new_word.example_eng
                    elif language == "Persian":
                        translate = new_word.translate_pers
                        example = new_word.example_pers

                    temp = learn_words[str(user_ID)]
                    temp.pop(value)
                    learn_words[str(user_ID)] = temp
                    print("to")
                    learn_words.close()
                    print('close')
                    flag = False
            else:
                break
        print(flag)
        if flag is True:
            bot.send_message(user_ID, "choose next level")
            menu(user_ID)
        else:
            msg = bot.send_message(user_ID, "*{word}* - {translate_eng}\n"
                                            "{transcription}\n"
                                            "- _{example}_\n"
                                            "- _{example_eng}_".format(word=new_word.word, translate_eng=translate,
                                                                       transcription=new_word.transcription,
                                                                       example=new_word.example,
                                                                       example_eng=example), reply_markup=markup,
                                   parse_mode="Markdown")
            if len(new_word.audio) > 3:
                bot.send_voice(user_ID, new_word.audio)
            else:
                bot.send_message(user_ID, "not audio")
            bot.register_next_step_handler(msg, func, new_word)
    else:
        if users_db.get_param(user_ID, 'account') == 'normal':
            buy_premium_account(user_ID)
        else:
            users_db.set_settings(user_ID, {'count': 7})
            menu(user_ID)


def func(message, new_word):
    user_ID = message.from_user.id
    if message.text == "\U0001F4DDLearn":
        users_db.push_word(user_ID, {'words': new_word.word})
        users_db.update_count(user_ID, {'count': -1})
        users_db.update_count(user_ID, {'today': +1})
    else:
        users_db.push_word(user_ID, {'vocabulary': new_word.word})
    if message.text == "\U0001F4DDLearn":
        date = users_db.get_param(user_ID, 'last_answer')
        if datetime.datetime.now() > date + datetime.timedelta(days=1):
            users_db.set_settings(user_ID, {'today': 1})
    users_db.set_settings(user_ID, {'last_answer': datetime.datetime.utcnow()})
    learning_words(message.from_user.id)


def buy_premium_account(user_ID):
    language = users_db.get_param(user_ID, 'language')
    markup = generate_markup(types.ReplyKeyboardMarkup(resize_keyboard=True), config.buy_premium_account, language)
    msg = bot.send_message(user_ID, config.buy_premium_account[language]['text'], reply_markup=markup)
    bot.register_next_step_handler(msg, buy_route)


def buy_route(message):
    if message.text == "< Back":
        menu(message.from_user.id)
    else:
        not_yet(message.from_user.id)


def not_yet(user_ID):
    bot.send_message(user_ID, "function not ready")
    menu(user_ID)


def statistic(user_ID):
    language = users_db.get_param(user_ID, 'language')
    learn_words = shelve.open("learn_words", flag='c')
    vocabulary = len(users_db.get_param(user_ID, 'vocabulary'))
    date = users_db.get_param(user_ID, 'last_answer')
    if datetime.datetime.toordinal(date) < datetime.datetime.toordinal(datetime.datetime.utcnow()):
        users_db.set_settings(user_ID, {'today': 0})
    today = int(users_db.get_param(user_ID, 'today'))
    all_words = len(learn_words[str(user_ID)])
    learn_words.close()
    level = int(users_db.get_param(user_ID, 'level'))
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="Share with friends", switch_inline_query='https://telegram.me/RussianLanguageBot?start={user_ID}'.format(user_ID=user_ID)))
    bot.send_message(user_ID, "\U00002705{voc_text}: +{vocabulary}\n"
                              "\U0001F4C6{today_text}: +{today}\n"
                              "\U0001F525{level_text}: {level}\n"
                              "\U0001F4C8{goal_text}: {all_words}\n"
                              "\n"
                              "\U00002795 Share Russian Language Bot with your friends\n"
                              "and get *Premium* access *for free*".format(voc_text=config.statistic_text[language][0],
                                                                           vocabulary=vocabulary,
                                                                           today_text=config.statistic_text[language][1],
                                                                           today=today,
                                                                           level_text=config.statistic_text[language][2],
                                                                           level=config.levels[language]['elems'][level],
                                                                           goal_text=config.statistic_text[language][3],
                                                                           all_words=all_words), reply_markup=markup,
                     parse_mode="Markdown")

    time.sleep(2)
    menu(user_ID)


def commands(user_ID):
    bot.send_message(user_ID, "Send command:\n"
                              "/start - Return to menu\n"
                              "/language - To change language\n"
                              "/download - Download list words\n"
                              "/level - To change level")
    pass


if __name__ == '__main__':
    try:
        threading.Thread(target=bot.polling).start()
    except Exception as err:
        print('error')
