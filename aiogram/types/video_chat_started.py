from . import base
from . import mixins


class VideoChatStarted(base.TelegramObject, mixins.Downloadable):
    """
    his object represents a service message about a video chat started in the chat. Currently holds no information.

    https://core.telegram.org/bots/api#videochatstarted
    """
    pass
