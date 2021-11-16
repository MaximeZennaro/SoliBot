from chatterbot.logic import LogicAdapter
from clean_process import normalize
import config
from config import cities


def get_specific_info(statement):

    if config.statut_horaire:
        config.TTL_h = 1
        response_statement = "Merci pour ces informations nous les modifierons dès que possible. A bientôt !"
    if config.statut_ref:
        config.TTL_ref = 1
        response_statement = "Merci pour vos informations je vais les transmettre à nos équipes. A bientôt !"

    words_norm_1 = ['horair', 'chang']
    words_norm_2 = ['référenc', 'soliguid']
    words_norm_3 = ['référent', 'soliguid']

    if all(x in normalize(statement.text) for x in words_norm_1):
        response_statement = "Nous vous remercions pour nous en avoir informé. \n Pouvez-vous me transmettre le lien internet / url et/ ou le nom exacte de la structure en question ainsi que les nouvelles horaires ou me donner les informations à modifier ?"
        config.statut_horaire = True
        config.TTL_h = 2
    if all(x in normalize(statement.text) for x in words_norm_2) or all(x in normalize(statement.text) for x in words_norm_3):
        response_statement = "Nous vous remercions pour l'intérêt que vous portez à l'association. \n Pouvez-vous me donner vos coordonnées (e-mail et/ou numéro de téléphone) afin que l'on puisse vous recontacter. Et dans quelle ville/commune souhaitez-vous être référencé ?"
        config.statut_ref = True
        config.TTL_ref = 2

    return response_statement


class SpecificAdapter(LogicAdapter):
    """
    A logic adapter that returns a specific response based on the informations given by the asker
    for the statements such like "nos horaires ont changé", "les horaires de ... ont changé", "je veux être référencé sur Soliguide"
    """

    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)

    def can_process(self, statement):
        """
        Return true if the input statement contains
        'horaire' and 'changé'/'changement'... or 'référencer','Soliguide'
        """
        # if the user asks for more results
        if config.more_choices:
            return False
        # we reset the status variables
        if config.statut_horaire and config.TTL_h == 1:
            config.statut_horaire = False
        if config.statut_ref and config.TTL_ref == 1:
            config.statut_ref = False
        input_statement = statement.text
        statement_norm = normalize(input_statement)
        # if the user gives new information about the modified hours or the referencement
        if (config.statut_ref or config.statut_horaire) and any(normalize(city)[0] in statement_norm for city in cities if len(normalize(city)) != 0):
            return True
        if config.statut_ref or config.statut_horaire:
            return True
        words_norm_1 = ['horair', 'chang']
        words_norm_2 = ['référenc', 'soliguid']
        words_norm_3 = ['référent', 'soliguid']
        if all(x in normalize(statement.text) for x in words_norm_1):
            return True
        if all(x in normalize(statement.text) for x in words_norm_2):
            return True
        if all(x in normalize(statement.text) for x in words_norm_3):
            return True
        else:
            return False

    def process(self, input_statement, additional_response_selection_parameters):
        from chatterbot.conversation import Statement

        response_statement = Statement(text=get_specific_info(input_statement))

        return response_statement
