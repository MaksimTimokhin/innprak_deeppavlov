import telebot
import time
from typing import Tuple, Optional, List
from deeppavlov.configs import configs
from deeppavlov.core.common.file import read_json
from deeppavlov.core.commands.utils import expand_path
from deeppavlov.core.data.utils import update_dict_recursive
from deeppavlov import build_model, train_model
import requests

telebot.apihelper.proxy = {'https':'socks5://telegram:S0cks@socks.serzhenko.me:1080'}
bot = telebot.TeleBot('secret')

class SimilarityMatchingSkill():
    def __init__(self, data_path: Optional[str] = None, config_path: Optional[str] = None, config_type: Optional[str] = 'tfidf_autofaq',
                 x_col_name: Optional[str] = 'Question', y_col_name: Optional[str] = 'Answer',
                 save_load_path: Optional[str] = './similarity_matching',
                 edit_dict: Optional[dict] = None, train: Optional[bool] = True):

        if config_type not in configs.faq:
            raise ValueError("There is no config named '{0}'. Possible options are: {1}"
                             .format(config_type, ", ".join(configs.faq.keys())))
        
        if config_path is not None:
            model_config = read_json(config_path)
        else:
            model_config = read_json(configs.faq[config_type])

        if x_col_name is not None:
            model_config['dataset_reader']['x_col_name'] = x_col_name
        if y_col_name is not None:
            model_config['dataset_reader']['y_col_name'] = y_col_name
        
        model_config['metadata']['variables']['MODELS_PATH'] = save_load_path

        if data_path is not None:
            if expand_path(data_path).exists():
                if 'data_url' in model_config['dataset_reader']:
                    del model_config['dataset_reader']['data_url']
                model_config['dataset_reader']['data_path'] = data_path
            else:
                if 'data_path' in model_config['dataset_reader']:
                    del model_config['dataset_reader']['data_path']
                model_config['dataset_reader']['data_url'] = data_path

        if edit_dict is not None:
            update_dict_recursive(model_config, edit_dict)

        if train:
            self.model = train_model(model_config, download=True)
            #log.info('Your model was saved at: \'' + save_load_path + '\'')
        else:
            self.model = build_model(model_config, download=False)
            
    def __call__(self, utterances_batch: List[str], history_batch: List[List[str]],
                 states_batch: Optional[list] = None) -> Tuple[List[str], List[float]]:
        responses, confidences = self.model(utterances_batch)

        return responses, confidences

faq = SimilarityMatchingSkill(
  data_path ='dodo.csv',
  x_col_name = 'Question',
  y_col_name = 'Answer',
  config_path = 'config.json',
  edit_dict = {},
  train = True
)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    result = faq([message.text], [], [])
    '''
    answers = result[0][0]
    confidences = sorted(result[1][0])[-3:]
    answer = ""
    for i in range(len(answers)):
        answer += 'Ответ: {}, Уверенность: {}\n'.format(answers[i], confidences[-i])
    bot.send_message(message.from_user.id, answer)
    '''
    ipavlov_answer = result[0][0][0]
    ms_rsp = requests.post('https://demododoformax.azurewebsites.net/qnamaker/knowledgebases/74340b33-ccc4-45f6-8bee-6f85ee1daaf9/generateAnswer', headers = {'Authorization' : 'sectet', 'Content-type': 'application/json'}, data=str('{ "question" : "' + message.text +'"}').encode('utf-8')).json()
    reason8_rsp = requests.post('https://api.autofaq.ai/v1/query', data=str('{"service_id": 118758, "service_token": "secret", "query":"' + message.text + '"}').encode('utf-8')).json()
    answer = 'SimilarityMatchingSkill: {}\n Microsoft: {}\n Reason8: {}'.format(ipavlov_answer, ms_rsp['answers'][0]['answer'], reason8_rsp['results'][0]['answer'])
    bot.send_message(message.from_user.id, answer)
bot.polling(none_stop=True, interval=0)
    
