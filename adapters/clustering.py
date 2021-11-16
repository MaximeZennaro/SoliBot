"""In this file, we use the clustering method for classifying our data """

from stop_words import get_stop_words
from sklearn.feature_extraction.text import TfidfVectorizer
from training_process.clean_process import process_data_WS, stem_tokens, normalize
import math
import nltk
from nltk.corpus import stopwords
from nltk import word_tokenize, stem

from nltk.tokenize import sent_tokenize
import numpy as np
import pandas as pd
import json

import nltk
import string
# nltk.download('punkt') # to download if not in your machine

path = "adapters/training_data/"

stemmer = nltk.stem.porter.PorterStemmer()
remove_ponctuation_map = dict((ord(char), None) for char in string.punctuation)
stop_words = get_stop_words('fr')+['alor', 'aur', 'aurion', 'auron', 'auss', 'autr', 'avi', 'avion', 'avon', 'ayon', 'cec', 'cel', 'chaqu', 'comm', 'dan', 'dedan', 'dehor', 'devr', 'devrion', 'devron', 'droit', 'e', 'encor', 'euss', 'eussion', 'eûm', 'fair',
                                   'forc', 'fuss', 'fussion', 'fûm', 'hor', 'just', 'mainten', 'moin', 'mêm', 'nomm', 'notr', 'parc', 'parol', 'person', 'san', 'ser', 'serion', 'seron', 'seul', 'somm', 'soyon', 'tand', 'tel', 'tres', 'votr', 'éti', 'étion', 'ête']

# Definition of the filters and stop words
french_stopwords = list(set(stopwords.words('french')))
symb = ["[", ".", "!", "?", "]", "+", ",", "(", ";", ")"]


def cosine_sim(text1: str, text2: str):
    """
    This function calculates the cosine between 2 sentences. 
    First we vectorize our sentences and then we calculate the dot product. We deduce at the end the cosine
    If the cosine is closed to 1, it means that the sentences are closed in terms of meaning.
    :input: str, str
        Both sentences that we want to determine the cosine
    :output: float
        It returns the cosine between the 2 sentences
    """
    vectorizer = TfidfVectorizer(
        tokenizer=normalize, stop_words=french_stopwords, ngram_range=(1, 1))
    tfidf = vectorizer.fit_transform([text1, text2])
    return ((tfidf*tfidf.T).A)[0, 1]


def clean_data_WS(filename):

    L = []
    # ouverture, lecture et fermeture du fichier filename
    file = open(filename, 'r', encoding="utf8")
    fileLines = file.readlines()
    file.close()
    dic = {}
    dic['USER_ASK'] = []
    dic['RESPONSE'] = []

    for i in range(1, len(fileLines)):

        line = fileLines[i].strip()
        if line != '\n':
            if line.startswith("Conversation"):
                L.append(dic)
                dic = {}
                dic['USER_ASK'] = []
                dic['RESPONSE'] = []
            else:
                if line.startswith("USER_ASK:"):
                    dic['USER_ASK'].append(line[len("USER_ASK: "):])

                if line.startswith("RESPONSE:"):
                    dic['RESPONSE'].append(line[len("RESPONSE: "):])

                # cas ou on a une pharse issue d'un retour à la ligne et ne commençant pas par un des 3 cas ci-dessus:
                else:
                    if fileLines[i-1] in dic['USER_ASK']:
                        dic['USER_ASK'].append(line)
                    if fileLines[i-1] in dic['RESPONSE']:
                        dic['RESPONSE'].append(line)

    return pd.DataFrame.from_dict(L, orient='columns')


# these two dictionaries contain reference sentences that will be used to compare to the sentences of the corpus in order to find the best match intent
dico_intentions_ask = json.loads(
    open(path + "intentions_ask.json", encoding='utf8').read())
dico_intentions_resp = json.loads(
    open(path + "intentions_resp.json",  encoding='utf8').read())


def cluster(corpus: str):
    """
    This function permits us to sort the sentences by intents with the clustering method. We want a dictionary structure like this example :
    Example :
    {
    "intents": [
        {
            "tag": "Bienvenue",
            "patterns": [
                "salut quelqu'un peut m'aider ?",
                "salut",
                "Bonjour, j'ai besoin de votre aide",
                "bonjour"

            ],
            "responses": [
                "Bonjour que cherchez vous ?",
                "Bonjour,"
            ]
             }, ....... }

    The tag key corresponds to the intent label. Then, the patterns correspond to the user messages and the responses correspond to the volunteer messages.

    :input: str
        The corpus text whihc contains all the messages
    :output: dic
        A dictionary similar to our example with the global key 'intents' and the value a list of intent dictionaries with 3 keys : 'tag', 'patterns', 'responses'
    """
    dico_ask = dico_intentions_ask
    dico_resp = dico_intentions_resp

    # we initialize the dictionary given as output
    dic_cluster = {}
    dic_cluster["intents"] = []
    L_user_ask = []
    L_resp = []
    nb_conv = len(corpus)

    # we collect all the messages for each member
    for c in range(nb_conv):
        list_ask = corpus.iloc[c]['USER_ASK']
        list_resp = corpus.iloc[c]['RESPONSE']
        L_user_ask = L_user_ask + list_ask
        L_resp = L_resp + list_resp

    # we sort first the user messages according the different intents
    for i in range(len(L_user_ask)):
        s1 = L_user_ask[i]
        maxi = 0
        key = None

        # we want to find the maximum score and the best match intent
        for k in dico_intentions_ask:

            for sent_k in dico_intentions_ask[k]:
                s2 = sent_k
                p = cosine_sim(s1, s2)
                if p > maxi:
                    maxi = p
                    key = k
        # Similarity threshold : 50%
        if key != None and maxi >= 0.5:
            dico_ask[key].append(s1)
        # else:
        #     dico_ask["Exceptions"].append(s1)

    # we sort first the response messages according the different intents
    for i in range(len(L_resp)):
        s1 = L_resp[i]
        if not(s1.startswith("USER_ASK:")):
            maxi = 0
            key = None
            for k in dico_intentions_resp:

                for sent_k in dico_intentions_resp[k]:
                    s2 = sent_k
                    p = cosine_sim(s1, s2)
            # Similarity threshold : 50%
            if key != None and maxi >= 0.5:
                dico_resp[key].append(s1)

    # we fulfill the clustering dictionary
    for k in dico_ask:
        dic = {}
        dic["tag"] = k
        dic["patterns"] = list(set(dico_ask[k]))
        dic["responses"] = list(set(dico_resp[k]))
        dic_cluster["intents"].append(dic)

    return dic_cluster


if __name__ == '__main__':

    # dico_int = cluster(clean_data_WS('training_data/max1.txt'))
    # tf = open("training_data/max1.json", "w", encoding='utf8')
    # json.dump(dico_int, tf)
    # tf.close()
    print(normalize('je suis'))
    pass
