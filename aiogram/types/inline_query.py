import typing

from . import base
from . import fields
from .inline_query_result import InlineQueryResult
from .location import Location
from .user import User


class InlineQuery(base.TelegramObject):
    """
    This object represents an incoming inline query.

    When the user sends an empty query, your bot could return some default or trending results.

    https://core.telegram.org/bots/api#inlinequery
    """
    id: base.String = fields.Field()
    from_user: User = fields.Field(alias='from', base=User)
    location: Location = fields.Field(base=Location)
    query: base.String = fields.Field()
    offset: base.String = fields.Field()

    async def answer(self,
                     results: typing.List[InlineQueryResult],
                     cache_time: typing.Union[base.Integer, None] = None,
                     is_personal: typing.Union[base.Boolean, None] = None,
                     next_offset: typing.Union[base.String, None] = None,
                     switch_pm_text: typing.Union[base.String, None] = None,
                     switch_pm_parameter: typing.Union[base.String, None] = None):
        """
        Use this method to send answers to an inline query.
        No more than 50 results per query are allowed.

        Source: https://core.telegram.org/bots/api#answerinlinequery

        :param results: A JSON-serialized array of results for the inline query
        :type results: :obj:`typing.List[types.InlineQueryResult]`
        :param cache_time: The maximum amount of time in seconds that the result of the
            inline query may be cached on the server. Defaults to 300.
        :type cache_time: :obj:`typing.Union[base.Integer, None]`
        :param is_personal: Pass True, if results may be cached on the server side only
            for the user that sent the query. By default, results may be returned to any user who sends the same query
        :type is_personal: :obj:`typing.Union[base.Boolean, None]`
        :param next_offset: Pass the offset that a client should send in the
            next query with the same text to receive more results.
            Pass an empty string if there are no more results or if you don‘t support pagination.
            Offset length can’t exceed 64 bytes.
        :type next_offset: :obj:`typing.Union[base.String, None]`
        :param switch_pm_text: If passed, clients will display a button with specified text that
            switches the user to a private chat with the bot and sends the bot a start message
            with the parameter switch_pm_parameter
        :type switch_pm_text: :obj:`typing.Union[base.String, None]`
        :param switch_pm_parameter: Deep-linking parameter for the /start message sent to the bot when
            user presses the switch button. 1-64 characters, only A-Z, a-z, 0-9, _ and - are allowed.
        :type switch_pm_parameter: :obj:`typing.Union[base.String, None]`
        :return: On success, True is returned
        :rtype: :obj:`base.Boolean`
        """
        return await self.bot.answer_inline_query(self.id,
                                                  results=results,
                                                  cache_time=cache_time,
                                                  is_personal=is_personal,
                                                  next_offset=next_offset,
                                                  switch_pm_text=switch_pm_text,
                                                  switch_pm_parameter=switch_pm_parameter)
