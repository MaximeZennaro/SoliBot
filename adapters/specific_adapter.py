from chatterbot.logic import LogicAdapter
from clean_process import normalize


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
        words_norm_1 = ['horair', 'chang']
        words_norm_2 = ['référenc', 'soliguid']
        if all(x in normalize(statement.text) for x in words_norm_1):
            return True
        if all(x in normalize(statement.text) for x in words_norm_2):
            return True
        else:
            return False

    def process(self, input_statement, additional_response_selection_parameters):
        from chatterbot.conversation import Statement

        words_norm_1 = ['horair', 'chang']
        words_norm_2 = ['référenc', 'soliguid']

        if all(x in normalize(input_statement.text) for x in words_norm_1):
            response_statement = Statement(
                text="Nous vous remercions pour nous en avoir informé. Je vous invite à signaler ce changement directement à l'équipe Soliguide afin qu'ils puissent mettre à jour les informations en question")

        if all(x in normalize(input_statement.text) for x in words_norm_2):
            response_statement = Statement(
                text="Nous vous remercions pour l'intérêt que vous portez à l'association. Je vous invite à transmettre votre demande directement à Soliguide")

        return response_statement
