import datetime
import itertools
from contextvars import ContextVar
from typing import Any

import pytest

from aiogram import Dispatcher, F, Router
from aiogram.dispatcher.event.bases import UNHANDLED, SkipHandler
from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.dispatcher.table import (
    _EVENT_FIELDS,
    compile_plan,
    compile_table,
    execute,
    routing_keys,
)
from aiogram.types import CallbackQuery, Chat, Message, Update, User
from aiogram.types.update import UpdateTypeLookupError
from tests.mocked_bot import MockedBot

USER = User(id=42, is_bot=False, first_name="Test")
CHAT = Chat(id=42, type="private")


def message(text: str | None = "hello", **kwargs: Any) -> Message:
    return Message(
        message_id=1, date=datetime.datetime.now(), chat=CHAT, from_user=USER, text=text, **kwargs
    )


def update(text: str | None = "hello", **kwargs: Any) -> Update:
    return Update(update_id=1, message=message(text, **kwargs))


def recorder(log: list[Any], name: str, *, result: Any = None):
    async def handler(event: Any, **data: Any) -> Any:
        log.append((name, dict(data)))
        return result if result is not None else name

    return handler


def outer(log: list[Any], name: str):
    async def middleware(handler, event, data):
        log.append(name)
        return await handler(event, data)

    return middleware


class TestR09Scopes:
    """The three probes of codex-review §11 and the scope rules around them."""

    async def test_failed_candidate_leaves_no_filter_data(self, bot: MockedBot):
        dp, log = Dispatcher(), []
        dp.message.register(recorder(log, "first"), lambda m: {"db": 1}, lambda m: False)
        dp.message.register(recorder(log, "second"))

        assert await dp.feed_update(bot, update()) == "second"
        assert "db" not in log[0][1]

    async def test_passed_candidate_then_skip_keeps_filter_data(self, bot: MockedBot):
        dp, log = Dispatcher(), []

        async def skipping(message: Message) -> None:
            raise SkipHandler

        dp.message.register(skipping, lambda m: {"db": 1})
        dp.message.register(recorder(log, "second"))

        assert await dp.feed_update(bot, update()) == "second"
        assert log[0][1]["db"] == 1

    async def test_inner_middleware_write_then_skip_survives(self, bot: MockedBot):
        dp, log = Dispatcher(), []

        @dp.message.middleware()
        async def writer(handler, event, data):
            data.setdefault("writes", []).append(data["handler"].callback.__name__)
            return await handler(event, data)

        async def skipping(message: Message) -> None:
            raise SkipHandler

        dp.message.register(skipping)
        dp.message.register(recorder(log, "second"))

        assert await dp.feed_update(bot, update()) == "second"
        assert log[0][1]["writes"] == ["skipping", "handler"]

    async def test_filter_dicts_merge_in_order_and_later_filters_see_them(self, bot: MockedBot):
        dp, log = Dispatcher(), []
        dp.message.register(
            recorder(log, "h"),
            lambda m: {"a": 1, "b": 1},
            lambda m, a: a == 1 and {"b": 2},
        )

        await dp.feed_update(bot, update())
        assert (log[0][1]["a"], log[0][1]["b"]) == (1, 2)

    async def test_sibling_router_does_not_see_trigger_data(self, bot: MockedBot):
        dp, r1, r2, log = Dispatcher(), Router(name="r1"), Router(name="r2"), []
        dp.include_routers(r1, r2)

        @r1.message.middleware()
        async def writer(handler, event, data):
            data["inner"] = True
            return await handler(event, data)

        async def skipping(message: Message) -> None:
            raise SkipHandler

        r1.message.register(skipping, lambda m: {"db": 1})
        r2.message.register(recorder(log, "r2"))

        assert await dp.feed_update(bot, update()) == "r2"
        data = log[0][1]
        assert "db" not in data
        assert "inner" not in data
        assert data["event_router"] is r2

    async def test_root_filter_data_reaches_children(self, bot: MockedBot):
        dp, child, log = Dispatcher(), Router(), []
        dp.include_router(child)
        dp.message.filter(lambda m: {"root": 1})
        child.message.register(recorder(log, "child"))

        assert await dp.feed_update(bot, update()) == "child"
        assert log[0][1]["root"] == 1

    async def test_failing_root_filter_skips_children(self, bot: MockedBot):
        dp, child = Dispatcher(), Router()
        dp.include_router(child)
        dp.message.filter(lambda m: False)
        child.message.register(recorder([], "child"))

        assert await dp.feed_update(bot, update()) is UNHANDLED

    async def test_outer_middleware_data_is_a_copy_past_the_chain(self, bot: MockedBot):
        dp, seen = Dispatcher(), {}
        dp.message.filter(lambda m: {"root": 1})

        @dp.message.outer_middleware()
        async def keeper(handler, event, data):
            result = await handler(event, data)
            seen.update(data)
            return result

        dp.message.register(recorder([], "h"), lambda m: {"filtered": 1})

        assert await dp.feed_update(bot, update()) == "h"
        assert seen["event_router"] is dp
        assert "root" not in seen
        assert "filtered" not in seen
        assert "handler" in seen  # the dp.update handler (the routing stage), as in 3.x

    async def test_nested_mutable_values_are_shared(self, bot: MockedBot):
        dp, log = Dispatcher(), []
        shared: list[str] = []

        async def skipping(message: Message, bag: list[str]) -> None:
            bag.append("first")
            raise SkipHandler

        dp.message.register(skipping, lambda m: {"bag": shared})
        dp.message.register(recorder(log, "second"), lambda m: False)

        assert await dp.feed_update(bot, update()) is UNHANDLED
        assert shared == ["first"]


