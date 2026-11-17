"""Recorder and redactor for real traces (benchmarks/record, A-04)."""

import asyncio
import io
import json
import re

import pytest
from aiohttp import web

from aiogram import Bot
from aiogram.client.telegram import TelegramAPIServer
from aiogram.exceptions import ClientDecodeError
from aiogram.methods import SendMessage, SendPhoto
from aiogram.types import BufferedInputFile

redact = pytest.importorskip("benchmarks.record.redact")
recorder = pytest.importorskip("benchmarks.record.recorder")

BOT_ID = "1234567890"
TOKEN = f"{BOT_ID}:AAH{'x' * 32}"
USER_ID = 987654321
GROUP_ID = -1001234567890
PHONE = "+15551234567"
FILE_ID = "AgACAgIAAxkBAAIBY2ZsecretFileId"
UNIQUE_ID = "AQADsecretUniq"
TEXT = f"call @jane_doe at {PHONE} or tg://user?id={USER_ID}"


def user():
    return {"id": USER_ID, "is_bot": False, "first_name": "Jane", "username": "jane_doe"}


TRACE = [
    {"provenance": {"source": "recorded", "redacted": False}},
    {
        "method": "setWebhook",
        "params": {"url": f"https://example.com/hook/{TOKEN}"},
        "status": 200,
        "response": {"ok": True, "result": True},
    },
    {
        "method": "getUpdates",
        "params": {},
        "status": 200,
        "response": {
            "ok": True,
            "result": [
                {
                    "update_id": 1,
                    "message": {
                        "message_id": 1,
                        "date": 1,
                        "from": user(),
                        "chat": {"id": USER_ID, "type": "private", "first_name": "Jane"},
                        "text": TEXT,
                        "entities": [{"type": "mention", "offset": 5, "length": 9}],
                    },
                },
                {
                    "update_id": 2,
                    "message": {
                        "message_id": 2,
                        "date": 2,
                        "from": user(),
                        "chat": {"id": GROUP_ID, "type": "supergroup", "title": "Jane's group"},
                        "contact": {
                            "phone_number": PHONE,
                            "first_name": "Jane",
                            "user_id": USER_ID,
                        },
                        "photo": [
                            {
                                "file_id": FILE_ID,
                                "file_unique_id": UNIQUE_ID,
                                "width": 1,
                                "height": 1,
                            }
                        ],
                    },
                },
            ],
        },
    },
    {
        "method": "sendPhoto",
        "params": {"chat_id": GROUP_ID, "photo": FILE_ID},
        "status": 200,
        "response": {"ok": True, "result": True},
    },
]


def test_redact_trace():
    result = redact.redact_trace(json.loads(json.dumps(TRACE)))
    dumped = json.dumps(result)

    for secret in (TOKEN, BOT_ID, str(USER_ID), str(GROUP_ID), PHONE[1:], "jane_doe", "Jane"):
        assert secret not in dumped, secret
    assert FILE_ID not in dumped
    assert UNIQUE_ID not in dumped
    assert not re.search(r"\d{5,}:[A-Za-z0-9_-]{30,}", dumped)
    assert result[0]["provenance"]["redacted"]
    assert result[1]["params"]["url"].endswith(":***")

    first, second = (u["message"] for u in result[2]["response"]["result"])
    pseudo_user = first["from"]["id"]
    # Pseudonyms are stable within the trace, keep sign and length, and reach free text.
    assert pseudo_user == first["chat"]["id"] == second["contact"]["user_id"]
    assert len(str(pseudo_user)) == len(str(USER_ID))
    assert first["text"].endswith(f"tg://user?id={pseudo_user}")
    assert str(second["chat"]["id"]).startswith("-100")
    assert second["chat"]["id"] == result[3]["params"]["chat_id"]
    assert second["contact"]["phone_number"] in first["text"]
    # Entity offsets stay valid: the mention is still where the entity says.
    assert len(first["text"]) == len(TEXT)
    assert first["text"][5:14] == "@" + first["from"]["username"]
    assert result[3]["params"]["photo"] == second["photo"][0]["file_id"]


def test_recording_session_writes_raw_exchange():
    sink = io.StringIO()
    bot = Bot("42:TEST", session=recorder.RecordingSession(sink))
    method = SendPhoto(chat_id=1, photo=BufferedInputFile(b"png", filename="red.png"))

    message = '{"message_id":1,"date":1,"chat":{"id":1,"type":"private"}}'
    bot.session.check_response(bot, method, 200, f'{{"ok":true,"result":{message}}}')
    with pytest.raises(ClientDecodeError):
        bot.session.check_response(bot, SendMessage(chat_id=1, text="x"), 200, "not json")

    ok, broken = (json.loads(line) for line in sink.getvalue().splitlines())
    assert ok["method"] == "sendPhoto"
    assert ok["params"]["chat_id"] == 1
    (key,) = ok["files"]
    assert ok["params"]["photo"] == f"attach://{key}"
    assert ok["files"][key] == "red.png"
    assert ok["response"] == {"ok": True, "result": json.loads(message)}
    assert broken["raw"] == "not json"


async def test_record_stops_once_and_drains_replies(aiohttp_server, tmp_path):
    """Two concurrent messages with limit=1: polling stops, and the in-flight reply is recorded."""
    chat = {"id": 1, "type": "private"}
    sent = {"message_id": 10, "date": 1, "chat": chat, "text": "recorded"}
    batches = [[{"update_id": n, "message": {**sent, "message_id": n}} for n in (1, 2)]]

    async def bot_api(request: web.Request) -> web.Response:
        method = request.match_info["method"]
        if method == "getMe":
            result = {"id": 42, "is_bot": True, "first_name": "Recorder"}
        elif method == "getUpdates":
            await asyncio.sleep(0.05)
            result = batches.pop() if batches else []
        else:
            await asyncio.sleep(0.2)  # still in flight when the stop starts
            result = sent
        return web.json_response({"ok": True, "result": result})

    app = web.Application()
    app.router.add_post("/bot{token}/{method}", bot_api)
    server = await aiohttp_server(app)
    output = tmp_path / "trace.jsonl"

    await asyncio.wait_for(
        recorder.record(
            "42:TEST",
            output,
            limit=1,
            api=TelegramAPIServer.from_base(f"http://{server.host}:{server.port}"),
        ),
        timeout=10,
    )

    records = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    replies = [r for r in records if r.get("method") == "sendMessage"]
    assert len(replies) == 1
    assert replies[0]["response"] == {"ok": True, "result": sent}
