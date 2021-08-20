from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from .base import TelegramObject

if TYPE_CHECKING:  # pragma: no cover
    from .callback_query import CallbackQuery
    from .chat_member_updated import ChatMemberUpdated
    from .chosen_inline_result import ChosenInlineResult
    from .inline_query import InlineQuery
    from .message import Message
    from .poll import Poll
    from .poll_answer import PollAnswer
    from .pre_checkout_query import PreCheckoutQuery
    from .shipping_query import ShippingQuery


class Update(TelegramObject):
    """
    This `object <https://core.telegram.org/bots/api#available-types>`_ represents an incoming update.

    At most **one** of the optional parameters can be present in any given update.

    Source: https://core.telegram.org/bots/api#update
    """

    update_id: int
    """The update's unique identifier. Update identifiers start from a certain positive number and increase sequentially. This ID becomes especially handy if you're using `Webhooks <https://core.telegram.org/bots/api#setwebhook>`_, since it allows you to ignore repeated updates or to restore the correct update sequence, should they get out of order. If there are no new updates for at least a week, then identifier of the next update will be chosen randomly instead of sequentially."""
    message: Optional[Message] = None
    """*Optional*. New incoming message of any kind — text, photo, sticker, etc."""
    edited_message: Optional[Message] = None
    """*Optional*. New version of a message that is known to the bot and was edited"""
    channel_post: Optional[Message] = None
    """*Optional*. New incoming channel post of any kind — text, photo, sticker, etc."""
    edited_channel_post: Optional[Message] = None
    """*Optional*. New version of a channel post that is known to the bot and was edited"""
    inline_query: Optional[InlineQuery] = None
    """*Optional*. New incoming `inline <https://core.telegram.org/bots/api#inline-mode>`_ query"""
    chosen_inline_result: Optional[ChosenInlineResult] = None
    """*Optional*. The result of an `inline <https://core.telegram.org/bots/api#inline-mode>`_ query that was chosen by a user and sent to their chat partner. Please see our documentation on the `feedback collecting <https://core.telegram.org/bots/inline#collecting-feedback>`_ for details on how to enable these updates for your bot."""
    callback_query: Optional[CallbackQuery] = None
    """*Optional*. New incoming callback query"""
    shipping_query: Optional[ShippingQuery] = None
    """*Optional*. New incoming shipping query. Only for invoices with flexible price"""
    pre_checkout_query: Optional[PreCheckoutQuery] = None
    """*Optional*. New incoming pre-checkout query. Contains full information about checkout"""
    poll: Optional[Poll] = None
    """*Optional*. New poll state. Bots receive only updates about stopped polls and polls, which are sent by the bot"""
    poll_answer: Optional[PollAnswer] = None
    """*Optional*. A user changed their answer in a non-anonymous poll. Bots receive new votes only in polls that were sent by the bot itself."""
    my_chat_member: Optional[ChatMemberUpdated] = None
    """*Optional*. The bot's chat member status was updated in a chat. For private chats, this update is received only when the bot is blocked or unblocked by the user."""
    chat_member: Optional[ChatMemberUpdated] = None
    """*Optional*. A chat member's status was updated in a chat. The bot must be an administrator in the chat and must explicitly specify 'chat_member' in the list of *allowed_updates* to receive these updates."""

    @property
    def event(self) -> Tuple[str, TelegramObject]:
        """
        Detect content type

        Return update type and event
        If update type unknown raise UpdateTypeLookupError

        :return:
        """
        event: TelegramObject
        if self.message:
            update_type = "message"
            event = self.message
        elif self.edited_message:
            update_type = "edited_message"
            event = self.edited_message
        elif self.channel_post:
            update_type = "channel_post"
            event = self.channel_post
        elif self.edited_channel_post:
            update_type = "edited_channel_post"
            event = self.edited_channel_post
        elif self.inline_query:
            update_type = "inline_query"
            event = self.inline_query
        elif self.chosen_inline_result:
            update_type = "chosen_inline_result"
            event = self.chosen_inline_result
        elif self.callback_query:
            update_type = "callback_query"
            event = self.callback_query
        elif self.shipping_query:
            update_type = "shipping_query"
            event = self.shipping_query
        elif self.pre_checkout_query:
            update_type = "pre_checkout_query"
            event = self.pre_checkout_query
        elif self.poll:
            update_type = "poll"
            event = self.poll
        elif self.poll_answer:
            update_type = "poll_answer"
            event = self.poll_answer
        elif self.my_chat_member:
            update_type = "my_chat_member"
            event = self.my_chat_member
        elif self.chat_member:
            update_type = "chat_member"
            event = self.chat_member
        else:
            raise UpdateTypeLookupError("Unknown update type")

        return update_type, event


class UpdateTypeLookupError(LookupError):
    pass
