import typing

from . import base
from . import fields
from .message import Message
from .user import User


class CallbackQuery(base.TelegramObject):
    """
    This object represents an incoming callback query from a callback button in an inline keyboard.

    If the button that originated the query was attached to a message sent by the bot,
    the field message will be present.

    If the button was attached to a message sent via the bot (in inline mode),
    the field inline_message_id will be present.

    Exactly one of the fields data or game_short_name will be present.

    https://core.telegram.org/bots/api#callbackquery
    """
    id: base.String = fields.Field()
    from_user: User = fields.Field(alias='from', base=User)
    message: Message = fields.Field(base=Message)
    inline_message_id: base.String = fields.Field()
    chat_instance: base.String = fields.Field()
    data: base.String = fields.Field()
    game_short_name: base.String = fields.Field()

    async def answer(self, text: typing.Union[base.String, None] = None,
                     show_alert: typing.Union[base.Boolean, None] = None,
                     url: typing.Union[base.String, None] = None,
                     cache_time: typing.Union[base.Integer, None] = None):
        """
        Use this method to send answers to callback queries sent from inline keyboards.
        The answer will be displayed to the user as a notification at the top of the chat screen or as an alert.

        Alternatively, the user can be redirected to the specified Game URL.
        For this option to work, you must first create a game for your bot via @Botfather and accept the terms.
        Otherwise, you may use links like t.me/your_bot?start=XXXX that open your bot with a parameter.

        Source: https://core.telegram.org/bots/api#answercallbackquery

        :param text: Text of the notification. If not specified, nothing will be shown to the user, 0-200 characters
        :type text: :obj:`typing.Union[base.String, None]`
        :param show_alert: If true, an alert will be shown by the client instead of a notification
            at the top of the chat screen. Defaults to false.
        :type show_alert: :obj:`typing.Union[base.Boolean, None]`
        :param url: URL that will be opened by the user's client.
        :type url: :obj:`typing.Union[base.String, None]`
        :param cache_time: The maximum amount of time in seconds that the
            result of the callback query may be cached client-side.
        :type cache_time: :obj:`typing.Union[base.Integer, None]`
        :return: On success, True is returned.
        :rtype: :obj:`base.Boolean`"""
        return await self.bot.answer_callback_query(callback_query_id=self.id,
                                                    text=text,
                                                    show_alert=show_alert,
                                                    url=url,
                                                    cache_time=cache_time)

    def __hash__(self):
        return hash(self.id)
