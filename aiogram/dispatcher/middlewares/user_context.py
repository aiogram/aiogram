from contextlib import contextmanager
from typing import Any, Awaitable, Callable, Dict, Iterator, Optional, Tuple

from aiogram.api.types import Chat, Update, User
from aiogram.dispatcher.middlewares.base import BaseMiddleware


class UserContextMiddleware(BaseMiddleware[Update]):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        chat, user = self.resolve_event_context(event=event)
        with self.context(chat=chat, user=user):
            return await handler(event, data)

    @contextmanager
    def context(self, chat: Optional[Chat] = None, user: Optional[User] = None) -> Iterator[None]:
        chat_token = None
        user_token = None
        if chat:
            chat_token = chat.set_current(chat)
        if user:
            user_token = user.set_current(user)
        try:
            yield
        finally:
            if chat and chat_token:
                chat.reset_current(chat_token)
            if user and user_token:
                user.reset_current(user_token)

    @classmethod
    def resolve_event_context(cls, event: Update) -> Tuple[Optional[Chat], Optional[User]]:
        """
        Resolve chat and user instance from Update object
        """
        if event.message:
            return event.message.chat, event.message.from_user
        if event.edited_message:
            return event.edited_message.chat, event.edited_message.from_user
        if event.channel_post:
            return event.channel_post.chat, None
        if event.edited_channel_post:
            return event.edited_channel_post.chat, None
        if event.inline_query:
            return None, event.inline_query.from_user
        if event.chosen_inline_result:
            return None, event.chosen_inline_result.from_user
        if event.callback_query:
            if event.callback_query.message:
                return event.callback_query.message.chat, event.callback_query.from_user
            return None, event.callback_query.from_user
        if event.shipping_query:
            return None, event.shipping_query.from_user
        if event.pre_checkout_query:
            return None, event.pre_checkout_query.from_user
        if event.poll_answer:
            return None, event.poll_answer.user
        return None, None
