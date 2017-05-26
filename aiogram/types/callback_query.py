from . import Deserializable


class CallbackQuery(Deserializable):
    __slots__ = ('id', 'from_user', 'message', 'inline_message_id', 'chat_instance', 'data', 'game_short_name')

    def __init__(self, id, from_user, message, inline_message_id, chat_instance, data, game_short_name):
        self.data = data
        self.id = id
        self.from_user = from_user
        self.message = message
        self.inline_message_id = inline_message_id
        self.chat_instance = chat_instance
        self.data = data
        self.game_short_name = game_short_name

    @classmethod
    def de_json(cls, raw_data):
        raw_data = cls.check_json(raw_data)

        id = raw_data.get('id')
        from_user = raw_data.get('from')
        message = raw_data.get('message')
        inline_message_id = raw_data.get('inline_message_id')
        chat_instance = raw_data.get('chat_instance')
        data = raw_data.get('data')
        game_short_name = raw_data.get('game_short_name')

        return CallbackQuery(id, from_user, message, inline_message_id, chat_instance, data, game_short_name)
