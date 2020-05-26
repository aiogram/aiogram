from __future__ import annotations

import warnings
from typing import Any, Dict, Generator, List, Optional, Union

from ..api.types import TelegramObject, Update
from ..utils.imports import import_module
from ..utils.warnings import CodeHasNoEffect
from .event.bases import NOT_HANDLED, SkipHandler
from .event.event import EventObserver
from .event.telegram import TelegramEventObserver
from .filters import BUILTIN_FILTERS
from .middlewares.error import ErrorsMiddleware


class Router:
    """
    Events router
    """

    def __init__(self, use_builtin_filters: bool = True) -> None:
        self.use_builtin_filters = use_builtin_filters

        self._parent_router: Optional[Router] = None
        self.sub_routers: List[Router] = []

        # Observers
        self.update = TelegramEventObserver(router=self, event_name="update")
        self.message = TelegramEventObserver(router=self, event_name="message")
        self.edited_message = TelegramEventObserver(router=self, event_name="edited_message")
        self.channel_post = TelegramEventObserver(router=self, event_name="channel_post")
        self.edited_channel_post = TelegramEventObserver(
            router=self, event_name="edited_channel_post"
        )
        self.inline_query = TelegramEventObserver(router=self, event_name="inline_query")
        self.chosen_inline_result = TelegramEventObserver(
            router=self, event_name="chosen_inline_result"
        )
        self.callback_query = TelegramEventObserver(router=self, event_name="callback_query")
        self.shipping_query = TelegramEventObserver(router=self, event_name="shipping_query")
        self.pre_checkout_query = TelegramEventObserver(
            router=self, event_name="pre_checkout_query"
        )
        self.poll = TelegramEventObserver(router=self, event_name="poll")
        self.poll_answer = TelegramEventObserver(router=self, event_name="poll_answer")
        self.errors = TelegramEventObserver(router=self, event_name="error")

        self.startup = EventObserver()
        self.shutdown = EventObserver()

        self.observers: Dict[str, TelegramEventObserver] = {
            "update": self.update,
            "message": self.message,
            "edited_message": self.edited_message,
            "channel_post": self.channel_post,
            "edited_channel_post": self.edited_channel_post,
            "inline_query": self.inline_query,
            "chosen_inline_result": self.chosen_inline_result,
            "callback_query": self.callback_query,
            "shipping_query": self.shipping_query,
            "pre_checkout_query": self.pre_checkout_query,
            "poll": self.poll,
            "poll_answer": self.poll_answer,
            "error": self.errors,
        }

        # Root handler
        self.update.register(self._listen_update)

        self.update.outer_middleware(ErrorsMiddleware(self))

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
        event: TelegramObject
        if update.message:
            update_type = "message"
            event = update.message
        elif update.edited_message:
            update_type = "edited_message"
            event = update.edited_message
        elif update.channel_post:
            update_type = "channel_post"
            event = update.channel_post
        elif update.edited_channel_post:
            update_type = "edited_channel_post"
            event = update.edited_channel_post
        elif update.inline_query:
            update_type = "inline_query"
            event = update.inline_query
        elif update.chosen_inline_result:
            update_type = "chosen_inline_result"
            event = update.chosen_inline_result
        elif update.callback_query:
            update_type = "callback_query"
            event = update.callback_query
        elif update.shipping_query:
            update_type = "shipping_query"
            event = update.shipping_query
        elif update.pre_checkout_query:
            update_type = "pre_checkout_query"
            event = update.pre_checkout_query
        elif update.poll:
            update_type = "poll"
            event = update.poll
        elif update.poll_answer:
            update_type = "poll_answer"
            event = update.poll_answer
        else:
            warnings.warn(
                "Detected unknown update type.\n"
                "Seems like Telegram Bot API was updated and you have "
                "installed not latest version of aiogram framework",
                RuntimeWarning,
            )
            raise SkipHandler

        kwargs.update(event_update=update, event_router=self)
        observer = self.observers[update_type]
        response = await observer.trigger(event, update=update, **kwargs)

        if response is NOT_HANDLED:  # Resolve nested routers
            for router in self.sub_routers:
                response = await router.update.trigger(event=update, **kwargs)
                if response is NOT_HANDLED:
                    continue

        return response

    async def emit_startup(self, *args: Any, **kwargs: Any) -> None:
        """
        Recursively call startup callbacks

        :param args:
        :param kwargs:
        :return:
        """
        kwargs.update(router=self)
        await self.startup.trigger(*args, **kwargs)
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
        await self.shutdown.trigger(*args, **kwargs)
        for router in self.sub_routers:
            await router.emit_shutdown(*args, **kwargs)

    @property
    def update_handler(self) -> TelegramEventObserver:
        warnings.warn(
            "`Router.update_handler(...)` is deprecated and will be removed in version 3.2 "
            "use `Router.update(...)`",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.update

    @property
    def message_handler(self) -> TelegramEventObserver:
        warnings.warn(
            "`Router.message_handler(...)` is deprecated and will be removed in version 3.2 "
            "use `Router.message(...)`",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.message

    @property
    def edited_message_handler(self) -> TelegramEventObserver:
        warnings.warn(
            "`Router.edited_message_handler(...)` is deprecated and will be removed in version 3.2 "
            "use `Router.edited_message(...)`",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.edited_message

    @property
    def channel_post_handler(self) -> TelegramEventObserver:
        warnings.warn(
            "`Router.channel_post_handler(...)` is deprecated and will be removed in version 3.2 "
            "use `Router.channel_post(...)`",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.channel_post

    @property
    def edited_channel_post_handler(self) -> TelegramEventObserver:
        warnings.warn(
            "`Router.edited_channel_post_handler(...)` is deprecated and will be removed in version 3.2 "
            "use `Router.edited_channel_post(...)`",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.edited_channel_post

    @property
    def inline_query_handler(self) -> TelegramEventObserver:
        warnings.warn(
            "`Router.inline_query_handler(...)` is deprecated and will be removed in version 3.2 "
            "use `Router.inline_query(...)`",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.inline_query

    @property
    def chosen_inline_result_handler(self) -> TelegramEventObserver:
        warnings.warn(
            "`Router.chosen_inline_result_handler(...)` is deprecated and will be removed in version 3.2 "
            "use `Router.chosen_inline_result(...)`",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.chosen_inline_result

    @property
    def callback_query_handler(self) -> TelegramEventObserver:
        warnings.warn(
            "`Router.callback_query_handler(...)` is deprecated and will be removed in version 3.2 "
            "use `Router.callback_query(...)`",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.callback_query

    @property
    def shipping_query_handler(self) -> TelegramEventObserver:
        warnings.warn(
            "`Router.shipping_query_handler(...)` is deprecated and will be removed in version 3.2 "
            "use `Router.shipping_query(...)`",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.shipping_query

    @property
    def pre_checkout_query_handler(self) -> TelegramEventObserver:
        warnings.warn(
            "`Router.pre_checkout_query_handler(...)` is deprecated and will be removed in version 3.2 "
            "use `Router.pre_checkout_query(...)`",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.pre_checkout_query

    @property
    def poll_handler(self) -> TelegramEventObserver:
        warnings.warn(
            "`Router.poll_handler(...)` is deprecated and will be removed in version 3.2 "
            "use `Router.poll(...)`",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.poll

    @property
    def poll_answer_handler(self) -> TelegramEventObserver:
        warnings.warn(
            "`Router.poll_answer_handler(...)` is deprecated and will be removed in version 3.2 "
            "use `Router.poll_answer(...)`",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.poll_answer

    @property
    def errors_handler(self) -> TelegramEventObserver:
        warnings.warn(
            "`Router.errors_handler(...)` is deprecated and will be removed in version 3.2 "
            "use `Router.errors(...)`",
            DeprecationWarning,
            stacklevel=2,
        )

        return self.errors
