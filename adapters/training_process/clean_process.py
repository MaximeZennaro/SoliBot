""" In this file, we gathered all the functions that get the data, process them, clean them in order to create the training file for our Chatbot"""

import ast
import string
import spacy
from stop_words import get_stop_words
import math
import nltk
from nltk.corpus import stopwords
from nltk import word_tokenize, stem
from nltk.tokenize import sent_tokenize

# French stemmer used for stemming
stemmer = nltk.stem.snowball.FrenchStemmer()

# excluded punctuation
remove_ponctuation_map = dict((ord(char), None) for char in string.punctuation)

# spacy French corpus
nlp = spacy.load("fr_core_news_sm")

path = "adapters/training_data/"

# list of the different categories of services provided by Soliguide
cate_data = ast.literal_eval(open(
    path+'categories.txt', encoding='utf8').read())

# Soliguide DataBase
db_file = "DB_Soliguide.db"


def stem_tokens(text: str):
    """
    This function tokenize the text and stem the different tokens by removing the stop words
    We obtain the canonic form of each word
    :input: str
        The text that we have to stem
    :output: list
        It returns a list of stemmed tokens
    """
    return [stemmer.stem(token) for token in text]


def normalize(text: str):
    """
    This function normalize the text by removing the punctuation characters, the stop words and finding the common root of the word (canonic form).
    We can also remove upper case letters.
    First we have to use the fonction stem_tokens and then apply the normalization.
    Examples : inputs = 'je donne','donnera', 'ils donnent' -->  output 'don'

    :input: str
        The text that we have to normalize
    :output: list
        It returns a list of normalized tokens
    """
    return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_ponctuation_map)))


def return_NER(sentence: str):
    """
    This function tokenize the sentence given as input.
    It returns a list of tuples for very relevant word with the word and its label
    Example : input = 'Bouygues a son siège sur Paris' -->  output = [('Bouygues','ORG'),('Paris','LOC')]
    :input: str
        The sentence that we have to labelize
    :output: list of tuples
        It returns a list of labelized tokens
    """
    # Tokeniser la phrase
    sentence_up = str(sentence).upper()  # .text.upper()
    doc = nlp(sentence_up)
    # Retourner le texte et le label pour chaque entité
    return [(X.text, X.label_) for X in doc.ents]


def find_key(v: str, dic: dict):
    """
    This function find the key associated to a value on a dictionary.
    It returns the key which corresponds to the value given as input
    :input: str, dict
        The value "v" that we have to find the key and the dictionary "dic" where we have to apply this function.
    :output: str
        It returns the key.
    """
    for k, val in dic.items():
        if v == val:
            return k


# the names of the categories are normalized in a new dictionary with the same key (number)
cate_norm = {}
cate_value_norm = []
for key in cate_data:
    value = normalize(cate_data[key])[0]
    cate_norm[key] = value
    cate_value_norm.append(value)

# we had some root words which will be very useful because are parts of the common language
cate_value_norm = cate_value_norm + \
    ['emploi', 'dépist', 'soign', 'épici', 'médecin', 'mang',
        'docteur', 'avocat', 'travail', 'travaill', 'assist', 'social']

# the list of sentences that we use for asking where the user is searching
sent_ask_lieu = [
    "Dans quel lieu cherchez-vous ?",
    "Pouvez-vous me dire où êtes-vous situé ?",
    "Très bien. Ou êtes-vous situé?",
    "D'accord et pouvez-vous me dire où vous êtes situé ?",
    "Bonjour, d'accord et où êtes-vous situé ?",
    "Bonjour, je vais me renseigner. Pouvez-vous me dire où vous êtes situé ?"]

# global variable city_kept in order to store the information of the city
# global variable cate_kept in order to store the information of the type of services
city_kept = None
cate_kept = None

# Scrapped conversations and processing :


def process_data_WS(filename):
    """
    This function permits to sort and clean the different sentences scrapped from the conversations. 
    :input: file
        The file that we have to process the data (txt file which contains the web-scrapped conversations)
    :output: list
        It generates at the end a list which contains the user sentences for each odd line number and the response sentences for each even line number
    """
    # file opening, reading and closing
    file = open(filename, 'r', encoding="utf8")
    fileLines = file.readlines()
    # this list_bin is used for recording the last line that we process in the file
    fileLines_bin = [fileLines[0][len("USER_ASK: "):]]
    file.close()

    # we initialize a list which will contain the sentences given by the user and the associated responses
    L_Q_R = [fileLines[0][len("USER_ASK: "):]]
    N = len(fileLines)

    i = 0
    while i < N:

        try:  # if the line of the file is different from an empty line or a line which starts with 'Conversation'
            line = fileLines[i].strip()
            c = 0
            if line.startswith("USER_ASK:"):
                # in the case of the user sends several messages for the same questions or for adding more information
                if fileLines_bin[-1].strip().startswith("USER_ASK:"):
                    L_Q_R[-1] = L_Q_R[-1] + " " + \
                        line[len("USER_ASK: "):]

                else:
                    L_Q_R.append(line[len("USER_ASK: "):])
                c = 1

            if line.startswith("RESPONSE:"):
                # in the case of the software sends a default response
                if line.startswith("RESPONSE: Bonsoir !") and fileLines_bin[-1].startswith("RESPONSE:"):
                    L_Q_R.append("Bonsoir ! Malheureusement nous ne pouvons pas vous répondre pour le moment mais nous le ferons dès que possible. Vous pouvez laisser votre mail, écrire votre question, et nous reviendrons vers vous aussi vite que possible. En cas d'urgence, vous pouvez appeler le 115")
                    del(fileLines[i+1:i+5])
                else:
                    # in the case of the volunteer sends several messages for the same questions or for adding more information
                    if fileLines_bin[-1].startswith("RESPONSE:"):
                        L_Q_R[-1] = L_Q_R[-1] + " " +\
                            line[len("RESPONSE: "):]

                    else:
                        L_Q_R.append(line[len("RESPONSE: "):])
                c = 1
            if c == 1:
                # we store the last sentence in order to know if it was a user request or a volunteer reponse
                fileLines_bin.append(line)

        except:
            None
        i += 1

    return L_Q_R[1:]


def write_data_training(filename, List_training: list):
    """
    This function permits to reset and rewrite the training file if we update the file. 
    :input: file, list
        The file that we have to write the cleaned data (txt file)
    :output: file
        It creates a txt file which contains the cleaned sentences processed with the previous function 'process_data_WS'
    """
    f = open(filename, 'r+')
    f.truncate(0)
    file = open(filename, 'w', encoding="utf8")
    for sent in List_training:
        file.write(sent+'\n')
    file.close()


if __name__ == '__main__':

    # print(process_data_WS('data_output.txt'))
    # write_data_training('training_data/data_clean.txt',
    #                     process_data_WS('data_output.txt'))
    # print(cate_value_norm)
    pass
