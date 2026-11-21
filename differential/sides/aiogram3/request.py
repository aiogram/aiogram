"""Request / response side for aiogram 3.x (A-09): what 3.x sends over HTTP and accepts back.

Standalone: stdlib + aiogram only, run by the runner as ``python -I request.py --corpus DIR
--out FILE --trace-module trace.py --header JSON [--poison]``. ``wire.py`` (the body
canonicaliser) is loaded from the directory of ``--trace-module``.

Every request goes through the public path, ``bot(method)``, to a local aiohttp ``TestServer``
that plays the Bot API and records the raw request (R26). Cases and probes:

- ``request.*`` (A-04 inputs and the probes below) / ``resolved`` + ``encoding``
- ``response.*`` (A-04 inputs) / ``decode``: the result dump, or the exception and its attributes
- ``webhook.reply.*`` / ``resolved`` + ``encoding``: a method returned as the webhook reply
- ``request.*`` (A-04 inputs) / ``serialize``: ``deserialize_telegram_object(method)``

``--poison`` drops one resolved param from every ``resolved`` record.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import importlib.util
import json
import platform
import sys
import time
import tomllib
from pathlib import Path
from types import ModuleType
from typing import Any

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

import aiogram
from aiogram import Bot, Dispatcher, methods
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.client.telegram import TelegramAPIServer
from aiogram.exceptions import AiogramError
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    Message,
    TelegramObject,
)
from aiogram.utils.serialization import deserialize_telegram_object
from aiogram.webhook.aiohttp_server import SimpleRequestHandler

TOKEN = "42:DIFFERENTIAL"  # noqa: S105 - a fake token for the local fake server
CHAT_ID = 100000001
# what the fake server answers to request probes; their result is not what they record
REQUEST_REPLY = "response.sendMessage"
# a minimal call per method that a response input answers
RESPONSE_CALLS: dict[str, dict[str, Any]] = {
    "sendMessage": {"chat_id": CHAT_ID, "text": "hello"},
    "getUpdates": {},
}
HOOK_MARK = "differential_hook"  # the key the custom json_dumps adds to every dumped object


def load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"differential_{path.stem}", path)
    if spec is None or spec.loader is None:
        msg = f"cannot load {path}"
        raise ImportError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeBotAPI:
    """A local Bot API: records each raw request and answers with a fixed body and status."""

    def __init__(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.reply: tuple[bytes, int] = (b"", 200)
        app = web.Application()
        app.router.add_route("*", "/{tail:.*}", self.handle)
        self.server = TestServer(app)

    async def handle(self, request: web.Request) -> web.Response:
        self.requests.append(
            {
                "http_method": request.method,
                "api_method": request.path.rsplit("/", 1)[-1],
                "content_type": request.headers.get("Content-Type", ""),
                "body": await request.read(),
            }
        )
        body, status = self.reply
        return web.Response(body=body, status=status, content_type="application/json")

    def session(self, cls: type[AiohttpSession] = AiohttpSession, **kwargs: Any) -> AiohttpSession:
        base = str(self.server.make_url("")).rstrip("/")
        return cls(api=TelegramAPIServer.from_base(base), **kwargs)


# ------------------------------------------------------------------------------------------------
# Inputs
# ------------------------------------------------------------------------------------------------


def materialise(value: Any, files: Path) -> Any:
    """Corpus params to Python: ``{corpus_file = "x"}`` becomes an upload of ``files/x``."""
    if isinstance(value, dict):
        if set(value) == {"corpus_file"}:
            name = value["corpus_file"]
            return BufferedInputFile((files / name).read_bytes(), filename=name)
        return {key: materialise(item, files) for key, item in value.items()}
    if isinstance(value, list):
        return [materialise(item, files) for item in value]
    return value


def build(api_method: str, params: dict[str, Any]) -> methods.TelegramMethod[Any]:
    cls = getattr(methods, api_method[0].upper() + api_method[1:])
    method: methods.TelegramMethod[Any] = cls(**params)
    return method


def keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Так ✓", callback_data="yes")]]
    )


class PrepareValueSession(AiohttpSession):
    """Hook (a): a session subclass whose ``prepare_value`` rewrites one string."""

    def prepare_value(
        self, value: Any, bot: Bot, files: dict[str, Any], _dumps_json: bool = True
    ) -> Any:  # noqa: FBT001, FBT002, E501 - the overridden signature
        if value == "hello":
            value = "hello from prepare_value"
        return super().prepare_value(value, bot=bot, files=files, _dumps_json=_dumps_json)


class RewriteText(BaseRequestMiddleware):
    """Hook (b): a request middleware that rewrites a param."""

    async def __call__(self, make_request: Any, bot: Bot, method: Any) -> Any:
        return await make_request(bot, method.model_copy(update={"text": "hello from middleware"}))


def hooked_dumps(obj: Any, **kwargs: Any) -> str:
    """Hook (c): a custom ``json_dumps`` that marks every object it dumps."""
    if isinstance(obj, dict):
        obj = {**obj, HOOK_MARK: True}
    return json.dumps(obj, **kwargs)


# ------------------------------------------------------------------------------------------------
# Probes
# ------------------------------------------------------------------------------------------------


class Side:
    def __init__(self, trace: ModuleType, wire: ModuleType, corpus: Path, *, poison: bool) -> None:
        self.trace, self.wire, self.corpus, self.poison = trace, wire, corpus, poison
        manifest = tomllib.loads((corpus / "MANIFEST.toml").read_text(encoding="utf-8"))
        self.inputs = {item["id"]: item for item in manifest["input"]}
        self.records: list[dict[str, Any]] = []
        self.api = FakeBotAPI()

    def fixture(self, case: str) -> tuple[bytes, int]:
        item = self.inputs[case]
        return (self.corpus / item["path"]).read_bytes(), item.get("status", 200)

    def wire_records(
        self,
        case: str,
        content_type: str,
        body: bytes,
        extra: dict[str, Any],
        relative: dict[str, datetime.timedelta] | None = None,
        window: tuple[float, float] = (0, 0),
    ) -> None:
        """``resolved`` + ``encoding`` of one captured body.

        ``relative`` names params sent as ``now + timedelta`` (PD-11). One that falls inside the
        send ``window`` (+- 1 s for rounding) is recorded as ``{"now_plus": <seconds>}``, which is
        what both sides must agree on; anything else keeps the raw offset from the window start.
        """
        resolved, encoding = self.wire.canonical_request(content_type, body)
        for name, delta in (relative or {}).items():
            offset = int(resolved[name]) - delta.total_seconds()
            inside = window[0] - 1 <= offset <= window[1] + 1
            resolved[name] = {
                "now_plus": int(delta.total_seconds() if inside else offset - window[0])
            }
        if self.poison and resolved:
            del resolved[min(resolved)]
        self.records.append(self.trace.ok(case, "resolved", resolved))
        self.records.append(self.trace.ok(case, "encoding", {**encoding, **extra}))

    async def send(
        self,
        case: str,
        method: methods.TelegramMethod[Any],
        *,
        session: AiohttpSession | None = None,
        default: DefaultBotProperties | None = None,
        relative: dict[str, datetime.timedelta] | None = None,
    ) -> None:
        """Send ``method`` through ``bot(method)`` and record the request the server got."""
        session = session or self.api.session()
        bot = Bot(TOKEN, session=session, default=default)
        self.api.requests.clear()
        self.api.reply = self.fixture(REQUEST_REPLY)
        started = time.time()
        try:
            await bot(method)
        except AiogramError:
            pass  # the reply does not fit every method; response.* cases cover decoding
        except Exception as exc:  # noqa: BLE001 - a failed send is a recorded outcome
            self.records.append(self.trace.error(case, "resolved", exc))
            self.records.append(self.trace.error(case, "encoding", exc))
            return
        finally:
            await session.close()
        (request,) = self.api.requests
        extra = {"http_method": request["http_method"], "api_method": request["api_method"]}
        self.wire_records(
            case,
            request["content_type"],
            request["body"],
            extra,
            relative,
            (started, time.time()),
        )

    async def corpus_requests(self) -> None:
        for case, item in self.inputs.items():
            if item["kind"] != "request":
                continue
            spec = tomllib.loads((self.corpus / item["path"]).read_text(encoding="utf-8"))
            params = materialise(
                {**spec.get("params", {}), **spec.get("extra", {})}, self.corpus / "files"
            )
            default = DefaultBotProperties(**spec["defaults"]) if "defaults" in spec else None
            await self.send(case, build(spec["method"], params), default=default)
            self.serialize(case, build(spec["method"], params), default)

    def serialize(self, case: str, method: Any, default: DefaultBotProperties | None) -> None:
        result = deserialize_telegram_object(method, default=default)
        # attach keys are random: name the files by their order instead
        names = {f"attach://{key}": f"file#{n}" for n, key in enumerate(result.files)}

        def rename(value: Any) -> Any:
            if isinstance(value, dict):
                return {key: rename(item) for key, item in value.items()}
            if isinstance(value, list):
                return [rename(item) for item in value]
            return names.get(value, value) if isinstance(value, str) else value

        files = {names[f"attach://{key}"]: file.filename for key, file in result.files.items()}
        self.records.append(
            self.trace.ok(case, "serialize", {"data": rename(result.data), "files": files})
        )

    async def defaults(self) -> None:
        variants = {
            "none": None,
            "parse_mode": DefaultBotProperties(parse_mode="HTML"),
            "link_preview_protect": DefaultBotProperties(
                link_preview=LinkPreviewOptions(is_disabled=True), protect_content=True
            ),
        }
        for name, default in variants.items():
            method = methods.SendMessage(chat_id=CHAT_ID, text="<b>hi</b> https://example.com")
            await self.send(f"request.defaults.{name}", method, default=default)

    async def hooks(self) -> None:
        def method() -> methods.SendMessage:
            return methods.SendMessage(chat_id=CHAT_ID, text="hello", reply_markup=keyboard())

        await self.send("request.hooks.none", method())
        await self.send(
            "request.hooks.prepare_value", method(), session=self.api.session(PrepareValueSession)
        )
        session = self.api.session()
        session.middleware(RewriteText())
        await self.send("request.hooks.middleware", method(), session=session)
        await self.send(
            "request.hooks.json_dumps", method(), session=self.api.session(json_dumps=hooked_dumps)
        )

    async def datetimes(self) -> None:
        aware = datetime.datetime(2030, 1, 2, 3, 4, 5, tzinfo=datetime.UTC)
        naive = datetime.datetime(2030, 1, 2, 3, 4, 5)  # noqa: DTZ001 - naive on purpose
        ban: dict[str, Any] = {"chat_id": CHAT_ID, "user_id": 900000002}
        await self.send("request.datetime.aware", methods.BanChatMember(**ban, until_date=aware))
        await self.send("request.datetime.naive", methods.BanChatMember(**ban, until_date=naive))
        await self.send(
            "request.datetime.timedelta",
            methods.BanChatMember(**ban, until_date=datetime.timedelta(days=1)),
            relative={"until_date": datetime.timedelta(days=1)},
        )
        await self.send(
            "request.datetime.floats",
            methods.SendLocation(
                chat_id=CHAT_ID, latitude=50.4501, longitude=30.5234, horizontal_accuracy=1.5
            ),
        )
        await self.send(
            "request.datetime.large_int",
            methods.SendMessage(chat_id=2**53 + 1, text="hello", message_thread_id=2**31 + 7),
        )
        await self.send(
            "request.datetime.non_ascii",
            methods.SendMessage(
                chat_id=CHAT_ID, text="Привіт 👋 — “ok”   end", reply_markup=keyboard()
            ),
        )

    async def responses(self) -> None:
        session = self.api.session()
        bot = Bot(TOKEN, session=session)
        for case, item in self.inputs.items():
            if item["kind"] != "response":
                continue
            self.api.reply = self.fixture(case)
            try:
                result = await bot(build(item["method"], RESPONSE_CALLS[item["method"]]))
            except AiogramError as exc:
                attrs = {
                    name: getattr(exc, name)
                    for name in ("message", "retry_after", "migrate_to_chat_id")
                    if hasattr(exc, name)
                }
                self.records.append(self.trace.error(case, "decode", exc, attrs=attrs))
                continue
            self.records.append(self.trace.ok(case, "decode", dump(result)))
        await session.close()

    async def webhook_replies(self) -> None:
        photo = (self.corpus / "files" / "red.png").read_bytes()
        replies = {
            "webhook.reply.text": lambda: methods.SendMessage(chat_id=CHAT_ID, text="hello"),
            "webhook.reply.photo": lambda: methods.SendPhoto(
                chat_id=CHAT_ID, photo=BufferedInputFile(photo, filename="red.png"), caption="red"
            ),
        }
        update = (self.corpus / self.inputs["update.text.small"]["path"]).read_bytes()
        for case, reply in replies.items():
            dispatcher = Dispatcher()

            @dispatcher.message()
            async def handler(message: Message, reply: Any = reply) -> Any:
                return reply()

            session = self.api.session()
            bot = Bot(TOKEN, session=session)
            app = web.Application()
            SimpleRequestHandler(dispatcher, bot, handle_in_background=False).register(
                app, path="/hook"
            )
            async with TestClient(TestServer(app)) as client:
                response = await client.post(
                    "/hook", data=update, headers={"Content-Type": "application/json"}
                )
                body = await response.read()
                self.wire_records(
                    case, response.headers["Content-Type"], body, {"status": response.status}
                )
            await session.close()

    async def run(self) -> list[dict[str, Any]]:
        async with self.api.server:
            await self.corpus_requests()
            await self.defaults()
            await self.hooks()
            await self.datetimes()
            await self.responses()
            await self.webhook_replies()
        return self.records


def dump(value: Any) -> Any:
    if isinstance(value, TelegramObject):
        return {
            "type": type(value).__name__,
            "dump": value.model_dump(mode="json", exclude_unset=True),
        }
    if isinstance(value, list):
        return [dump(item) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--trace-module", required=True)
    parser.add_argument("--header", required=True)
    parser.add_argument("--poison", action="store_true")
    args = parser.parse_args()

    trace_path = Path(args.trace_module)
    trace, wire = load_module(trace_path), load_module(trace_path.with_name("wire.py"))
    records = asyncio.run(Side(trace, wire, Path(args.corpus), poison=args.poison).run())

    header = json.loads(args.header)
    header.update(
        aiogram=aiogram.__version__,
        python=sys.version.split()[0],
        implementation=platform.python_implementation(),
        platform=sys.platform,
    )
    trace.write(args.out, header, records)


if __name__ == "__main__":
    main()
