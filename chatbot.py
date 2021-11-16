""" In this file we train our chatbot with the training data """

from chatterbot.trainers import ChatterBotCorpusTrainer
from chatterbot.trainers import ListTrainer
from chatterbot import ChatBot
import json

path = "training_data/"

chatbot = ChatBot(
    'Solibot',

    storage_adapter='chatterbot.storage.SQLStorageAdapter',
    logic_adapters=[
        {
            'import_path': 'specific_adapter.SpecificAdapter'
        },
        {
            'import_path': 'request_adapter.RequestAdapter',
            'database': path+"DB_Soliguide.db"
        },

        {
            'import_path': 'statement_adapter.StatementAdapter',
            'excluded_words': [],
            'default_response': "Je suis désolé mais je n'ai pas compris votre question ? Pouvez-vous reformuler ? Sinon Le 115 est un numéro d'urgence, gratuit et disponible 24 h/24, 7j/7. Le 115 gère toutes les places d'hébergement d'urgence en France. Il est souvent saturé, mais il faut l'appeler tous les jours.",
            'maximum_similarity_threshold': 0.60
        }
    ],
    database_uri='sqlite:///' + path + 'solibot.db',
)


# Training With Own Questions

# trainer = ListTrainer(chatbot)

# training_data_ques_ans = open(
#     path+'ques_ans.txt', encoding='utf8').read().splitlines()
# training_data_personal = open(
#     path+'personal_ques.txt', encoding='utf8').read().splitlines()

# training_data = training_data_personal + training_data_ques_ans

# trainer.train(training_data)

# # Training With Corpus

# trainer_corpus = ChatterBotCorpusTrainer(chatbot)

# trainer_corpus.train(
#     'chatterbot.corpus.french'
# )
