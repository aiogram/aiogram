from . import base
from . import fields


class LoginUrl(base.TelegramObject):
    """
    This object represents a parameter of the inline keyboard button used to automatically authorize a user.
    Serves as a great replacement for the Telegram Login Widget when the user is coming from Telegram.
    All the user needs to do is tap/click a button and confirm that they want to log in.

    https://core.telegram.org/bots/api#loginurl
    """
    url: base.String = fields.Field()
    forward_text: base.String = fields.Field()
    bot_username: base.String = fields.Field()
    request_write_access: base.Boolean = fields.Field()

    def __init__(self,
                 url: base.String,
                 forward_text: base.String = None,
                 bot_username: base.String = None,
                 request_write_access: base.Boolean = None,
                 **kwargs):
        super(LoginUrl, self).__init__(
            url=url,
            forward_text=forward_text,
            bot_username=bot_username,
            request_write_access=request_write_access,
            **kwargs
        )