class TestD111:
    async def test_outer_middleware_without_handler_is_skipped(self, bot: MockedBot):
        dp, empty, full, log = Dispatcher(), Router(), Router(), []
        dp.include_routers(empty, full)
        empty.message.outer_middleware(outer(log, "empty"))
        empty.callback_query.register(recorder([], "cb"))
        full.message.outer_middleware(outer(log, "full"))
        full.message.register(recorder([], "h"))

        assert await dp.feed_update(bot, update()) == "h"
        assert log == ["full"]

    async def test_outer_middleware_runs_when_filters_then_fail(self, bot: MockedBot):
        dp, log = Dispatcher(), []
        dp.message.outer_middleware(outer(log, "dp"))
        dp.message.register(recorder([], "h"), lambda m: False)

        assert await dp.feed_update(bot, update()) is UNHANDLED
        assert log == ["dp"]

    async def test_parent_outer_middleware_surrounds_children(self, bot: MockedBot):
        dp, child, log = Dispatcher(), Router(), []
        dp.include_router(child)

        @dp.message.outer_middleware()
        async def around(handler, event, data):
            log.append("enter")
            result = await handler(event, data)
            log.append("exit")
            return result

        async def handler(message: Message) -> str:
            log.append("handler")
            return "ok"

        child.message.register(handler)

        assert await dp.feed_update(bot, update()) == "ok"
        assert log == ["enter", "handler", "exit"]

    async def test_no_handler_anywhere_is_unhandled(self, bot: MockedBot):
        dp, log = Dispatcher(), []
        dp.message.outer_middleware(outer(log, "dp"))

        assert await dp.feed_update(bot, update()) is UNHANDLED
        assert log == []

    async def test_short_circuit_stops_propagation(self, bot: MockedBot):
        dp, r1, r2 = Dispatcher(), Router(), Router()
        dp.include_routers(r1, r2)

        @r1.message.outer_middleware()
        async def stop(handler, event, data):
            return "stopped"

        r1.message.register(recorder([], "r1"))
        r2.message.register(recorder([], "r2"))

        assert await dp.feed_update(bot, update()) == "stopped"

    async def test_continuation_called_twice(self, bot: MockedBot):
        dp, log = Dispatcher(), []

        @dp.message.outer_middleware()
        async def twice(handler, event, data):
            await handler(event, data)
            return await handler(event, data)

        dp.message.register(recorder(log, "h"))

        assert await dp.feed_update(bot, update()) == "h"
        assert len(log) == 2

    async def test_error_plan_uses_the_same_rule(self, bot: MockedBot):
        dp, child, log = Dispatcher(), Router(), []
        dp.include_router(child)
        child.errors.outer_middleware(outer(log, "child-errors"))
        dp.errors.register(recorder([], "on_error"))

        @dp.message()
        async def boom(message: Message) -> None:
            raise ValueError

        assert await dp.feed_update(bot, update()) == "on_error"
        assert log == []


