from .base import Deserializable
from .message import Message
from .user import User


class CallbackQuery(Deserializable):
    """
    This object represents an incoming callback query from a callback button in an inline keyboard. 
    
    If the button that originated the query was attached to a message sent by the bot, 
    the field message will be present. 
    
    If the button was attached to a message sent via the bot (in inline mode), 
    the field inline_message_id will be present. 
    
    Exactly one of the fields data or game_short_name will be present.
    
    https://core.telegram.org/bots/api#callbackquery
    """
    def __init__(self, id, from_user, message, inline_message_id, chat_instance, data, game_short_name):
        self.id: int = id
        self.from_user: User = from_user
        self.message: Message = message
        self.inline_message_id: int = inline_message_id
        self.chat_instance: str = chat_instance
        self.data: str = data
        self.game_short_name: str = game_short_name

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        id = raw_data.get('id')
        from_user = User.deserialize(raw_data.get('from'))
        message = Message.deserialize(raw_data.get('message'))
        inline_message_id = raw_data.get('inline_message_id')
        chat_instance = raw_data.get('chat_instance')
        data = raw_data.get('data')
        game_short_name = raw_data.get('game_short_name')

        return CallbackQuery(id, from_user, message, inline_message_id, chat_instance, data, game_short_name)
