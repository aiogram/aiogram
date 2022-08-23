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
        parameters = (
            'message', 'edited_message',
            'channel_post', 'edited_channel_post',
            'chosen_inline_result', 'callback_query',
            'shipping_query', 'pre_checkout_query',
            'poll_answer', 'my_chat_member',
            'chat_member', 'chat_join_request',
            'inline_query',
        )
        for parameter in parameters:
            telegram_obj = getattr(event, parameter, None)
            if telegram_obj:
                break
    
        if not telegram_obj:
            return None, None
        if parameter == 'inline_query' and telegram_obj.message:
            return parameter.message.chat, parameter.message.from_user
        if parameter == 'poll_answer':
            return None, parameter.user

        return getattr(parameter, 'chat', None), getattr(parameter, 'from_user', None)