class TestUpdateLevel:
    async def test_dp_update_root_filter(self, bot: MockedBot):
        dp, log = Dispatcher(), []
        dp.update.filter(lambda u: False)
        dp.message.register(recorder(log, "h"))

        assert await dp.feed_update(bot, update()) is UNHANDLED
        assert log == []

    async def test_dp_update_root_filter_data(self, bot: MockedBot):
        dp, log = Dispatcher(), []
        dp.update.filter(lambda u: {"from_update": 1})
        dp.message.register(recorder(log, "h"))

        assert await dp.feed_update(bot, update()) == "h"
        assert log[0][1]["from_update"] == 1

    async def test_user_update_handler_after_unknown_type(self, bot: MockedBot):
        dp = Dispatcher()
        dp.update.register(recorder([], "fallback"))

        with pytest.warns(RuntimeWarning, match="Detected unknown update type"):
            assert await dp.feed_update(bot, Update(update_id=1)) == "fallback"

    async def test_update_without_handlers(self, bot: MockedBot):
        dp = Dispatcher()
        dp.update.handlers.clear()

        assert await dp.feed_update(bot, update()) is UNHANDLED

    async def test_update_scope(self, bot: MockedBot):
        dp, log = Dispatcher(flag="workflow"), []
        dp.message.register(recorder(log, "h"))

        await dp.feed_update(bot, update(), extra=1)
        data = log[0][1]
        assert data["dispatcher"] is dp
        assert data["bot"] is bot
        assert (data["flag"], data["extra"]) == ("workflow", 1)
        assert data["event_update"].update_id == 1

    async def test_precompiled_table_is_used(self, bot: MockedBot):
        dp = Dispatcher()
        dp.message.register(recorder([], "old"))
        dp._table = compile_table(dp)
        dp.message.handlers.clear()

        assert await dp.feed_update(bot, update()) == "old"

    async def test_overridden_listen_update_still_runs(self, bot: MockedBot):
        class MyDispatcher(Dispatcher):
            async def _listen_update(self, update: Update, **kwargs: Any) -> Any:
                return "custom"

        assert await MyDispatcher().feed_update(bot, update()) == "custom"

    async def test_another_dispatchers_listener_is_not_replaced(self, bot: MockedBot):
        dp, child = Dispatcher(), Dispatcher()
        dp.update.handlers.clear()
        dp.update.register(child._listen_update)
        child.message.register(recorder([], "child"))

        assert await dp.feed_update(bot, update()) == "child"

    async def test_execute(self, bot: MockedBot):
        dp = Dispatcher()
        dp.message.register(recorder([], "h"))

        assert await execute(compile_table(dp), bot, update(), {}) == "h"


request_locale: ContextVar[str | None] = ContextVar("request_locale", default=None)


class TestHandlerResultHook:
    async def test_hook_sees_value_inside_middleware_scope(self, bot: MockedBot):
        dp, seen = Dispatcher(), []

        @dp.message.outer_middleware()
        async def locale(handler, event, data):
            token = request_locale.set("uk")
            try:
                return await handler(event, data)
            finally:
                request_locale.reset(token)

        def hook(value: Any, data: dict[str, Any]) -> Any:
            seen.append((value, request_locale.get(), data["handler"].callback.__name__))
            return f"{value}!"

        async def skipping(message: Message) -> None:
            raise SkipHandler

        async def answer(message: Message) -> str:
            return "hi"

        dp.message.register(skipping)
        dp.message.register(answer)
        dp._on_handler_result = hook

        assert await dp.feed_update(bot, update()) == "hi!"
        assert seen == [("hi", "uk", "answer")]

    async def test_hook_through_propagate_event_uses_the_root(self):
        dp, child, seen = Dispatcher(), Router(), []
        dp.include_router(child)
        child.message.register(recorder([], "h"))
        dp._on_handler_result = lambda value, data: seen.append(value) or value

        assert await child.propagate_event("message", message()) == "h"
        assert seen == ["h"]

    async def test_user_update_handler_gets_the_hook(self, bot: MockedBot):
        dp, seen = Dispatcher(), []
        dp.update.register(recorder([], "fallback"))
        dp._on_handler_result = lambda value, data: seen.append(value) or value

        with pytest.warns(RuntimeWarning):
            await dp.feed_update(bot, Update(update_id=1))
        assert seen == ["fallback"]


