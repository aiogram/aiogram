from . import Deserializable


class CallbackQuery(Deserializable):
    __slots__ = ('data', 'id', 'from', 'message', 'inline_message_id', 'chat_instance', 'data', 'game_short_name')

    def __init__(self, data, id, from_user, message, inline_message_id, chat_instance, data, game_short_name):
        self.data = data
        self.id = id
        self.from_user = from_user
        self.message = message
        self.inline_message_id = inline_message_id
        self.chat_instance = chat_instance
        self.data = data
        self.game_short_name = game_short_name

    @classmethod
    def de_json(cls, data):
        data = cls.check_json(data)

        id = data.get('id')
        from_user = data.get('from')
        message = data.get('message')
        inline_message_id = data.get('inline_message_id')
        chat_instance = data.get('chat_instance')
        data = data.get('data')
        game_short_name = data.get('game_short_name')

        return CallbackQuery(data, id, from_user, message, inline_message_id, chat_instance, data, game_short_name)
