import typing

from . import base
from . import fields
from . import mixins
from .user import User


class VideoChatParticipantsInvited(base.TelegramObject, mixins.Downloadable):
    """
    This object represents a service message about new members invited to a video chat.

    https://core.telegram.org/bots/api#videochatparticipantsinvited
    """

    users: typing.List[User] = fields.ListField(base=User)
