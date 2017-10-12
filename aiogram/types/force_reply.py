import typing

from . import base
from . import fields


class ForceReply(base.TelegramObject):
    """
    Upon receiving a message with this object,
    Telegram clients will display a reply interface to the user
    (act as if the user has selected the bot‘s message and tapped ’Reply').
    This can be extremely useful if you want to create user-friendly step-by-step
    interfaces without having to sacrifice privacy mode.

    Example: A poll bot for groups runs in privacy mode
    (only receives commands, replies to its messages and mentions).
    There could be two ways to create a new poll

    The last option is definitely more attractive.
    And if you use ForceReply in your bot‘s questions, it will receive the user’s answers even
    if it only receives replies, commands and mentions — without any extra work for the user.

    https://core.telegram.org/bots/api#forcereply
    """
    force_reply: base.Boolean = fields.Field(default=True)
    selective: base.Boolean = fields.Field()

    @classmethod
    def create(cls, selective: typing.Optional[base.Boolean] = None):
        """
        Create new force reply

        :param selective:
        :return:
        """
        return cls(selective=selective)
