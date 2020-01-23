from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    from .callback_query import CallbackQuery
    from .chosen_inline_result import ChosenInlineResult
    from .inline_query import InlineQuery
    from .message import Message
    from .poll import Poll
    from .poll_answer import PollAnswer
    from .pre_checkout_query import PreCheckoutQuery
    from .shipping_query import ShippingQuery


class Update(TelegramObject):
    """
    This object represents an incoming update.
    At most one of the optional parameters can be present in any given update.

    Source: https://core.telegram.org/bots/api#update
    """

    update_id: int
    """The update‘s unique identifier. Update identifiers start from a certain positive number and
    increase sequentially. This ID becomes especially handy if you’re using Webhooks, since it
    allows you to ignore repeated updates or to restore the correct update sequence, should
    they get out of order. If there are no new updates for at least a week, then identifier of
    the next update will be chosen randomly instead of sequentially."""
    message: Optional[Message] = None
    """New incoming message of any kind — text, photo, sticker, etc."""
    edited_message: Optional[Message] = None
    """New version of a message that is known to the bot and was edited"""
    channel_post: Optional[Message] = None
    """New incoming channel post of any kind — text, photo, sticker, etc."""
    edited_channel_post: Optional[Message] = None
    """New version of a channel post that is known to the bot and was edited"""
    inline_query: Optional[InlineQuery] = None
    """New incoming inline query"""
    chosen_inline_result: Optional[ChosenInlineResult] = None
    """The result of an inline query that was chosen by a user and sent to their chat partner.
    Please see our documentation on the feedback collecting for details on how to enable these
    updates for your bot."""
    callback_query: Optional[CallbackQuery] = None
    """New incoming callback query"""
    shipping_query: Optional[ShippingQuery] = None
    """New incoming shipping query. Only for invoices with flexible price"""
    pre_checkout_query: Optional[PreCheckoutQuery] = None
    """New incoming pre-checkout query. Contains full information about checkout"""
    poll: Optional[Poll] = None
    """New poll state. Bots receive only updates about stopped polls and polls, which are sent by
    the bot"""
    poll_answer: Optional[PollAnswer] = None
    """A user changed their answer in a non-anonymous poll. Bots receive new votes only in polls
    that were sent by the bot itself."""
