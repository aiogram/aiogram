from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Chat, TelegramObject, Update, User

EVENT_FROM_USER_KEY = "event_from_user"
EVENT_CHAT_KEY = "event_chat"
EVENT_THREAD_ID_KEY = "event_thread_id"


class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Update):
            raise RuntimeError("UserContextMiddleware got an unexpected event type!")
        chat, user, thread_id = self.resolve_event_context(event=event)
        if user is not None:
            data[EVENT_FROM_USER_KEY] = user
        if chat is not None:
            data[EVENT_CHAT_KEY] = chat
        if thread_id is not None:
            data[EVENT_THREAD_ID_KEY] = thread_id
        return await handler(event, data)

    @classmethod
    def resolve_event_context(
        cls, event: Update
    ) -> Tuple[Optional[Chat], Optional[User], Optional[int]]:
        """
        Resolve chat and user instance from Update object
        """
        if event.message:
            return (
                event.message.chat,
                event.message.from_user,
                event.message.message_thread_id if event.message.is_topic_message else None,
            )
        if event.edited_message:
            return (
                event.edited_message.chat,
                event.edited_message.from_user,
                event.edited_message.message_thread_id
                if event.edited_message.is_topic_message
                else None,
            )
        if event.channel_post:
            return event.channel_post.chat, None, None
        if event.edited_channel_post:
            return event.edited_channel_post.chat, None, None
        if event.inline_query:
            return None, event.inline_query.from_user, None
        if event.chosen_inline_result:
            return None, event.chosen_inline_result.from_user, None
        if event.callback_query:
            if event.callback_query.message:
                return (
                    event.callback_query.message.chat,
                    event.callback_query.from_user,
                    event.callback_query.message.message_thread_id
                    if event.callback_query.message.is_topic_message
                    else None,
                )
            return None, event.callback_query.from_user, None
        if event.shipping_query:
            return None, event.shipping_query.from_user, None
        if event.pre_checkout_query:
            return None, event.pre_checkout_query.from_user, None
        if event.poll_answer:
            return None, event.poll_answer.user, None
        if event.my_chat_member:
            return event.my_chat_member.chat, event.my_chat_member.from_user, None
        if event.chat_member:
            return event.chat_member.chat, event.chat_member.from_user, None
        if event.chat_join_request:
            return event.chat_join_request.chat, event.chat_join_request.from_user, None
        return None, None, None
