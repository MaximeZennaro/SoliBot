from chatterbot.logic import LogicAdapter
from chatterbot import filters
from clean_process import cate_value_norm, normalize, return_NER
from training import cities


class StatementAdapter(LogicAdapter):
    """
    A logic adapter that returns a response based on known responses to
    the closest matches to the input statement.

    :param excluded_words:
        The excluded_words parameter allows a list of words to be set that will
        prevent the logic adapter from returning statements that have text
        containing any of those words. This can be useful for preventing your
        chat bot from saying swears when it is being demonstrated in front of
        an audience.
        Defaults to None
    :type excluded_words: list
    """

    def __init__(self, chatbot, **kwargs):
        super().__init__(chatbot, **kwargs)

        self.excluded_words = kwargs.get('excluded_words')

    def can_process(self, statement):
        """
        Return False if the input statement contains
        one of the branch name of the DB or one value, or
        corresponds to the specific adapter. Indeed, this
        adapter is used for the other responses with no specific
        output.
        """
        input_statement = statement.text
        statement_norm = normalize(input_statement)
        print(statement_norm)
        if len(input_statement.split()) == 1:
            input_statement = "sur " + input_statement
        if any(x in statement_norm for x in cate_value_norm):
            return False
        if any(normalize(city) in statement_norm for city in cities):
            return False
        words_norm_1 = ['horair', 'chang']
        words_norm_2 = ['référenc', 'soliguid']
        if all(x in normalize(statement.text) for x in words_norm_1):
            return False
        if all(x in normalize(statement.text) for x in words_norm_2):
            return False
        return True

    def process(self, input_statement, additional_response_selection_parameters=None):
        search_results = self.search_algorithm.search(input_statement)

        # Use the input statement as the closest match if no other results are found
        closest_match = next(search_results, input_statement)

        # Search for the closest match to the input statement
        for result in search_results:

            # Stop searching if a match that is close enough is found
            if result.confidence >= self.maximum_similarity_threshold:
                closest_match = result
                break

        self.chatbot.logger.info('Using "{}" as a close match to "{}" with a confidence of {}'.format(
            closest_match.text, input_statement.text, closest_match.confidence
        ))

        recent_repeated_responses = filters.get_recent_repeated_responses(
            self.chatbot,
            input_statement.conversation
        )

        for index, recent_repeated_response in enumerate(recent_repeated_responses):
            self.chatbot.logger.info('{}. Excluding recent repeated response of "{}"'.format(
                index, recent_repeated_response
            ))

        response_selection_parameters = {
            'search_in_response_to': closest_match.search_text,
            'exclude_text': recent_repeated_responses,
            'exclude_text_words': self.excluded_words
        }

        alternate_response_selection_parameters = {
            'search_in_response_to': self.chatbot.storage.tagger.get_bigram_pair_string(
                input_statement.text
            ),
            'exclude_text': recent_repeated_responses,
            'exclude_text_words': self.excluded_words
        }

        if additional_response_selection_parameters:
            response_selection_parameters.update(
                additional_response_selection_parameters)
            alternate_response_selection_parameters.update(
                additional_response_selection_parameters)

        # Get all statements that are in response to the closest match
        response_list = list(self.chatbot.storage.filter(
            **response_selection_parameters))

        alternate_response_list = []

        if not response_list:
            self.chatbot.logger.info(
                'No responses found. Generating alternate response list.')
            alternate_response_list = list(self.chatbot.storage.filter(
                **alternate_response_selection_parameters))

        if response_list:
            self.chatbot.logger.info(
                'Selecting response from {} optimal responses.'.format(
                    len(response_list)
                )
            )

            response = self.select_response(
                input_statement,
                response_list,
                self.chatbot.storage
            )

            response.confidence = closest_match.confidence
            self.chatbot.logger.info(
                'Response selected. Using "{}"'.format(response.text))
        elif alternate_response_list:
            '''
            The case where there was no responses returned for the selected match
            but a value exists for the statement the match is in response to.
            '''
            self.chatbot.logger.info(
                'Selecting response from {} optimal alternate responses.'.format(
                    len(alternate_response_list)
                )
            )
            response = self.select_response(
                input_statement,
                alternate_response_list,
                self.chatbot.storage
            )

            response.confidence = closest_match.confidence
            self.chatbot.logger.info(
                'Alternate response selected. Using "{}"'.format(response.text))
        else:
            response = self.get_default_response(input_statement)

        return response
