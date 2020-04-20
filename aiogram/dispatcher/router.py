from __future__ import annotations

import warnings
from typing import Any, Dict, Generator, List, Optional, Union

from ..api.types import Chat, TelegramObject, Update, User
from ..utils.imports import import_module
from ..utils.warnings import CodeHasNoEffect
from .event.observer import EventObserver, SkipHandler, TelegramEventObserver
from .filters import BUILTIN_FILTERS
from .middlewares.abstract import AbstractMiddleware
from .middlewares.manager import MiddlewareManager


class Router:
    """
    Events router
    """

    def __init__(self, use_builtin_filters: bool = True) -> None:
        self.use_builtin_filters = use_builtin_filters

        self._parent_router: Optional[Router] = None
        self.sub_routers: List[Router] = []

        # Observers
        self.update_handler = TelegramEventObserver(router=self, event_name="update")
        self.message_handler = TelegramEventObserver(router=self, event_name="message")
        self.edited_message_handler = TelegramEventObserver(
            router=self, event_name="edited_message"
        )
        self.channel_post_handler = TelegramEventObserver(router=self, event_name="channel_post")
        self.edited_channel_post_handler = TelegramEventObserver(
            router=self, event_name="edited_channel_post"
        )
        self.inline_query_handler = TelegramEventObserver(router=self, event_name="inline_query")
        self.chosen_inline_result_handler = TelegramEventObserver(
            router=self, event_name="chosen_inline_result"
        )
        self.callback_query_handler = TelegramEventObserver(
            router=self, event_name="callback_query"
        )
        self.shipping_query_handler = TelegramEventObserver(
            router=self, event_name="shipping_query"
        )
        self.pre_checkout_query_handler = TelegramEventObserver(
            router=self, event_name="pre_checkout_query"
        )
        self.poll_handler = TelegramEventObserver(router=self, event_name="poll")
        self.poll_answer_handler = TelegramEventObserver(router=self, event_name="poll_answer")
        self.errors_handler = TelegramEventObserver(router=self, event_name="error")

        self.middleware = MiddlewareManager(router=self)

        self.startup = EventObserver()
        self.shutdown = EventObserver()

        self.observers: Dict[str, TelegramEventObserver] = {
            "update": self.update_handler,
            "message": self.message_handler,
            "edited_message": self.edited_message_handler,
            "channel_post": self.channel_post_handler,
            "edited_channel_post": self.edited_channel_post_handler,
            "inline_query": self.inline_query_handler,
            "chosen_inline_result": self.chosen_inline_result_handler,
            "callback_query": self.callback_query_handler,
            "shipping_query": self.shipping_query_handler,
            "pre_checkout_query": self.pre_checkout_query_handler,
            "poll": self.poll_handler,
            "poll_answer": self.poll_answer_handler,
            "error": self.errors_handler,
        }

        # Root handler
        self.update_handler.register(self._listen_update)

        # Builtin filters
        if use_builtin_filters:
            for name, observer in self.observers.items():
                for builtin_filter in BUILTIN_FILTERS.get(name, ()):
                    observer.bind_filter(builtin_filter)

    @property
    def chain_head(self) -> Generator[Router, None, None]:
        router: Optional[Router] = self
        while router:
            yield router
            router = router.parent_router

    @property
    def chain_tail(self) -> Generator[Router, None, None]:
        yield self
        for router in self.sub_routers:
            yield from router.chain_tail

    @property
    def chain(self) -> Generator[Router, None, None]:
        yield from self.chain_head
        tail = self.chain_tail
        next(tail)  # Skip self
        yield from tail

    def use(self, middleware: AbstractMiddleware, _stack_level: int = 1) -> AbstractMiddleware:
        """
        Use middleware

        :param middleware:
        :param _stack_level:
        :return:
        """
        return self.middleware.setup(middleware, _stack_level=_stack_level + 1)

    @property
    def parent_router(self) -> Optional[Router]:
        return self._parent_router

    @parent_router.setter
    def parent_router(self, router: Router) -> None:
        """
        Internal property setter of parent router fot this router.
        Do not use this method in own code.
        All routers should be included via `include_router` method.

        Self- and circular- referencing are not allowed here

        :param router:
        """
        if not isinstance(router, Router):
            raise ValueError(
                f"router should be instance of Router not {type(router).__class__.__name__}"
            )
        if self._parent_router:
            raise RuntimeError(f"Router is already attached to {self._parent_router!r}")
        if self == router:
            raise RuntimeError("Self-referencing routers is not allowed")

        parent: Optional[Router] = router
        while parent is not None:
            if parent == self:
                raise RuntimeError("Circular referencing of Router is not allowed")

            if not self.use_builtin_filters and parent.use_builtin_filters:
                warnings.warn(
                    f"Router(use_builtin_filters=False) has no effect for router {self} "
                    f"in due to builtin filters is already registered in parent router",
                    CodeHasNoEffect,
                    stacklevel=3,
                )

            parent = parent.parent_router

        self._parent_router = router
        router.sub_routers.append(self)

    def include_router(self, router: Union[Router, str]) -> Router:
        """
        Attach another router.

        Can be attached directly or by import string in format "<module>:<attribute>"

        :param router:
        :return:
        """
        if isinstance(router, str):  # Resolve import string
            router = import_module(router)
        if not isinstance(router, Router):
            raise ValueError(
                f"router should be instance of Router not {type(router).__class__.__name__}"
            )
        router.parent_router = self
        return router

    async def _listen_update(self, update: Update, **kwargs: Any) -> Any:
        """
        Main updates listener

        Workflow:
        - Detect content type and propagate to observers in current router
        - If no one filter is pass - propagate update to child routers as Update

        :param update:
        :param kwargs:
        :return:
        """
        chat: Optional[Chat] = None
        from_user: Optional[User] = None

        event: TelegramObject
        if update.message:
            update_type = "message"
            from_user = update.message.from_user
            chat = update.message.chat
            event = update.message
        elif update.edited_message:
            update_type = "edited_message"
            from_user = update.edited_message.from_user
            chat = update.edited_message.chat
            event = update.edited_message
        elif update.channel_post:
            update_type = "channel_post"
            chat = update.channel_post.chat
            event = update.channel_post
        elif update.edited_channel_post:
            update_type = "edited_channel_post"
            chat = update.edited_channel_post.chat
            event = update.edited_channel_post
        elif update.inline_query:
            update_type = "inline_query"
            from_user = update.inline_query.from_user
            event = update.inline_query
        elif update.chosen_inline_result:
            update_type = "chosen_inline_result"
            from_user = update.chosen_inline_result.from_user
            event = update.chosen_inline_result
        elif update.callback_query:
            update_type = "callback_query"
            if update.callback_query.message:
                chat = update.callback_query.message.chat
            from_user = update.callback_query.from_user
            event = update.callback_query
        elif update.shipping_query:
            update_type = "shipping_query"
            from_user = update.shipping_query.from_user
            event = update.shipping_query
        elif update.pre_checkout_query:
            update_type = "pre_checkout_query"
            from_user = update.pre_checkout_query.from_user
            event = update.pre_checkout_query
        elif update.poll:
            update_type = "poll"
            event = update.poll
        else:
            warnings.warn(
                "Detected unknown update type.\n"
                "Seems like Telegram Bot API was updated and you have "
                "installed not latest version of aiogram framework",
                RuntimeWarning,
            )
            raise SkipHandler

        return await self.listen_update(
            update_type=update_type,
            update=update,
            event=event,
            from_user=from_user,
            chat=chat,
            **kwargs,
        )

    async def listen_update(
        self,
        update_type: str,
        update: Update,
        event: TelegramObject,
        from_user: Optional[User] = None,
        chat: Optional[Chat] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Listen update by current and child routers

        :param update_type:
        :param update:
        :param event:
        :param from_user:
        :param chat:
        :param kwargs:
        :return:
        """
        user_token = None
        if from_user:
            user_token = User.set_current(from_user)
        chat_token = None
        if chat:
            chat_token = Chat.set_current(chat)

        kwargs.update(event_update=update, event_router=self)
        observer = self.observers[update_type]
        try:
            async for result in observer.trigger(event, update=update, **kwargs):
                return result

            for router in self.sub_routers:
                try:
                    return await router.listen_update(
                        update_type=update_type,
                        update=update,
                        event=event,
                        from_user=from_user,
                        chat=chat,
                        **kwargs,
                    )
                except SkipHandler:
                    continue

            raise SkipHandler

        except SkipHandler:
            raise

        except Exception as e:
            async for result in self.errors_handler.trigger(e, **kwargs):
                return result
            raise

        finally:
            if user_token:
                User.reset_current(user_token)
            if chat_token:
                Chat.reset_current(chat_token)

    async def emit_startup(self, *args: Any, **kwargs: Any) -> None:
        """
        Recursively call startup callbacks

        :param args:
        :param kwargs:
        :return:
        """
        kwargs.update(router=self)
        async for _ in self.startup.trigger(*args, **kwargs):  # pragma: no cover
            pass
        for router in self.sub_routers:
            await router.emit_startup(*args, **kwargs)

    async def emit_shutdown(self, *args: Any, **kwargs: Any) -> None:
        """
        Recursively call shutdown callbacks to graceful shutdown

        :param args:
        :param kwargs:
        :return:
        """
        kwargs.update(router=self)
        async for _ in self.shutdown.trigger(*args, **kwargs):  # pragma: no cover
            pass
        for router in self.sub_routers:
            await router.emit_shutdown(*args, **kwargs)
