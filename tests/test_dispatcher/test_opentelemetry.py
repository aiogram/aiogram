from datetime import datetime

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.util._once import Once  # noqa: PLC2701

from aiogram import Dispatcher, F
from aiogram.methods import SendMessage
from aiogram.types import Chat, Message, Update, User
from aiogram.utils.opentelemetry import (
    disable_telemetry,
    enable_telemetry,
    is_enabled,
)
from tests.mocked_bot import MockedBot


@pytest.fixture(autouse=True)
def setup_otel():
    # Reset OpenTelemetry global state to avoid "Overriding of current TracerProvider is not allowed"
    trace._TRACER_PROVIDER_SET_ONCE = Once()
    trace._TRACER_PROVIDER = None

    # Setup TracerProvider and InMemorySpanExporter
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    enable_telemetry()
    yield exporter
    disable_telemetry()


def find_span_by_suffix(spans, suffix):
    for s in spans:
        if s.name.endswith(suffix):
            return s
    names = [s.name for s in spans]
    raise ValueError(f"Span with suffix '{suffix}' not found in: {names}")


@pytest.mark.asyncio
async def test_opentelemetry_disabled(setup_otel):
    exporter = setup_otel
    disable_telemetry()
    assert not is_enabled()

    bot = MockedBot()
    dp = Dispatcher()

    @dp.message()
    async def handle_msg(message: Message):
        return "ok"

    chat = Chat(id=123, type="private")
    user = User(id=456, is_bot=False, first_name="User")
    message = Message(message_id=789, chat=chat, date=datetime.now(), from_user=user, text="hello")
    update = Update(update_id=1, message=message)

    await dp.feed_update(bot, update)

    spans = exporter.get_finished_spans()
    assert len(spans) == 0


@pytest.mark.asyncio
async def test_opentelemetry_hierarchy(setup_otel):
    exporter = setup_otel
    assert is_enabled()

    bot = MockedBot()
    bot.add_result_for(SendMessage, ok=True, result=None)

    dp = Dispatcher(name="test_dispatcher")

    # Define a custom middleware
    class CustomMiddleware:
        async def __call__(self, handler, event, data):
            return await handler(event, data)

    dp.message.outer_middleware(CustomMiddleware())

    # Handler with a filter
    @dp.message(F.text == "hello")
    async def handle_msg(message: Message):
        await bot.send_message(chat_id=message.chat.id, text="hi")
        return "handled"

    chat = Chat(id=123, type="private")
    user = User(id=456, is_bot=False, first_name="User")
    message = Message(message_id=789, chat=chat, date=datetime.now(), from_user=user, text="hello")
    update = Update(update_id=1, message=message)

    await dp.feed_update(bot, update)

    spans = exporter.get_finished_spans()

    update_span = find_span_by_suffix(spans, "aiogram.update.message")
    middleware_span = find_span_by_suffix(spans, "aiogram.middleware.CustomMiddleware")
    filter_span = find_span_by_suffix(spans, "aiogram.filter.MagicFilter")
    handler_span = find_span_by_suffix(spans, "handle_msg")
    api_span = find_span_by_suffix(spans, "telegram.api.sendMessage")

    # Verify they all belong to the same trace
    trace_id = update_span.context.trace_id
    for span in spans:
        assert span.context.trace_id == trace_id

    # Verify that api_span is a child of handler_span
    assert api_span.parent.span_id == handler_span.context.span_id

    # Verify attributes
    # Update Span attributes
    assert update_span.attributes["telegram.update.type"] == "message"
    assert update_span.attributes["telegram.user.id"] == 456
    assert update_span.attributes["telegram.chat.id"] == 123
    assert update_span.attributes["telegram.message.id"] == 789
    assert update_span.attributes["aiogram.router.name"] == "test_dispatcher"

    # Middleware Span attributes
    assert middleware_span.attributes["aiogram.middleware.name"] == "CustomMiddleware"
    assert middleware_span.attributes["aiogram.router.name"] == "test_dispatcher"

    # Filter Span attributes
    assert filter_span.attributes["aiogram.filter.name"] == "MagicFilter"
    assert filter_span.attributes["aiogram.router.name"] == "test_dispatcher"

    # Handler Span attributes
    assert handler_span.attributes["aiogram.handler.name"].endswith("handle_msg")
    assert handler_span.attributes["aiogram.router.name"] == "test_dispatcher"

    # Telegram API Span attributes
    assert api_span.attributes["telegram.api.method"] == "sendMessage"
    assert api_span.attributes["telegram.chat.id"] == 123


@pytest.mark.asyncio
async def test_opentelemetry_error_recording(setup_otel):
    exporter = setup_otel
    assert is_enabled()

    bot = MockedBot()
    dp = Dispatcher()

    @dp.message()
    async def handle_msg(message: Message):
        raise ValueError("Something went wrong")

    chat = Chat(id=123, type="private")
    user = User(id=456, is_bot=False, first_name="User")
    message = Message(message_id=789, chat=chat, date=datetime.now(), from_user=user, text="hello")
    update = Update(update_id=1, message=message)

    with pytest.raises(ValueError, match="Something went wrong"):
        await dp.feed_update(bot, update)

    spans = exporter.get_finished_spans()

    handler_span = find_span_by_suffix(spans, "handle_msg")

    # Verify span status and error recording
    assert not handler_span.status.is_ok
    assert "Something went wrong" in handler_span.status.description

    events = handler_span.events
    assert len(events) == 1
    assert events[0].name == "exception"
