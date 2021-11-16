""" In this file we store all the global varaibles used for our chatbot """

import pandas as pd
import sqlite3
import ast
from clean_process import normalize

path = "training_data/"

# all bags of words with category synonymes


def synonymes_categories(filename=path+'synonymes_cate.csv'):
    """ This function creates a dictionary. The keys are the different categories of services,
    and the values the synonymes closed to the meaning of the category.
    For instance : {... , 'généraliste' : ['docteur', 'médecin', 'médecine', 'soins' ...], ...}
    :input: str
        the csv file path where we store the vocabulary
    :output: dict
        It returns dictionary which keys correspond to the category IDs (is an intenger)
        and the value is the relevant vocabulary associated to these categories
    """
    df = pd.read_csv(filename, sep=";")
    index_with_nan = df.index[df.iloc[:, 1].isnull()]
    df.drop(index_with_nan, 0, inplace=True)
    dic_synonymes = {}

    for i in range(len(df)):
        key_category = int(df.iloc[i]["ID CATEGORIE"])
        dic_synonymes[key_category] = df.iloc[i]["SYNONYMES"].split(
            ",")+[df.iloc[i]["URL ASSOCIÉ"]]

    return dic_synonymes


dico_synonymes = synonymes_categories()

# all cities


def select_city(database=path + 'DB_Soliguide.db'):
    """ This function creates a list with the different cities which are in the Soliguide DataBase
    :input: str,
        the databse file path where we store the cities (and all the informations from Soliguide)
    :output: list
        a list with the cities
    """
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT ville FROM informations")
    list_cities = []
    res = cursor.fetchall()
    for ele in res:
        list_cities.append(ele[0])
    return list_cities


cities = select_city()


# global variables for the request adapter (for mainly the request_process function) :

sent_ask_lieu = [
    "Dans quel lieu cherchez-vous ?",
    "Pouvez-vous me dire où êtes-vous situé ?",
    "Très bien. Ou êtes-vous situé?",
    "D'accord et pouvez-vous me dire où vous êtes situé ?",
    "D'accord et où êtes-vous situé ?",
    "Je vais me renseigner. Pouvez-vous me dire où vous êtes situé ?"]

city_kept = None
cate_kept = None
cate_serv = None
city = None
arrondissement = None
more_choices = False
TTL = 0
results = []


def arrondissements(filename=path+"arrondissements.txt"):
    """ This function creates a dictionary for the diffrent Paris districts
    :input: str,
        the txt file path where we store the districts
    :output: dic
        a dictionary which keys are the district numbers and values are some equivalent terms.
        For example : {..., '16' : ['seizième','16eme','75016',..],... }
    """
    file = open(filename, 'r', encoding="utf8")
    lines = file.readlines()
    dico_arrond = {}
    for i in range(len(lines)):
        dico_arrond[i+1] = []
        list_words = lines[i].strip().split(",")
        for word in list_words:
            dico_arrond[i+1].append(normalize(word)[0])
        dico_arrond[i+1] = set(dico_arrond[i+1])
    return dico_arrond


arrondissements_paris = arrondissements()

# weekdays list:
days = ['monday', 'tuesday', 'wednesday',
        'thursday', 'friday', 'saturday', 'sunday']
days_french = ['lundi', 'mardi', 'mercredi',
               'jeudi', 'vendredi', 'samedi', 'dimanche']

# global varibales for the specific adapter:
statut_horaire = False
statut_ref = False
TTL_h = 0
TTL_ref = 0
