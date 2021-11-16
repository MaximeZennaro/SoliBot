
import sqlite3
import ast
import random
from training_process.clean_process import write_data_training

file_path = "adapters/training_data/"

training_file = ast.literal_eval(
    open(file_path + 'clustering_data.json', encoding='utf8').read())


db_file = "solibot.db"
database = file_path + db_file


def insert_data_to_DB(filename):
    """
    We insert into the database the different data sorted with the clustering method.
    Each question or user message is associated to the response. 
    :input: file
        We take as argument the training file
    :output: None
        We have just updated the DataBase 'solibot'
    """
    list_intents = filename['intents']
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    for i in range(len(list_intents)):
        for dic in list_intents:
            if len(dic['patterns']) != 0:
                for j in range(len(dic['patterns'])):
                    # we add in the first line the user message in the column 'text' and the value 'NULL' in the column 'in_response_to'
                    cursor.execute("""INSERT INTO statement(text,conversation) VALUES (?,?)""",
                                   (dic['patterns'][j], 'training'))
                    # we create the response line to the previous line. Thus we add in the first line the user message in the column 'in_response_to'
                    # and the response given by the volunteer (and so our chatbot) in the column 'text'
                    cursor.execute("""INSERT INTO statement(text,conversation,in_response_to) VALUES (?,?,?)""",
                                   (random.choice(dic['responses']), 'training', dic['patterns'][j]))
    conn.commit()
    # conn.close()


def insert_data_training_file(filename):
    """
    We insert into the database the different data sorted with the clustering method.
    Each question or user message is associated to the response. 
    :input: file
        We take as argument the training file
    :output: list
        We return the list Questions/Answers
    """
    list_intents = filename['intents']
    list_training = []
    for i in range(len(list_intents)):
        for dic in list_intents:
            if len(dic['patterns']) != 0:
                for j in range(len(dic['patterns'])):
                    list_training.append(dic['patterns'][j])
                    list_training.append(random.choice(dic['responses']))
    return list_training


global cities
cities = []


def select_city(database=file_path + 'DB_Soliguide.db'):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT ville FROM informations")
    global cities
    cities = []
    res = cursor.fetchall()
    for ele in res:
        cities.append(ele[0])


if __name__ == '__main__':
    # insert_data_to_DB(training_file)
    # write_data_training('training_data/ques_ans.txt',
    #                     insert_data_training_file(training_file))
    select_city()
    print(cities)
    pass
