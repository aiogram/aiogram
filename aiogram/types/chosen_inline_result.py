from .base import Deserializable
from .location import Location
from .user import User


class ChosenInlineResult(Deserializable):
    """
    Represents a result of an inline query that was chosen by the user and sent to their chat partner.
    
    https://core.telegram.org/bots/api#choseninlineresult
    """
    def __init__(self, result_id, from_user, location, inline_message_id, query):
        self.result_id: str = result_id
        self.from_user: User = from_user
        self.location: Location = location
        self.inline_message_id: str = inline_message_id
        self.query: str = query

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        result_id = raw_data.get('result_id')
        from_user = User.deserialize(raw_data.get('from'))
        location = Location.deserialize(raw_data.get('location'))
        inline_message_id = raw_data.get('inline_message_id')
        query = raw_data.get('query')

        return ChosenInlineResult(result_id, from_user, location, inline_message_id, query)
