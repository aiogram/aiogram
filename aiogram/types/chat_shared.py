from . import base, fields


class ChatShared(base.TelegramObject):
    """
    This object contains information about the chat whose identifier was
    shared with the bot using a KeyboardButtonRequestChat button.

    https://core.telegram.org/bots/api#chatshared
    """
    request_id: base.Integer = fields.Field()
    user_id: base.Integer = fields.Field()
