"""aiogram 3.x adapter: corpus inputs in, aiogram objects and calls out.

Every function a case uses lives here. Keep it thin: build what the input describes with public
3.x API, nothing the measured code paths would not do themselves.
"""

from __future__ import annotations

import copy
import json
import types
from collections.abc import Awaitable, Callable
from typing import Any

from aiohttp import web

from aiogram import Bot, Dispatcher, F, Router, methods
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    MessageEntity,
    Update,
    User,
)
from aiogram.utils.formatting import Text
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.serialization import deserialize_telegram_object
from aiogram.utils.text_decorations import html_decoration

TOKEN = "42:TEST-TOKEN-FOR-BENCHMARKS-0000000000"  # fabricated, matches no real bot


def method_class(name: str) -> type[methods.TelegramMethod[Any]]:
    return getattr(methods, name[0].upper() + name[1:])


# -- decode -----------------------------------------------------------------------------------


def decode_update(raw: bytes) -> Update:
    update = Update.model_validate_json(raw)
    update.event_type  # noqa: B018  the type lookup is part of the decode path
    return update


def response_decoder(method: str, status: int) -> Callable[[str], Any]:
    """The polling/response path: ``BaseSession.check_response`` with envelope + result types."""
    bot = Bot(TOKEN)
    instance = method_class(method).model_construct()
    check = bot.session.check_response
    return lambda content: check(bot, instance, status, content)


def retained_child(response: Any) -> Any:
    """One child kept from a decoded getUpdates batch (R04: does it pin the whole batch?)."""
    return response.result[0].message.chat


# -- dispatch ---------------------------------------------------------------------------------


