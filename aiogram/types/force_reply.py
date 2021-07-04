import typing

from . import base
from . import fields


class ForceReply(base.TelegramObject):
    """
    Upon receiving a message with this object, Telegram clients will
    display a reply interface to the user (act as if the user has
    selected the bot's message and tapped 'Reply'). This can be
    extremely useful if you want to create user-friendly step-by-step
    interfaces without having to sacrifice privacy mode.

    https://core.telegram.org/bots/api#forcereply
    """
    force_reply: base.Boolean = fields.Field(default=True)
    input_field_placeholder: base.String = fields.Field()
    selective: base.Boolean = fields.Field()

    @classmethod
    def create(cls,
               input_field_placeholder: typing.Optional[base.String] = None,
               selective: typing.Optional[base.Boolean] = None,
               ) -> 'ForceReply':
        """
        Create new force reply

        :param selective:
        :param input_field_placeholder:
        :return:
        """
        return cls(selective=selective, input_field_placeholder=input_field_placeholder)
