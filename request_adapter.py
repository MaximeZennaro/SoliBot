""" We created our own adapter for the messages similar to a request message """

from chatterbot.logic import LogicAdapter
import ast
import sqlite3
from clean_process import cate_value_norm, cate_norm, normalize, find_key, return_NER, cate_data
import config
from config import city_kept, cate_kept, sent_ask_lieu, cities, dico_synonymes, arrondissement, arrondissements_paris, days, days_french, results, cate_serv, city
from datetime import datetime


def get_info(statement):
    """
    This function collects the diffrents key arguments that we can have in the message (the type of service and the location)
    of course if we can process the message with this Logic Request Adapter
    :input: Statement, dict
        We take as arguments the statement (which corresponds to the current user message) and the dictionary (cate_norm) 
        with the name of categories that have been normalized
    :output: list
        A list key_args in which we store 1 or 2 pieces of information (services and/or location/or district) or the answer to the question :
        'Do you want more results ?'
    """
    key_arg = []
    input_statement = statement.text
    statement_norm = normalize(input_statement)

    if config.more_choices:
        tokens = []
        for token in statement_norm:
            tokens.append((token, 'None'))
        return tokens

    syno_temp = {}
    for key in dico_synonymes:
        for x in dico_synonymes[key]:
            # we are looking for the words which the root is closed to one of the normalized category names
            for token_norm in normalize(x):
                if token_norm in statement_norm:
                    if key not in syno_temp:
                        syno_temp[key] = 1
                    else:
                        syno_temp[key] += 1
    relevant_key = None
    maxi = 0
    for key in syno_temp:
        if syno_temp[key] > maxi:
            relevant_key = key
            maxi = syno_temp[key]
    syno = []
    for key in syno_temp:
        if syno_temp[key] == maxi:
            syno.append(key)
    if len(syno) == 1:
        key_arg.append((syno[0], 'cate'))
    if len(syno) > 1:
        syno.sort()
        key_arg.append(syno)

    for city in cities:
        # if one word is the location
        if len(normalize(city)) != 0:
            if normalize(city)[0] in statement_norm:
                key_arg.append((city, 'LOC'))
                break
    for arrondissement_number in arrondissements_paris:
        for arr in arrondissements_paris[arrondissement_number]:
            if arr in statement_norm:
                key_arg.append((arrondissement_number, 'ARR'))
                break
    print(key_arg)
    return key_arg


def current_time_in_seconds():
    """ This function converts the current time into a number which corresponds to the current time in seconds
    :input: None
        We take no arguments
    :output: int
        The converted current time in seconds
    """
    current_time = datetime.now().time().isoformat(timespec='auto')
    list_h_m_s = current_time.split(':')
    hours = int(list_h_m_s[0])
    minutes = int(list_h_m_s[1])
    seconds = int(float(list_h_m_s[-1]))
    return 3600*hours + 60*minutes + seconds


hour, minute = 0, 0


def seconds_to_time(nb_seconds):
    """ This function converts a number to a time with the conventional format H:M:S
    :input: int
        The number of seconds
    :output: tuple
        A tuple with the number of hours, minutes and seconds
    """
    hour = nb_seconds / 3600
    nb_seconds %= 3600
    minute = nb_seconds/60
    nb_seconds %= 60
    return (hour, minute, nb_seconds)


