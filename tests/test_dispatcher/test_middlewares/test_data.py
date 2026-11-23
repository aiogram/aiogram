import datetime
from typing import Any

from aiogram import Dispatcher
from aiogram.dispatcher.middlewares import data
from aiogram.types import Chat, Message, Update, User
from tests.mocked_bot import MockedBot


def test_exports():
    assert set(data.__all__) == {"FSMKeysData", "MiddlewareData", "OuterData", "RouterOuterData"}
    assert not hasattr(data, "FSMData")


def test_required_keys():
    # The runtime view must match what mypy sees (a `from __future__` import would make every key required)
    assert data.OuterData.__required_keys__ == {"dispatcher", "bot", "event_context"}
    assert data.RouterOuterData.__required_keys__ == {
        "dispatcher",
        "bot",
        "event_context",
        "event_update",
        "event_router",
    }
    assert data.MiddlewareData.__required_keys__ == data.RouterOuterData.__required_keys__ | {
        "handler"
    }
    assert data.MiddlewareData.__optional_keys__ == {
        "bots",
        "fsm_storage",
        "state",
        "raw_state",
        "i18n",
        "i18n_middleware",
    }


async def test_required_keys_match_dispatched_data(bot: MockedBot):
    # Each type's required keys are present where the docs say to use it
    dp = Dispatcher()
    seen: dict[str, set[str]] = {}

    @dp.update.outer_middleware()
    async def update_outer(handler, event, kw):
        seen["update_outer"] = set(kw)
        return await handler(event, kw)

    @dp.update.middleware()
    async def update_inner(handler, event, kw):
        seen["update_inner"] = set(kw)
        return await handler(event, kw)

    @dp.message.outer_middleware()
    async def message_outer(handler, event, kw):
        seen["message_outer"] = set(kw)
        return await handler(event, kw)

    @dp.message.middleware()
    async def message_inner(handler, event, kw):
        seen["message_inner"] = set(kw)
        return await handler(event, kw)

    @dp.message()
    async def on_message(message: Message, **kw: Any) -> None:
        seen["handler"] = set(kw)
        raise ValueError

    @dp.errors()
    async def on_error(event: Any, **kw: Any) -> bool:
        seen["errors"] = set(kw)
        return True

    message = Message(
        message_id=1,
        date=datetime.datetime.now(),
        chat=Chat(id=1, type="private"),
        from_user=User(id=1, is_bot=False, first_name="Test"),
        text="test",
    )
    await dp.feed_update(bot, Update(update_id=1, message=message))

    for point in ("update_outer", "update_inner", "errors"):
        assert data.OuterData.__required_keys__ <= seen[point], point
    assert data.RouterOuterData.__required_keys__ <= seen["message_outer"]
    for point in ("message_inner", "handler"):
        assert data.MiddlewareData.__required_keys__ <= seen[point], point
