import asyncio
from functools import partial
from unittest.mock import AsyncMock, patch

import pytest

from aiogram.client.session import RequestContext
from aiogram.client.session.middlewares import manager as manager_module
from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.client.session.middlewares.manager import RequestMiddlewareManager
from aiogram.methods import GetMe
from tests.mocked_bot import MockedBot, bot_full_info

ME = bot_full_info()


class Recorder(BaseRequestMiddleware):
    def __init__(self, log: list[str], name: str | None = None) -> None:
        self.log = log
        self.name = name or type(self).__name__

    async def __call__(self, ctx):
        self.log.append(self.name)
        return await ctx.next()


class Retry(Recorder):
    pass


class RateLimit(Recorder):
    pass


class Span(Recorder):
    pass


def names(manager: RequestMiddlewareManager) -> list[str]:
    return [m.name for m in manager]


class TestRegister:
    def test_register_unregister(self):
        manager = RequestMiddlewareManager()

        @manager
        async def middleware(ctx):
            return await ctx.next()

        assert list(manager) == [middleware]
        assert manager[0] is middleware
        assert manager[:] == [middleware]
        manager.unregister(middleware)
        assert not manager

    def test_unregister_missing(self):
        with pytest.raises(ValueError, match="Recorder is not registered"):
            RequestMiddlewareManager().unregister(Recorder([]))

    def test_decorator_with_anchor(self):
        manager = RequestMiddlewareManager()
        manager.register(Recorder([], "a"))

        @manager(before=Recorder)
        async def outer(ctx):
            return await ctx.next()

        assert manager[0] is outer

    def test_wrong_signature(self):
        async def two(ctx, extra):
            pass

        async def star(*args):
            pass

        for middleware in (two, star, print, object()):
            with pytest.raises(TypeError, match="must take one positional argument"):
                RequestMiddlewareManager().register(middleware)


class TestOrder:
    def test_registration_order(self):
        manager = RequestMiddlewareManager()
        for name in "abc":
            manager.register(Recorder([], name))
        assert names(manager) == ["a", "b", "c"]

    def test_before_places_outside(self):
        manager = RequestMiddlewareManager()
        manager.register(Retry([], "a"))
        manager.register(Recorder([], "b"), before=Retry)
        assert names(manager) == ["b", "a"]

    def test_after_by_instance(self):
        manager = RequestMiddlewareManager()
        first = Recorder([], "a")
        manager.register(Recorder([], "x"), after=first)  # anchor registered later
        manager.register(first)
        manager.register(Recorder([], "b"))
        assert names(manager) == ["a", "x", "b"]

    def test_class_anchor_first_match_and_subclass(self):
        class SubRetry(Retry):
            pass

        manager = RequestMiddlewareManager()
        manager.register(Recorder([], "a"))
        manager.register(SubRetry([], "r1"))
        manager.register(Retry([], "r2"))
        manager.register(Recorder([], "x"), before=Retry)
        assert names(manager) == ["a", "x", "r1", "r2"]

    @pytest.mark.parametrize("retry_first", [True, False])
    def test_retry_ratelimit_span(self, retry_first: bool):
        manager = RequestMiddlewareManager()
        if retry_first:
            manager.register(Retry([]))
            manager.register(Span([]))
            manager.register(RateLimit([]), after=Retry, before=Span)
        else:
            manager.register(Span([]))
            manager.register(RateLimit([]), before=Span)
            manager.register(Retry([]), before=RateLimit)
        assert names(manager) == ["Retry", "RateLimit", "Span"]

    async def test_missing_anchor_raises_at_next_call(self, bot: MockedBot):
        class Missing:
            pass

        bot.session.middleware.register(Recorder([]), after=Missing)  # no error here
        with pytest.raises(
            ValueError, match=r"Recorder is anchored after=.*Missing, which is not"
        ):
            await bot.get_me()
        with pytest.raises(ValueError, match="Missing"):
            await bot.get_me()  # still broken: nothing cached on failure

    def test_self_anchor_is_missing(self):
        manager = RequestMiddlewareManager()
        middleware = Recorder([])
        manager.register(middleware, before=middleware)
        with pytest.raises(ValueError, match="not registered"):
            list(manager)

    def test_cycle(self):
        manager = RequestMiddlewareManager()
        manager.register(Recorder([], "free"))
        manager.register(Retry([]), after=RateLimit)
        manager.register(RateLimit([]), after=Span)
        manager.register(Span([]), after=Retry)
        manager.register(Recorder([], "downstream"), after=Span)
        with pytest.raises(ValueError, match="form a cycle: Span -> RateLimit -> Retry -> Span"):
            manager.chain


class TestCache:
    async def test_chain_resolved_once(self, bot: MockedBot):
        log: list[str] = []
        bot.session.middleware.register(Recorder(log, "a"))
        with patch.object(manager_module, "_resolve", wraps=manager_module._resolve) as resolve:
            for _ in range(3):
                bot.add_result_for(GetMe, ok=True, result=ME)
                await bot.get_me()
            assert resolve.call_count == 1

            later = Recorder(log, "b")
            bot.session.middleware.register(later, before=Recorder)
            bot.add_result_for(GetMe, ok=True, result=ME)
            await bot.get_me()
            assert resolve.call_count == 2

            bot.session.middleware.unregister(later)
            bot.add_result_for(GetMe, ok=True, result=ME)
            await bot.get_me()
            assert resolve.call_count == 3
        assert log == ["a", "a", "a", "b", "a", "a"]


