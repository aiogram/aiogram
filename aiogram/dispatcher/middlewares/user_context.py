from contextlib import contextmanager
from typing import Any, Awaitable, Callable, Dict, Iterator, Optional, Tuple

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import Chat, TelegramObject, Update, User


class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Update):
            raise RuntimeError("UserContextMiddleware got an unexpected event type!")
        chat, user = self.resolve_event_context(event=event)
        with self.context(chat=chat, user=user):
            if user is not None:
                data["event_from_user"] = user
            if chat is not None:
                data["event_chat"] = chat
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
        if event.inline_query:
            if event.inlinee_query.message:
                return event.callback_query.message.chat, event.callback_query.from_user
            return None, event.callback_query.from_user

        parametrs = (
            'message', 'edited_message',
            'channel_post', 'edited_channel_post',
            'chosen_inline_result', 'callback_query',
            'shipping_query', 'pre_checkout_query',
            'poll_answer', 'my_chat_member',
            'chat_member', 'chat_join_request',
        )
        for parametr in parametrs:
            parametr = getattr(event, parametr, None)
            if parametr:
                break
        return getattr(parametr, 'chat', None), getattr(parametr, 'from_user', None)
