from datetime import datetime

from . import base
from . import fields


class VideoChatScheduled(base.TelegramObject):
    """
    This object represents a service message about a video chat scheduled in the chat.

    https://core.telegram.org/bots/api#videochatscheduled
    """

    start_date: datetime = fields.DateTimeField()
