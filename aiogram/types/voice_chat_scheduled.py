from datetime import datetime

from . import base
from . import fields


class VoiceChatScheduled(base.TelegramObject):
    """
    This object represents a service message about a voice chat scheduled in the chat.

    https://core.telegram.org/bots/api#voicechatscheduled
    """

    start_date: datetime = fields.DateTimeField()
