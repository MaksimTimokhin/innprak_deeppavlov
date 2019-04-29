import telebot
from deeppavlov.contrib.skills.similarity_matching_skill import SimilarityMatchingSkill
from telebot import apihelper
import time

apihelper.proxy = {'https':'socks5://telegram:S0cks@socks.serzhenko.me:1080'}
bot = telebot.TeleBot('secret-token')


faq = SimilarityMatchingSkill(
  data_path ='dodo.csv',
  x_col_name = 'Question',
  y_col_name = 'Answer',
  config_type = 'tfidf_logreg_autofaq',
  edit_dict = {},
  train = True
)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    bot.send_message(message.from_user.id, 'Ответ: {}, Уверенность: {}'.format(faq([message.text], [], [])[0][0][0], faq([message.text], [], [])[1][0]))

bot.polling(none_stop=True, interval=0)
    
