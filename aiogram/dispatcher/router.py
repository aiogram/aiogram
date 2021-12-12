from __future__ import annotations

import warnings
from typing import Any, Dict, Generator, List, Optional, Set, Union

from ..types import TelegramObject
from ..utils.imports import import_module
from ..utils.warnings import CodeHasNoEffect
from .event.bases import REJECTED, UNHANDLED
from .event.event import EventObserver
from .event.telegram import TelegramEventObserver
from .filters import BUILTIN_FILTERS

INTERNAL_UPDATE_TYPES = frozenset({"update", "error"})


class Router:
    """
    Router can route update, and it nested update types like messages, callback query,
    polls and all other event types.

    Event handlers can be registered in observer by two ways:

    - By observer method - :obj:`router.<event_type>.register(handler, <filters, ...>)`
    - By decorator - :obj:`@router.<event_type>(<filters, ...>)`
    """

    def __init__(self, use_builtin_filters: bool = True, name: Optional[str] = None) -> None:
        """

        :param use_builtin_filters: `aiogram` has many builtin filters and you can controll automatic registration of this filters in factory
        :param name: Optional router name, can be useful for debugging
        """

        self.use_builtin_filters = use_builtin_filters
        self.name = name or hex(id(self))

        self._parent_router: Optional[Router] = None
        self.sub_routers: List[Router] = []

        # Observers
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
        self.my_chat_member = TelegramEventObserver(router=self, event_name="my_chat_member")
        self.chat_member = TelegramEventObserver(router=self, event_name="chat_member")
        self.chat_join_request = TelegramEventObserver(router=self, event_name="chat_join_request")

        self.errors = TelegramEventObserver(router=self, event_name="error")

        self.startup = EventObserver()
        self.shutdown = EventObserver()

        self.observers: Dict[str, TelegramEventObserver] = {
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
            "my_chat_member": self.my_chat_member,
            "chat_member": self.chat_member,
            "chat_join_request": self.chat_join_request,
            "error": self.errors,
        }

        # Builtin filters
        if use_builtin_filters:
            for name, observer in self.observers.items():
                for builtin_filter in BUILTIN_FILTERS.get(name, ()):
                    observer.bind_filter(builtin_filter)

    def __str__(self) -> str:
        return f"{type(self).__name__} {self.name!r}"

    def __repr__(self) -> str:
        return f"<{self}>"

    def resolve_used_update_types(self, skip_events: Optional[Set[str]] = None) -> List[str]:
        """
        Resolve registered event names

        Is useful for getting updates only for registered event types.

        :param skip_events: skip specified event names
        :return: set of registered names
        """
        handlers_in_use: Set[str] = set()
        if skip_events is None:
            skip_events = set()
        skip_events = {*skip_events, *INTERNAL_UPDATE_TYPES}

        for router in self.chain_tail:
            for update_name, observer in router.observers.items():
                if observer.handlers and update_name not in skip_events:
                    handlers_in_use.add(update_name)

        return list(sorted(handlers_in_use))

    async def propagate_event(self, update_type: str, event: TelegramObject, **kwargs: Any) -> Any:
        kwargs.update(event_router=self)
        observer = self.observers[update_type]

        async def _wrapped(telegram_event: TelegramObject, **data: Any) -> Any:
            return await self._propagate_event(
                observer=observer, update_type=update_type, event=telegram_event, **data
            )

        return await observer.wrap_outer_middleware(_wrapped, event=event, data=kwargs)

    async def _propagate_event(
        self,
        observer: TelegramEventObserver,
        update_type: str,
        event: TelegramObject,
        **kwargs: Any,
    ) -> Any:
        response = await observer.trigger(event, **kwargs)
        if response is REJECTED:
            return UNHANDLED
        if response is not UNHANDLED:
            return response

        for router in self.sub_routers:
            response = await router.propagate_event(update_type=update_type, event=event, **kwargs)
            if response is not UNHANDLED:
                break

        return response

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
            raise ValueError(f"router should be instance of Router not {type(router).__name__!r}")
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
                    f"{type(self).__name__}(use_builtin_filters=False) has no effect"
                    f" for router {self} in due to builtin filters is already registered"
                    f" in parent router",
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
