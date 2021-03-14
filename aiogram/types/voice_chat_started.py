from . import base
from . import mixins


class VoiceChatStarted(base.TelegramObject, mixins.Downloadable):
    """
    This object represents a service message about a voice chat started in the chat.
    Currently holds no information.

    https://core.telegram.org/bots/api#voicechatstarted
    """
    pass
