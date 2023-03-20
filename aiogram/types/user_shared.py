from . import base, fields


class UserShared(base.TelegramObject):
    """
    This object contains information about the user whose identifier was
    shared with the bot using a KeyboardButtonRequestUser button.

    https://core.telegram.org/bots/api#usershared
    """
    request_id: base.Integer = fields.Field()
    user_id: base.Integer = fields.Field()
