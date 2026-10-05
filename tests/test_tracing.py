from aiogram.tracer import (
    AbstractTracer,
    tracer,
    TracerProxy,
    SpanProxy,
    safe_span_manager,
    execute_with_tracing,
)
from unittest.mock import MagicMock, AsyncMock, call
from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram import Router, Dispatcher, Bot
from aiogram.types import TelegramObject
import pytest
from dataclasses import dataclass
from tests.test_dispatcher.test_dispatcher import UPDATE


@dataclass
class Spans:
    handler: AsyncMock
    middleware: AsyncMock
    trigger: AsyncMock
    filter: AsyncMock


@pytest.fixture
def spans():
    return Spans(
        handler=AsyncMock(),
        middleware=AsyncMock(),
        trigger=AsyncMock(),
        filter=AsyncMock(),
    )


@pytest.fixture
def handler():
    return AsyncMock(spec=lambda event, **kwargs: None)


@pytest.fixture
def test_filter():
    return MagicMock(side_effect=lambda event, **kwargs: True)


@pytest.fixture(autouse=True)
def tracer_impl(spans: Spans):
    tracer_instance = MagicMock(spec=AbstractTracer)
    tracer_instance.get_handler_span_manager.return_value = spans.handler
    tracer_instance.get_middleware_span_manager.return_value = spans.middleware
    tracer_instance.get_trigger_span_manager.return_value = spans.trigger
    tracer_instance.get_filter_span_manager.return_value = spans.filter
    yield tracer_instance


@pytest.fixture
def observer(handler, test_filter):
    router = Router()
    router.message.register(handler, test_filter)
    return router.message


@pytest.fixture(autouse=True)
def inner_middleware(observer: TelegramEventObserver):
    inner = MagicMock(side_effect=lambda middleware, event, data: middleware(event, data))
    observer.middleware.register(inner)
    return inner


@pytest.fixture(autouse=True)
def outer_middleware(observer: TelegramEventObserver):
    outer = MagicMock(side_effect=lambda middleware, event, data: middleware(event, data))
    observer.outer_middleware.register(outer)
    return outer


class TestProxy:
    async def test_exception_on_span_entering(self, caplog):
        span = AsyncMock()
        span.__aenter__.side_effect = Exception("Test exception")
        async with SpanProxy(span):
            pass
        assert "Exception during entering span" in caplog.text
        span.__aexit__.assert_not_awaited()

    async def test_exception_on_span_exiting(self, caplog):
        span = AsyncMock()
        span.__aexit__.side_effect = Exception("Test exception")
        async with SpanProxy(span):
            pass
        assert "Exception during exiting span" in caplog.text

    def test_safe_span_manager(self, caplog):
        def span_getter():
            raise Exception("Test exception")

        result = safe_span_manager("test")(span_getter)()
        assert result is None
        assert "Exception during initialization of test span manager" in caplog.text

    async def test_exception_in_span_context_manager_not_suppressed(self):
        span = AsyncMock()
        with pytest.raises(Exception, match="Test exception"):
            async with SpanProxy(span):
                raise Exception("Test exception")
        span.__aenter__.assert_awaited_once()
        span.__aexit__.assert_awaited_once()

    @pytest.mark.parametrize(
        "method_name",
        [f"get_{name}_span_manager" for name in ("middleware", "trigger", "filter", "handler")],
    )
    async def test_proxy_delegates_to_tracer(self, method_name, tracer_impl):
        mocked_object = MagicMock()
        getattr(TracerProxy(tracer_impl), method_name)(mocked_object)
        getattr(tracer_impl, method_name).assert_called_once_with(mocked_object)

    async def test_execute_with_tracing(self):
        coro1 = AsyncMock(return_value="test")
        span = MagicMock()
        result = await execute_with_tracing(span, coro1())
        assert result == "test"
        coro1.assert_awaited_once()
        span.__aenter__.assert_awaited_once()
        span.__aexit__.assert_awaited_once()

        coro2 = AsyncMock()
        result = await execute_with_tracing(None, coro2())
        coro2.assert_awaited_once()


class TestArgumentPassing:
    @pytest.fixture(autouse=True)
    def set_tracer_var(self, tracer_impl):
        token = tracer.set(TracerProxy(tracer_impl))
        yield
        tracer.reset(token)

    @pytest.fixture
    def trigger(self, observer: TelegramEventObserver):
        async def _trigger():
            await observer.router.propagate_event("message", MagicMock(spec=TelegramObject))

        return _trigger

    async def test_handler_argument_passing(self, handler, tracer_impl, trigger, spans):
        await trigger()
        tracer_impl.get_handler_span_manager.assert_called_once()
        assert tracer_impl.get_handler_span_manager.call_args[0][0].callback is handler
        spans.handler.__aenter__.assert_awaited_once()
        spans.handler.__aexit__.assert_awaited_once()

    async def test_middleware_await_order(
        self, tracer_impl, trigger, inner_middleware, outer_middleware
    ):
        await trigger()
        assert tracer_impl.get_middleware_span_manager.call_args_list == [
            call(outer_middleware),
            call(inner_middleware),
        ]

    async def test_filter_argument_passing(self, tracer_impl, trigger, observer, test_filter):
        some_other_filter = lambda event, **kwargs: True
        observer.register(lambda event: None, some_other_filter)
        await trigger()
        assert (
            tracer_impl.get_filter_span_manager.call_args[0][0].filters[0].callback is test_filter
        )


class TestIntegration:
    @pytest.fixture
    def dp(self, tracer_impl):
        return Dispatcher(tracer=tracer_impl)

    @pytest.fixture
    def trigger(self, observer: TelegramEventObserver, dp: Dispatcher):
        dp.include_router(observer.router)

        async def _trigger():
            await dp.feed_update(Bot(token="42:TEST"), UPDATE)

        return _trigger

    @pytest.mark.parametrize(
        "method_name",
        [f"get_{name}_span_manager" for name in ("middleware", "trigger", "filter", "handler")],
    )
    async def test_handle_if_span_manager_is_none(self, tracer_impl, trigger, method_name):
        getattr(tracer_impl, method_name).return_value = None
        await trigger()
        getattr(tracer_impl, method_name).assert_called()

    async def test_trigger_span_opens_once_in_few_routers(
        self, tracer_impl, spans, dp: Dispatcher, trigger
    ):
        dp.message.register(lambda message: True)
        for _ in range(3):
            router = Router()
            router.message.register(lambda message: True)
            dp.include_router(router)
        await trigger()
        tracer_impl.get_trigger_span_manager.assert_called_once()
        assert (
            tracer_impl.get_trigger_span_manager.call_args[0][0].model_dump()
            == UPDATE.event.model_dump()
        )
        spans.trigger.__aenter__.assert_awaited_once()
        spans.trigger.__aexit__.assert_awaited_once()
