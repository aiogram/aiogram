from .base import Deserializable


class ResponseParameters(Deserializable):
    """
    Contains information about why a request was unsuccessfull.
    
    https://core.telegram.org/bots/api#responseparameters
    """
    def __init__(self, migrate_to_chat_id, retry_after):
        self.migrate_to_chat_id = migrate_to_chat_id
        self.retry_after = retry_after

    @classmethod
    def de_json(cls, raw_data):
        data = cls.check_json(raw_data)

        migrate_to_chat_id = data.get('migrate_to_chat_id')
        retry_after = data.get('retry_after')

        return ResponseParameters(migrate_to_chat_id, retry_after)
