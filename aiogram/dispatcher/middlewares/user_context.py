from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Chat, InaccessibleMessage, TelegramObject, Update, User

EVENT_CONTEXT_KEY = "event_context"

EVENT_FROM_USER_KEY = "event_from_user"
EVENT_CHAT_KEY = "event_chat"
EVENT_THREAD_ID_KEY = "event_thread_id"


@dataclass(frozen=True)
class EventContext:
    chat: Optional[Chat] = None
    user: Optional[User] = None
    thread_id: Optional[int] = None
    business_connection_id: Optional[str] = None

    @property
    def user_id(self) -> Optional[int]:
        return self.user.id if self.user else None

    @property
    def chat_id(self) -> Optional[int]:
        return self.chat.id if self.chat else None


class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Update):
            raise RuntimeError("UserContextMiddleware got an unexpected event type!")
        event_context = data[EVENT_CONTEXT_KEY] = self.resolve_event_context(event=event)

        # Backward compatibility
        if event_context.user is not None:
            data[EVENT_FROM_USER_KEY] = event_context.user
        if event_context.chat is not None:
            data[EVENT_CHAT_KEY] = event_context.chat
        if event_context.thread_id is not None:
            data[EVENT_THREAD_ID_KEY] = event_context.thread_id

        return await handler(event, data)

    @classmethod
    def resolve_event_context(cls, event: Update) -> EventContext:
        """
        Resolve chat and user instance from Update object
        """
        if event.message:
            return EventContext(
                chat=event.message.chat,
                user=event.message.from_user,
                thread_id=event.message.message_thread_id
                if event.message.is_topic_message
                else None,
            )
        if event.edited_message:
            return EventContext(
                chat=event.edited_message.chat,
                user=event.edited_message.from_user,
                thread_id=event.edited_message.message_thread_id
                if event.edited_message.is_topic_message
                else None,
            )
        if event.channel_post:
            return EventContext(chat=event.channel_post.chat)
        if event.edited_channel_post:
            return EventContext(chat=event.edited_channel_post.chat)
        if event.inline_query:
            return EventContext(user=event.inline_query.from_user)
        if event.chosen_inline_result:
            return EventContext(user=event.chosen_inline_result.from_user)
        if event.callback_query:
            if event.callback_query.message:
                return EventContext(
                    chat=event.callback_query.message.chat,
                    user=event.callback_query.from_user,
                    thread_id=event.callback_query.message.message_thread_id
                    if not isinstance(event.callback_query.message, InaccessibleMessage)
                    and event.callback_query.message.is_topic_message
                    else None,
                )
            return EventContext(user=event.callback_query.from_user)
        if event.shipping_query:
            return EventContext(user=event.shipping_query.from_user)
        if event.pre_checkout_query:
            return EventContext(user=event.pre_checkout_query.from_user)
        if event.poll_answer:
            return EventContext(
                chat=event.poll_answer.voter_chat,
                user=event.poll_answer.user,
            )
        if event.my_chat_member:
            return EventContext(
                chat=event.my_chat_member.chat, user=event.my_chat_member.from_user
            )
        if event.chat_member:
            return EventContext(chat=event.chat_member.chat, user=event.chat_member.from_user)
        if event.chat_join_request:
            return EventContext(
                chat=event.chat_join_request.chat, user=event.chat_join_request.from_user
            )
        if event.message_reaction:
            return EventContext(
                chat=event.message_reaction.chat,
                user=event.message_reaction.user,
            )
        if event.message_reaction_count:
            return EventContext(chat=event.message_reaction_count.chat)
        if event.chat_boost:
            return EventContext(chat=event.chat_boost.chat)
        if event.removed_chat_boost:
            return EventContext(chat=event.removed_chat_boost.chat)
        if event.deleted_business_messages:
            return EventContext(
                chat=event.deleted_business_messages.chat,
                business_connection_id=event.deleted_business_messages.business_connection_id,
            )
        if event.business_connection:
            return EventContext(
                user=event.business_connection.user,
                business_connection_id=event.business_connection.id,
            )
        if event.business_message:
            return EventContext(
                chat=event.business_message.chat,
                user=event.business_message.from_user,
                thread_id=event.business_message.message_thread_id
                if event.business_message.is_topic_message
                else None,
                business_connection_id=event.business_message.business_connection_id,
            )
        if event.edited_business_message:
            return EventContext(
                chat=event.edited_business_message.chat,
                user=event.edited_business_message.from_user,
                thread_id=event.edited_business_message.message_thread_id
                if event.edited_business_message.is_topic_message
                else None,
                business_connection_id=event.edited_business_message.business_connection_id,
            )
        return EventContext()