def _patched(payload: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(payload)
    for dotted, value in patch.items():
        *path, last = dotted.split(".")
        node = payload
        for key in path:
            node = node[key]
        node[last] = value
    return payload


def _filter(spec: dict[str, Any]) -> Any:
    if spec["kind"] == "command":
        return Command(*spec["commands"])
    if spec["kind"] == "text_eq":
        return F.text == spec["value"]
    msg = f"unknown filter kind {spec['kind']!r}"
    raise ValueError(msg)


async def _pass(handler: Any, event: Any, data: dict[str, Any]) -> Any:
    return await handler(event, data)


def _handler(handler_id: str) -> Callable[..., Awaitable[str]]:
    async def handler(event: Any) -> str:
        return handler_id

    return handler


def build_dispatch(
    topology: dict[str, Any], updates: dict[str, Any], fsm: bool
) -> tuple[Callable[[], Awaitable[None]], Callable[[], Awaitable[None]]]:
    """A dispatcher for a ``routing/*.toml`` topology.

    Returns ``(feed_all, verify)``: ``feed_all`` feeds every ``[[event]]`` once, ``verify``
    checks each lands on its ``expect`` handler. ``updates`` maps wire ids to payloads.
    """
    bot = Bot(TOKEN)
    routers: dict[str, Router] = {}
    for spec in topology["router"]:
        if "parent" not in spec:
            router: Router = Dispatcher(storage=MemoryStorage(), disable_fsm=not fsm)
        else:
            router = Router(name=spec["name"])
            routers[spec["parent"]].include_router(router)
        routers[spec["name"]] = router
        for mw in spec.get("outer_middlewares", []):
            router.observers[mw["event"]].outer_middleware(_pass)
        for mw in spec.get("inner_middlewares", []):
            router.observers[mw["event"]].middleware(_pass)
        for handler in spec.get("handler", []):
            router.observers[handler["event"]].register(
                _handler(handler["id"]), *map(_filter, handler.get("filters", []))
            )
    dp = next(iter(routers.values()))
    assert isinstance(dp, Dispatcher)

    events = [
        (
            Update.model_validate(
                _patched(updates[event["update"]], event.get("patch", {})), context={"bot": bot}
            ),
            event["expect"],
        )
        for event in topology["event"]
    ]
    feed = dp.feed_update

    async def feed_all() -> None:
        for update, _ in events:
            await feed(bot, update)

    async def verify() -> None:
        for update, expect in events:
            result = await feed(bot, update)
            got = "unhandled" if result is UNHANDLED else result
            assert got == expect, f"update {update.update_id}: expected {expect}, got {got}"

    return feed_all, verify


# -- requests ---------------------------------------------------------------------------------


def _value(value: Any, files: Callable[[str], bytes]) -> Any:
    if isinstance(value, dict):
        if set(value) == {"corpus_file"}:
            return BufferedInputFile(files(value["corpus_file"]), filename=value["corpus_file"])
        return {k: _value(v, files) for k, v in value.items()}
    if isinstance(value, list):
        return [_value(v, files) for v in value]
    return value


def build_method(request: dict[str, Any], files: Callable[[str], bytes]) -> Any:
    params = _value(request.get("params", {}), files)
    return method_class(request["method"])(**params, **request.get("extra", {}))


async def fake_api(responses: dict[str, bytes]) -> tuple[str, Callable[[], Awaitable[None]]]:
    """A local Bot API on 127.0.0.1 answering each method with a pinned envelope.

    Returns ``(base_url, close)``. The body is read in full, as a real server would.
    """

    async def answer(request: web.Request) -> web.Response:
        await request.read()
        return web.Response(
            body=responses[request.match_info["method"]], content_type="application/json"
        )

    app = web.Application()
    app.router.add_post("/bot{token}/{method}", answer)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = runner.addresses[0][1]
    return f"http://127.0.0.1:{port}", runner.cleanup


def list_envelope(single: bytes) -> bytes:
    """``{"ok": true, "result": X}`` -> ``{"ok": true, "result": [X]}`` (sendMediaGroup)."""
    envelope = json.loads(single)
    envelope["result"] = [envelope["result"]]
    return json.dumps(envelope).encode()


def api_bot(base_url: str, defaults: dict[str, Any]) -> Bot:
    session = AiohttpSession(api=TelegramAPIServer.from_base(base_url))
    return Bot(TOKEN, session=session, default=DefaultBotProperties(**defaults))


# -- utilities --------------------------------------------------------------------------------


def keyboard_buttons(markup: dict[str, Any]) -> tuple[list[InlineKeyboardButton], int]:
    rows = markup["inline_keyboard"]
    return [InlineKeyboardButton(**b) for row in rows for b in row], len(rows[0])


def build_keyboard(buttons: list[InlineKeyboardButton], width: int) -> Any:
    builder = InlineKeyboardBuilder()
    for button in buttons:
        builder.add(button)
    builder.adjust(width)
    return builder.as_markup()


def keyboard_dump(markup: Any) -> Any:
    return markup.model_dump(mode="json", exclude_none=True)


def entities(payload: dict[str, Any]) -> tuple[str, list[MessageEntity]]:
    return payload["text"], [MessageEntity(**e) for e in payload["entities"]]


def formatting_html(text: str, items: list[MessageEntity]) -> str:
    return Text.from_entities(text, items).as_html()


def unparse_html(text: str, items: list[MessageEntity]) -> str:
    return html_decoration.unparse(text, items)


_PY_TYPES = {"int": int, "str": str, "bool": bool, "float": float}


def callback_filters(spec: dict[str, Any]) -> list[Any]:
    filters = []
    for cls in spec["classes"]:
        annotations = {f["name"]: _PY_TYPES[f["type"]] for f in cls["fields"]}
        data_cls = types.new_class(
            f"CB_{cls['prefix']}",
            (CallbackData,),
            {"prefix": cls["prefix"], "sep": spec["separator"]},
            lambda ns, a=annotations: ns.update(__annotations__=a, __module__=__name__),
        )
        filters.append(data_cls.filter())
    return filters


def callback_query(data: str) -> CallbackQuery:
    user = User(id=100000001, is_bot=False, first_name="Alice")
    return CallbackQuery(id="1", from_user=user, chat_instance="1", data=data)


def deserialize(method: Any, defaults: dict[str, Any]) -> Any:
    return deserialize_telegram_object(method, default=DefaultBotProperties(**defaults))


def memory_storage() -> tuple[Any, Any]:
    return MemoryStorage(), StorageKey(bot_id=42, chat_id=100000001, user_id=100000001)


def event_isolation() -> tuple[Any, Any]:
    return SimpleEventIsolation(), StorageKey(bot_id=42, chat_id=100000001, user_id=100000001)
