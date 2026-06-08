from __future__ import annotations

import inspect
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager, suppress
from typing import Any

# Check if opentelemetry is installed
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode

    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False
    trace = None  # type: ignore
    Status = None  # type: ignore
    StatusCode = None  # type: ignore

_settings = {"enabled": False}


def is_enabled() -> bool:
    return HAS_OTEL and _settings["enabled"]


def enable_telemetry() -> None:
    _settings["enabled"] = True


def disable_telemetry() -> None:
    _settings["enabled"] = False


def get_callable_name(callback: Any) -> str:
    unwrapped = inspect.unwrap(callback)
    if hasattr(unwrapped, "__qualname__"):
        return str(unwrapped.__qualname__)
    if hasattr(unwrapped, "__name__"):
        return str(unwrapped.__name__)
    return str(unwrapped.__class__.__name__)


def extract_telemetry_attributes(event: Any, data: dict[str, Any]) -> dict[str, Any]:
    attributes: dict[str, Any] = {}

    # Try resolving event context via user_context keys if they exist in data
    from aiogram.dispatcher.middlewares.user_context import EVENT_CONTEXT_KEY

    if EVENT_CONTEXT_KEY in data:
        ctx = data[EVENT_CONTEXT_KEY]
        if ctx.user_id is not None:
            attributes["telegram.user.id"] = ctx.user_id
        if ctx.chat_id is not None:
            attributes["telegram.chat.id"] = ctx.chat_id
    else:
        # Fallback to direct event attributes
        if hasattr(event, "from_user") and event.from_user:
            attributes["telegram.user.id"] = event.from_user.id
        elif hasattr(event, "user") and event.user:
            attributes["telegram.user.id"] = event.user.id

        if hasattr(event, "chat") and event.chat:
            attributes["telegram.chat.id"] = event.chat.id

    # Get message ID
    if hasattr(event, "message_id"):
        attributes["telegram.message.id"] = event.message_id
    elif hasattr(event, "message") and event.message and hasattr(event.message, "message_id"):
        attributes["telegram.message.id"] = event.message.message_id

    return attributes


def _resolve_context_attributes(update: Any, attributes: dict[str, Any]) -> None:
    with suppress(Exception):
        from aiogram.dispatcher.middlewares.user_context import UserContextMiddleware

        event_context = UserContextMiddleware.resolve_event_context(update)
        if event_context.user_id is not None:
            attributes["telegram.user.id"] = event_context.user_id
        if event_context.chat_id is not None:
            attributes["telegram.chat.id"] = event_context.chat_id


def _resolve_message_id(update: Any, attributes: dict[str, Any]) -> None:
    with suppress(Exception):
        msg_id = None
        for attr in (
            "message",
            "edited_message",
            "channel_post",
            "edited_channel_post",
            "business_message",
            "edited_business_message",
        ):
            val = getattr(update, attr, None)
            if val is not None and hasattr(val, "message_id"):
                msg_id = val.message_id
                break
        if msg_id is None and update.callback_query and update.callback_query.message:
            msg_id = getattr(update.callback_query.message, "message_id", None)
        if msg_id is not None:
            attributes["telegram.message.id"] = msg_id


@contextmanager
def trace_update(update: Any, router: Any, kwargs: dict[str, Any]) -> Generator[Any, None, None]:
    if not HAS_OTEL:
        yield None
        return

    event_type = "update"
    with suppress(Exception):
        event_type = update.event_type

    span_name = f"aiogram.update.{event_type}"
    tracer = trace.get_tracer("aiogram")

    attributes = {
        "telegram.update.type": event_type,
        "aiogram.router.name": router.name,
    }

    _resolve_context_attributes(update, attributes)
    _resolve_message_id(update, attributes)

    with tracer.start_as_current_span(span_name, attributes=attributes) as span:
        yield span


def wrap_middleware_otel(m: Any) -> Any:
    if not HAS_OTEL:
        return m

    m_name = getattr(m, "__name__", m.__class__.__name__)
    if m_name == "__call__" and hasattr(m, "__class__"):
        m_name = m.__class__.__name__

    async def middleware_wrapper(handler: Any, event: Any, data: Any) -> Any:
        span_name = f"aiogram.middleware.{m_name}"
        tracer = trace.get_tracer("aiogram")

        attributes = {
            "aiogram.middleware.name": m_name,
        }

        if "event_router" in data:
            attributes["aiogram.router.name"] = data["event_router"].name

        if "event_update" in data:
            with suppress(Exception):
                attributes["telegram.update.type"] = data["event_update"].event_type

        attributes.update(extract_telemetry_attributes(event, data))

        with tracer.start_as_current_span(span_name, attributes=attributes):
            return await m(handler, event, data)

    return middleware_wrapper


@asynccontextmanager
async def trace_filter(
    filter_obj: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> AsyncGenerator[Any, None]:
    if not HAS_OTEL:
        yield None
        return

    if filter_obj.magic is not None:
        f_name = "MagicFilter"
    else:
        f_name = get_callable_name(filter_obj.callback)

    span_name = f"aiogram.filter.{f_name}"
    tracer = trace.get_tracer("aiogram")

    attributes = {
        "aiogram.filter.name": f_name,
    }

    if "event_router" in kwargs:
        attributes["aiogram.router.name"] = kwargs["event_router"].name

    if "event_update" in kwargs:
        with suppress(Exception):
            attributes["telegram.update.type"] = kwargs["event_update"].event_type

    if args:
        attributes.update(extract_telemetry_attributes(args[0], kwargs))

    with tracer.start_as_current_span(span_name, attributes=attributes) as span:
        yield span


@asynccontextmanager
async def trace_handler(
    handler_obj: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> AsyncGenerator[Any, None]:
    if not HAS_OTEL:
        yield None
        return

    h_name = get_callable_name(handler_obj.callback)
    span_name = f"aiogram.handler.{h_name}"
    tracer = trace.get_tracer("aiogram")

    attributes = {
        "aiogram.handler.name": h_name,
    }

    if "event_router" in kwargs:
        attributes["aiogram.router.name"] = kwargs["event_router"].name

    if "event_update" in kwargs:
        with suppress(Exception):
            attributes["telegram.update.type"] = kwargs["event_update"].event_type

    if args:
        attributes.update(extract_telemetry_attributes(args[0], kwargs))

    with tracer.start_as_current_span(span_name, attributes=attributes) as span:
        yield span


@asynccontextmanager
async def trace_api_call(method: Any) -> AsyncGenerator[Any, None]:
    if not HAS_OTEL:
        yield None
        return

    method_name = method.__api_method__
    span_name = f"telegram.api.{method_name}"
    tracer = trace.get_tracer("aiogram")

    attributes = {
        "telegram.api.method": method_name,
    }

    for field_name, attr_name in [
        ("chat_id", "telegram.chat.id"),
        ("user_id", "telegram.user.id"),
        ("message_id", "telegram.message.id"),
        ("reply_to_message_id", "telegram.reply_to_message.id"),
    ]:
        val = getattr(method, field_name, None)
        if val is not None and isinstance(val, (int, str)):
            attributes[attr_name] = val

    with tracer.start_as_current_span(span_name, attributes=attributes) as span:
        yield span