class TestCompile:
    def test_frames_are_dfs_and_pruned(self):
        dp = Dispatcher()
        r1, r1a, r1b, r2 = Router(name="r1"), Router(name="r1a"), Router(name="r1b"), Router()
        dp.include_routers(r1, r2)
        r1.include_routers(r1a, r1b)
        h = recorder([], "h")
        dp.message.register(h)
        r1a.message.register(h)
        r1a.message.register(h)
        r1b.message.register(h)
        r2.callback_query.register(h)

        plan = compile_plan(dp, "message")
        assert [frame.router for frame in plan.frames] == [dp, r1, r1a, r1b]
        assert [frame.span for frame in plan.frames] == [
            range(0, 1),
            range(1, 1),
            range(1, 3),
            range(3, 4),
        ]
        assert plan.frames[1].children == (plan.frames[2], plan.frames[3])
        assert plan.frames[2].parent is plan.frames[1]
        assert [c.router for c in plan.candidates] == [dp, r1a, r1a, r1b]
        assert compile_plan(r2, "message") is None

        table = compile_table(dp)
        assert sorted(table.by_event) == ["callback_query", "message"]
        assert table.outer_chain is table.update.outer

    async def test_custom_event_type(self):
        r1, r2 = Router(), Router()
        r1.include_router(r2)
        r2.observers["custom"] = TelegramEventObserver(r2, event_name="custom")
        r2.observers["custom"].register(recorder([], "custom"))

        assert await r1.propagate_event("custom", None) == "custom"
        plan = compile_plan(r1, "custom")
        assert plan.frames[0].root_filters == ()
        assert plan.frames[0].candidates == ()

    async def test_inner_middlewares_come_from_real_parents(self):
        parent, child, log = Router(), Router(), []
        parent.include_router(child)

        @parent.message.middleware()
        async def inherited(handler, event, data):
            log.append("parent-inner")
            return await handler(event, data)

        child.message.register(recorder([], "h"))

        assert await child.propagate_event("message", message()) == "h"
        assert log == ["parent-inner"]


class TestCallEvent:
    async def test_sync_filter_and_handler_run(self, bot: MockedBot):
        dp = Dispatcher()

        def sync_handler(message: Message) -> str:
            return "sync"

        dp.message.register(sync_handler, F.text == "hello")
        assert await dp.feed_update(bot, update()) == "sync"

    async def test_awaitable_filter_result_is_rejected(self, bot: MockedBot):
        dp = Dispatcher()

        async def coro() -> bool:
            return True

        dp.message.register(recorder([], "h"), lambda m: coro())
        with pytest.raises(TypeError, match="returned an awaitable"):
            await dp.feed_update(bot, update())


class TestRoutingKeys:
    def test_every_event_field_is_known(self):
        assert set(_EVENT_FIELDS) == set(Update.model_fields) - {"update_id"}

    @pytest.mark.parametrize("pair", itertools.combinations(_EVENT_FIELDS, 2))
    def test_priority_matches_event_type(self, pair):
        marker = message()
        fabricated = Update.model_construct(update_id=1, **dict.fromkeys(pair, marker))
        assert routing_keys(fabricated).event_type == fabricated.event_type

    @pytest.mark.parametrize("name", _EVENT_FIELDS)
    def test_single_field(self, name):
        marker = message()
        fabricated = Update.model_construct(update_id=1, **{name: marker})
        keys = routing_keys(fabricated)
        assert (keys.event_type, keys.event) == (name, marker)

    def test_unknown(self):
        with pytest.raises(UpdateTypeLookupError):
            routing_keys(Update(update_id=1))
        with pytest.raises(UpdateTypeLookupError):
            routing_keys(Update(update_id=1, message=None))

    def test_message_keys(self):
        keys = routing_keys(update("/start@bot arg1 arg2"))
        assert keys.text == "/start@bot arg1 arg2"
        assert keys.command is not None
        assert (keys.command.prefix, keys.command.command) == ("/", "start")
        assert (keys.command.mention, keys.command.args) == ("bot", "arg1 arg2")
        assert keys.chat_type == "private"
        assert keys.content_kind == "text"
        assert keys.callback_data is None

    def test_caption_and_blank_text(self):
        assert routing_keys(update(None, caption="/help")).command.command == "help"
        assert routing_keys(update("\x1c\x1f")).command is None
        assert routing_keys(update(None)).command is None

    def test_callback_query_keys(self):
        query = CallbackQuery(id="1", from_user=USER, chat_instance="c", data="payload")
        keys = routing_keys(Update(update_id=1, callback_query=query))
        assert keys.callback_data == "payload"
        assert keys.text is None
        assert keys.chat_type is None
        assert keys.content_kind is None
