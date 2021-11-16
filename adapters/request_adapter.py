""" We created our own adapter for the messages similar to a request message """

from chatterbot.logic import LogicAdapter
import ast
import sqlite3
from adapters.training import cities
from clean_process import cate_value_norm, cate_norm, normalize, find_key, return_NER, sent_ask_lieu, city_kept, cate_kept, cate_data


def frequent_request(category_name):
    """
    In this function we try to identify words from common language which match with some category names
    For instance : "médecin", "docteur" match with the category "Généraliste" and the key is '105'
    :input: str
        We try to associate the appropriate category to the word.
    :outout: a boolean or str
        We return the key which correspond to the category name or otherwise False 
    """
    key = False
    print(category_name)
    if category_name in ['emploi', 'job', 'travail', 'travaill']:
        key = "204"
    elif category_name in ['dépist']:
        key = "102"
    elif category_name in ['soign', 'médecin', 'docteur']:
        key = "105"
    elif category_name in ['mang', 'soif', 'faim']:
        key = "601"
    elif category_name in ['restaur']:
        key = "602"
    elif category_name in ['épici']:
        key = "604"
    elif category_name in ['avocat']:
        key = "402"
    elif category_name in ['assist', 'social']:
        key = "404"
    return key


def get_info(statement, dic: dict):
    """
    This function collects the diffrents key arguments that we can have in the message (the type of service and the location)
    of course if we can process the message with this Logic Request Adapter
    :input: Statement, dict
        We take as arguments the statement (which corresponds to the current user message) and the dictionary (cate_norm) 
        with the name of categories that have been normalized
    :output: list
        A list key_args in which we store 1 or 2 pieces of information (services and/or location)
    """
    key_arg = []
    input_statement = statement.text
    if len(input_statement.split()) == 1:
        input_statement = "sur " + input_statement
    statement_norm = normalize(input_statement)
    for x in cate_value_norm:
        # we are looking for the words which the root is closed to one of the normalized category names
        if x in statement_norm:
            key = frequent_request(x)
            if key != False:
                key_arg.append((key, 'cate'))
            else:
                key_arg.append((find_key(x, dic), 'cate'))
            break
    # for tup in return_NER(input_statement):
    for city in cities:
        # if one word has the 'LOC' label it means it is the location
        if normalize(city) in statement_norm:
            key_arg.append((city, 'LOC'))
            break
    return key_arg


def request_process(args: list, path_database: str):
    """
    According to the different pieces of information storing in the list coming from get_info, 
    we create the equivalent SQL request in order to return one result or not if there is no result due to the city.
    :input: list, str
        We take as arguments the list args with the key arguments (type of services and location) and the Soliguide database path 
    :output: str
        The response of the Chatbot for the initial request.
    """
    import random
    confidence = 1
    selected_statement = "D'accord. Pouvez-me donner plus d'informations comme le type de service que vous cherchez et dans quel lieu ?"

    # global variables in order to store the information of the city and the type of services from the previous message
    global city_kept
    global cate_kept

    if len(args) == 0:
        return selected_statement

    if city_kept != None:
        args.append((city_kept, 'LOC'))

    if cate_kept != None:
        args.append((cate_kept, 'cate'))
        args[0], args[1] = args[1], args[0]

    city_kept = None
    cate_kept = None

    # if we have all the information
    if len(args) == 2:
        conn = sqlite3.connect(path_database)
        cursor = conn.cursor()
        # we change the name of the city VILLE with Ville
        city = args[1][0][0] + args[1][0][1:].lower()
        cate_serv = args[0][0]
        print("cate : {}".format(cate_serv), "ville: {}".format(city))
        cursor.execute(
            "SELECT name, address, categorie FROM informations WHERE ville=? ", (city,))
        result_temp = cursor.fetchall()
        result = []
        for res in result_temp:
            if int(cate_serv) in ast.literal_eval(res[2]) or str(cate_serv) in ast.literal_eval(res[2]):
                result.append(res[:2])
        if len(result) == 0:
            selected_statement = "Désolé je n'ai pas trouvé de résultats à {}. Nous n'y sommes probablement pas encore implanté. Pour plus d'information je vous invite à contacter directement l'équipe Soliguide. ".format(
                city)
        else:
            selected_res = random.choice(result)
            print(result)
            print(selected_res)
            phr_begin = "Voici un résultat correspondant à votre recherche pour la catégorie '{}' à '{}' : \n".format(
                cate_data[cate_serv], city)
            phr_end = "\n Cet établissement est suceptible de vous aider."
            selected_statement = phr_begin +  \
                "Nom :" + selected_res[0] + ". \n" + \
                "Adresse :" + selected_res[1] + ". " + phr_end
        conn.close()

    # if only one argument is given, we ask the user for the missing information
    if len(args) == 1:
        # we ask for the city
        if args[0][1] == 'cate':
            cate_kept = args[0][0]
            selected_statement = random.choice(sent_ask_lieu)
        else:
            city_kept = args[0][0]
            selected_statement = random.choice(
                ["D'accord. J'ai compris que vous étiez sur {}. Quel type de service ou d'infrastructure recherchez-vous ?".format(args[0][0]), "Bien noté. J'ai compris que vous étiez sur {}. Et que cherchez-vous précisément ? Un logement, des soins ?".format(args[0][0])])
    return selected_statement


class RequestAdapter(LogicAdapter):
    """
    A logic adapter that returns a response based on the informations given by the asker 
    and on the fact that we can transform the question into a SQL request

    :database:
    we can specify the database in which we will fetch the information given by the user

    """

    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)

        self.database = kwargs.get('database')

    def can_process(self, statement):
        """
        Return true if the input statement contains
        one of the branch name of the DB, the location or one value of them.
        """
        input_statement = statement.text
        statement_norm = normalize(input_statement)
        print(statement_norm)
        if len(input_statement.split()) == 1:
            input_statement = "sur " + input_statement
        if any(x in statement_norm for x in cate_value_norm):
            return True
        if any(normalize(city) in statement_norm for city in cities):
            return True
        # if any('LOC' in tup[1] for tup in return_NER(input_statement) if tup[0] != 'Bonjour'):
        #     return True
        return False

    def process(self, input_statement, additional_response_selection_parameters=None):

        from chatterbot.conversation import Statement

        args = get_info(input_statement, cate_norm)
        reponse_statement = Statement(
            text=request_process(args, self.database))

        return reponse_statement
