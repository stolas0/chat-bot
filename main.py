import os
import telebot
import bs4
import requests as req
import random
from selenium import webdriver
from flask import Flask, request


BOT_TOKEN = "000000000000000000000"
APP_URL = f'https://chatbot.herokuapp.com/{BOT_TOKEN}'
bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)



@bot.message_handler(commands="start")
def send_welcome(message):
    bot.send_message(message.chat.id, f"Я бот! Приятно познакомиться, {message.from_user.first_name}")


@bot.message_handler(commands="help")
def send_help_message(message):
    bot.send_message(message.chat.id, '''Вот, что я умею:
    /start - начало
    /help - помощь
    /keyboard - привет пока
    /inline - вопрос про собаку
    /age - вопрос про возраст
    /video - найти видео на Youtube
    /news - хорошие новости с портала Бумага''')


@bot.message_handler(commands="keyboard")
def send_message(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    buttonA = telebot.types.KeyboardButton('Привет')
    buttonB = telebot.types.KeyboardButton('Пока')
    keyboard.row(buttonA, buttonB)
    bot.send_message(message.chat.id, 'Что ты хочешь мне сказать?', reply_markup=keyboard)


@bot.message_handler(commands='inline')
def send_message(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton('Три', callback_data=3))
    markup.add(telebot.types.InlineKeyboardButton('Четыре', callback_data=4))
    markup.add(telebot.types.InlineKeyboardButton('Пять', callback_data=5))
    bot.send_message(message.chat.id, 'Сколько лап у собаки?', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle(call):
    bot.answer_callback_query(call.id)
    answer = ''
    if call.data == '3':
        answer = 'Попробуй еще раз.'
    elif call.data == '4':
        answer = 'Правильный ответ!'
    elif call.data == '5':
        answer = 'Где ты такую собаку видел(а)?'
    bot.send_message(call.message.chat.id, answer)
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)


@bot.message_handler(commands='age')
def start_handler(message):
    msg = bot.send_message(message.chat.id, 'Сколько вам лет?')
    bot.register_next_step_handler(msg, ask_age)


def ask_age(message):
    text = message.text
    if not text.isdigit():
        msg = bot.send_message(message.chat.id, 'Введите еще раз, возраст должен быть числом')
        bot.register_next_step_handler(msg, ask_age)
        return
    bot.send_message(message.chat.id, f'Я запомнил, что вам {text} лет')



@bot.message_handler(commands='news')
def search_news(message):
    news_hrefs = goParse()
    news_index = random.randint(0, len(news_hrefs) - 1)
    bot.send_message(message.chat.id, news_hrefs[news_index])


def goParse():
    news_link = 'https://paperpaper.ru/tag/horoshie-novosti/'
    links = []

    res = req.get(news_link)
    html = bs4.BeautifulSoup(res.text, 'lxml')
    links_a = html.find_all('a', class_="post__bottom-link js-track-text-widget-title")

    for a in links_a:
        links.append(a['href'])

    return links


@bot.message_handler(commands='video')
def search_video(message):
   msg = bot.send_message(message.chat.id, 'Какое видео найти?')
  bot.register_next_step_handler(msg, search)


def search(message):
   driver = webdriver.Opera(executable_path='operadriver.exe')
   bot.send_message(message.chat.id, 'Начинаю поиск')
   video_href = "https://www.youtube.com/results?search_query=" + message.text
   driver.get(video_href)
   videos = driver.find_elements_by_id("video-title")
   for i in range(len(videos)):
       if videos[i].get_attribute('href') is not None:
           bot.send_message(message.chat.id, videos[i].get_attribute('href'))
       if i == 3:
           break


@bot.message_handler(content_types="text")
def get_text_message(message):
    if message.text.lower() == "привет":
        markup = telebot.types.ReplyKeyboardRemove(selective=False)
        bot.send_message(message.chat.id, "Ну привет!", reply_markup=markup)
    elif message.text.lower() == "пока":
        markup = telebot.types.ReplyKeyboardRemove(selective=False)
        bot.send_message(message.chat.id, "Ну пока!", reply_markup=markup)
    else:
        bot.send_message(message.from_user.id, "Я не понимаю.")


@server.route('/' + BOT_TOKEN, methods=['POST'])
def get_message():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_messages([update])
    return '!', 200


@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL)
    return '!', 200


bot.polling()