def is_opening(dic_opening_hours):
    """ This function determines if an organization found as a request result is opened or not.
    If it is closed, we explain why by giving as additional inofrmation, the hour when it will open and the day.
    :input: dic
        the dictionary which contain the opening hours
    :output: str
        A sentence with the opening information.
    """
    # if there is some pieces of information about the hours
    try:
        dico_hours = ast.literal_eval(dic_opening_hours)
        current_time = current_time_in_seconds()
        # we figure out the day with its ID (ID_monday=0, ID_tuesday=1...)
        day_ID = datetime.today().weekday()

        # if it is the Week-end
        if (day_ID == 5 or day_ID == 6):
            phr_end = "\n Cet établissement est fermé. Il ouvrira lundi."
            return phr_end

        else:
            # NB : 'evening' is for the morning
            day = days[day_ID]
            plages_horaires = [dico_hours[day]['evening_start'], dico_hours[day]['evening_end'],
                               dico_hours[day]['afternoon_start'], dico_hours[day]['afternoon_end']]

        if (plages_horaires[1], plages_horaires[2] == -1, -1) and plages_horaires[0] < current_time < plages_horaires[3]:
            phr_end = "\n Cet établissement est actuellement ouvert et toute la journée."
        if ((plages_horaires[0], plages_horaires[1] != -1, -1) and plages_horaires[0] < current_time < plages_horaires[1]) or ((plages_horaires[2], plages_horaires[3] != -1, -1) and plages_horaires[2] < current_time < plages_horaires[3]):
            phr_end = "\n Cet établissement est actuellement ouvert."
        else:
            horaire = None
            # opening soon
            if current_time < plages_horaires[0]:
                moment = "aujourd'hui"
                horaire = seconds_to_time(plages_horaires[0])
            # lunch break
            if plages_horaires[1] < current_time < plages_horaires[2]:
                moment = "cet après-midi"
                horaire = seconds_to_time(plages_horaires[2])
            # if it is closed on the afetrnoon or it is too late and it is closed because of the end of the day
            if (plages_horaires[1] < current_time and (plages_horaires[2], plages_horaires[3] == -1, -1)) or (current_time > plages_horaires[3] and plages_horaires[3] != -1):
                if day_ID == 4:
                    moment = "lundi"
                    day_next = days[0]
                else:
                    day_ID_next = day_ID + 1
                    day_next = days[day_ID_next]
                    day_next_french = days_french[day_ID_next]
                    moment = "demain {}".format(day_next_french)
                if plages_horaires[0] == -1:
                    horaire = None
                else:
                    horaire = seconds_to_time(
                        dico_hours[day_next]['evening_start'])

            if horaire != None:
                heure, minute = int(horaire[0]), int(horaire[1])

                if 0 <= minute <= 9:
                    phr_end = "\n Cet établissement est actuellement fermé. Il ouvrira à {}h0{} {}.".format(
                        heure, minute, moment)
                else:
                    phr_end = "\n Cet établissement est actuellement fermé. Il ouvrira à {}h{} {}.".format(
                        heure, minute, moment)
            else:
                phr_end = "\n Cet établissement est fermé."
    # if there is no information about the hours
    except:
        phr_end = ""

    return phr_end


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
    selected_statement = "D'accord. Pouvez-me donner plus d'informations comme le type de service que vous cherchez et dans quel lieu ?"

    # global variables in order to store the information of the city and the type of services from the previous message and if necessary the arrondissement number
    global city_kept
    global cate_kept
    global cate_serv
    global city
    global arrondissement
    global results
    arr = ""

    if len(args) == 0:
        return selected_statement

    # if only one argument is given, we ask the user for the missing information
    if len(args) == 1:

        # if the synonyme correspond to several categories or sub-categories (for example : 'manger' matches with 'alimentation', 'distribution alimentaire' ...)
        if len(args[0]) > 1 and args[0][1] not in ['cate', 'LOC', 'ARR', 'None']:

            options = "Pouvez vous me dire précisément si vous cherchez un service du type "

            for i in range(len(args[0])):
                option = args[0][i]
                if i == len(args[0])-1:
                    options += "'{}' ?".format(dico_synonymes[option][-1])
                else:
                    options += "'{}' ou ".format(dico_synonymes[option][-1])

            selected_statement = "J'ai compris que vous cherchiez une structure pouvant correspondre à " + \
                dico_synonymes[args[0][0]][-1] + ". " + options
            return selected_statement

        # we ask for the city
        if args[0][1] == 'cate':
            cate_kept = args[0][0]
            selected_statement = random.choice(sent_ask_lieu)
        if args[0][1] == 'LOC':
            city_kept = args[0][0]
            selected_statement = random.choice(
                ["D'accord. J'ai compris que vous étiez sur {}. Quel type de service ou d'infrastructure recherchez-vous ?".format(args[0][0]), "Bien noté. J'ai compris que vous étiez sur {}. Et que cherchez-vous précisément ? Un logement, des soins ?".format(args[0][0])])
        if args[0][1] == 'ARR':
            arrondissement = args[0][0]

    # if we have all the information
    if config.more_choices or (len(args) == 2) or (cate_kept != None and city_kept != None) or (cate_kept != None and city_kept != None and arrondissement != None):

        if config.more_choices:
            config.TTL = 1
            if any(token[0] in ['oui', 'daccord', 'dacor', 'ok', 'bien', 'oki', 'okay'] for token in args):

                more_results = []
                if len(results) > 0:
                    while len(results) > 0:
                        res = random.choice(results)
                        more_results.append(res)
                        results.remove(res)
                        if len(more_results) == 2:
                            break

                    phr_begin = "Voici {} autre(s) résultat(s) correspondant(s) à votre recherche pour la catégorie '{}' à '{}'. \n".format(len(more_results),
                                                                                                                                            dico_synonymes[cate_serv][-1], city)
                    selected_statement = phr_begin

                    for i in range(len(more_results)):
                        phr_end_i = is_opening(more_results[i][2])
                        selected_statement = selected_statement + " \n ---Nom--- : {}. \n  ---Adresse--- : {}. \n ".format(
                            more_results[i][0], more_results[i][1]) + phr_end_i + "-"*10
            else:
                selected_statement = "D'accord pas de soucis. Je reste à votre service si besoin !"

            cate_serv = None
            city = None
            return selected_statement
        else:

            if len(args) == 2:
                if args[0][1] == 'cate':
                    cate_kept = args[0][0]
                    city_kept = args[1][0]
                if args[0][1] == 'LOC':
                    cate_kept = args[1][0]
                    city_kept = args[0][0]

            conn = sqlite3.connect(path_database)
            cursor = conn.cursor()

            city = city_kept
            cate_serv = cate_kept
            #print("cate : {}".format(cate_serv), "ville: {}".format(city))

            if city == "Paris":
                if arrondissement != None:
                    if len(str(arrondissement)) == 1:
                        arr = "7500{}".format(arrondissement)
                    else:
                        arr = "750{}".format(arrondissement)
                    cursor.execute(
                        "SELECT name, address, hours,categorie FROM informations WHERE ville=? AND codePostal=?", (city, arr))
                    result_temp = cursor.fetchall()
                    city_kept = None
                    cate_kept = None
                    arrondissement = None
                else:
                    selected_statement = "Bien noté j'ai compris que vous étiez sur Paris. Pouvez-vous me donner votre arrondissement ou code postal ?"
                    return selected_statement
            else:
                cursor.execute(
                    "SELECT name, address, hours, categorie FROM informations WHERE ville=? ", (city,))
                result_temp = cursor.fetchall()
                city_kept = None
                cate_kept = None

            results = []
            for res in result_temp:
                if int(cate_serv) in ast.literal_eval(res[-1]) or str(cate_serv) in ast.literal_eval(res[-1]):
                    results.append(res[:3])

            if len(results) == 0:
                selected_statement = "Désolé je n'ai pas trouvé de résultats à {1} {2} pour {0}. Pour plus d'informations je vous invite à contacter directement l'équipe Soliguide. ".format(dico_synonymes[cate_serv][-1],
                                                                                                                                                                                              city, arr)
                return selected_statement

            else:
                selected_res = random.choice(results)
                results.remove(selected_res)
                # print(selected_res)
                # print(results)

                phr_end = is_opening(selected_res[2])

                if len(results) > 0:
                    config.more_choices = True
                    config.TTL = 2
                    phr_end = is_opening(
                        selected_res[2]) + " Souhaitez-vous afficher d'autres résultats supplémentaires pour la recherche de {} à {} ?".format(dico_synonymes[cate_serv][-1], city)

                phr_begin = "Voici un résultat correspondant à votre recherche pour la catégorie '{}' à '{}'. \n".format(
                    dico_synonymes[cate_serv][-1], city)

                selected_statement = phr_begin + \
                    " \n ---Nom--- : {}. \n  ---Adresse--- : {}. \n ".format(
                        selected_res[0], selected_res[1]) + phr_end

            conn.close()

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
        # more_choices variable reset
        if config.more_choices and config.TTL == 1:
            config.more_choices = False
        # if the user asks for more results
        if config.more_choices:
            return True
        # if the user gives new information about the modified hours or the referencement
        if config.statut_ref or config.statut_horaire:
            return False
        input_statement = statement.text
        statement_norm = normalize(input_statement)
        # for the following conditions, we asess if we can process the message or not with the request_adapter (if the message is similar to a database request)
        if (config.statut_ref or config.statut_horaire) and any(normalize(city)[0] in statement_norm for city in cities if len(normalize(city)) != 0):
            return False
        for key in dico_synonymes:
            if any(normalize(x)[0] in statement_norm for x in dico_synonymes[key]):
                return True
        if any(normalize(city)[0] in statement_norm for city in cities if len(normalize(city)) != 0):
            return True
        for arrondissement_number in arrondissements_paris:
            if any(arr in statement_norm for arr in arrondissements_paris[arrondissement_number]):
                return True

        return False

    def process(self, input_statement, additional_response_selection_parameters=None):

        from chatterbot.conversation import Statement

        args = get_info(input_statement)
        return_msg = request_process(args, self.database)
        reponse_statement = Statement(
            text=return_msg)

        return reponse_statement