class TestContext:
    async def test_fields_and_timeout(self, bot: MockedBot):
        seen: list[RequestContext] = []

        @bot.session.middleware
        async def middleware(ctx):
            seen.append(ctx)
            ctx.timeout = 7
            return await ctx.next()

        with patch.object(bot.session, "make_request", AsyncMock(return_value=ME)) as request:
            assert await bot(GetMe(), request_timeout=3) is ME
        (ctx,) = seen
        assert ctx.bot is bot
        assert isinstance(ctx.method, GetMe)
        assert ctx.attempt == 1
        request.assert_awaited_once_with(bot, ctx.method, timeout=7)

    async def test_attempt_and_retry(self, bot: MockedBot):
        attempts: list[int] = []

        async def retry(ctx):
            for attempt in (1, 2):
                ctx.attempt = attempt
                result = await ctx.next()
            return result

        async def inner(ctx):
            attempts.append(ctx.attempt)
            return await ctx.next()

        bot.session.middleware.register(inner)
        bot.add_result_for(GetMe, ok=True, result=ME)
        await bot.get_me()
        assert attempts == [1]

        bot.session.middleware.register(retry, before=inner)
        bot.add_result_for(GetMe, ok=True, result=ME)
        bot.add_result_for(GetMe, ok=True, result=ME)
        await bot.get_me()
        assert attempts == [1, 1, 2]

    async def test_concurrent_calls_independent(self, bot: MockedBot):
        both_inside = asyncio.Event()
        inside = 0
        seen: list[tuple[int, int]] = []

        async def outer(ctx):
            nonlocal inside
            ctx.attempt = ctx.timeout
            inside += 1
            if inside == 2:
                both_inside.set()
            await both_inside.wait()
            return await ctx.next()

        async def inner(ctx):
            seen.append((ctx.timeout, ctx.attempt))
            return await ctx.next()

        bot.session.middleware.register(outer)
        bot.session.middleware.register(inner)
        bot.add_result_for(GetMe, ok=True, result=ME)
        bot.add_result_for(GetMe, ok=True, result=ME)
        await asyncio.gather(bot(GetMe(), request_timeout=5), bot(GetMe(), request_timeout=9))
        assert sorted(seen) == [(5, 5), (9, 9)]

    async def test_replaced_method_reaches_request(self, bot: MockedBot):
        replacement = GetMe()

        @bot.session.middleware
        async def middleware(ctx):
            ctx.method = replacement
            return await ctx.next()

        with patch.object(bot.session, "make_request", AsyncMock(return_value=ME)) as request:
            await bot.get_me()
        assert request.await_args.args[1] is replacement


class TestLegacy:
    async def test_3x_middleware_runs_with_warning(self, bot: MockedBot):
        log: list[str] = []
        replacement = GetMe()

        class Legacy(BaseRequestMiddleware):
            async def __call__(self, make_request, bot, method):  # type: ignore[override]
                log.append(type(method).__name__)
                return await make_request(bot, replacement)

        async def legacy_fn(make_request, bot, method, extra=None):
            log.append("fn")
            return await make_request(bot, method)

        async def modern(ctx, extra=None):
            assert ctx.method is replacement
            return await ctx.next()

        with pytest.warns(DeprecationWarning, match="Legacy takes the 3.x arguments"):
            bot.session.middleware(Legacy())
        with pytest.warns(DeprecationWarning, match="legacy_fn takes the 3.x arguments"):
            bot.session.middleware(legacy_fn)
        bot.session.middleware(partial(modern, extra=1))

        with patch.object(bot.session, "make_request", AsyncMock(return_value=ME)) as request:
            assert await bot.get_me() is ME
        assert log == ["GetMe", "fn"]
        assert request.await_args.args[1] is replacement

    def test_warning_points_at_the_caller(self):
        async def legacy(make_request, bot, method):
            return await make_request(bot, method)

        manager = RequestMiddlewareManager()
        for register in (manager.register, manager, manager()):
            with pytest.warns(DeprecationWarning, match="AG4062") as record:
                register(legacy)
            assert record[0].filename == __file__

    async def test_concurrent_make_request_each_runs_the_inner_chain(self, bot: MockedBot):
        seen: list[str] = []

        async def fan(make_request, bot, method):
            first, _ = await asyncio.gather(make_request(bot, GetMe()), make_request(bot, GetMe()))
            return first

        async def inner(ctx):
            seen.append(type(ctx.method).__name__)
            await asyncio.sleep(0)
            return await ctx.next()

        with pytest.warns(DeprecationWarning, match="AG4062"):
            bot.session.middleware(fan)
        bot.session.middleware(inner)
        with patch.object(bot.session, "make_request", AsyncMock(return_value=ME)) as request:
            await bot.get_me()
        assert seen == ["GetMe", "GetMe"]
        assert request.await_count == 2

    async def test_rewrite_does_not_stack_on_retry(self, bot: MockedBot):
        sent: list[str] = []

        async def retry(ctx):
            await ctx.next()
            return await ctx.next()

        async def rewrite(make_request, bot, method):
            return await make_request(bot, method.model_copy(update={"text": method.text + "!"}))

        async def record(bot, method, timeout=None):
            sent.append(method.text)
            return ME

        bot.session.middleware(retry)
        with pytest.warns(DeprecationWarning, match="AG4062"):
            bot.session.middleware(rewrite)
        with patch.object(bot.session, "make_request", record):
            await bot.send_message(chat_id=1, text="hi")
        assert sent == ["hi!", "hi!"]
