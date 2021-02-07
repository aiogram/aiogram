import asyncio
import datetime
import time
import warnings
from typing import Any

import pytest

from aiogram import Bot
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.dispatcher.event.bases import UNHANDLED, SkipHandler
from aiogram.dispatcher.middlewares.user_context import UserContextMiddleware
from aiogram.dispatcher.router import Router
from aiogram.methods import GetMe, GetUpdates, SendMessage
from aiogram.types import (
    CallbackQuery,
    Chat,
    ChosenInlineResult,
    InlineQuery,
    Message,
    Poll,
    PollAnswer,
    PollOption,
    PreCheckoutQuery,
    ShippingAddress,
    ShippingQuery,
    Update,
    User,
)
from tests.mocked_bot import MockedBot

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock  # type: ignore
    from unittest.mock import patch


async def simple_message_handler(message: Message):
    await asyncio.sleep(0.2)
    return message.answer("ok")


async def invalid_message_handler(message: Message):
    await asyncio.sleep(0.2)
    raise Exception(42)


RAW_UPDATE = {
    "update_id": 42,
    "message": {
        "message_id": 42,
        "date": 1582324717,
        "text": "test",
        "chat": {"id": 42, "type": "private"},
        "from": {"id": 42, "is_bot": False, "first_name": "Test"},
    },
}
UPDATE = Update(**RAW_UPDATE)


class TestDispatcher:
    def test_init(self):
        dp = Dispatcher()

        assert dp.update.handlers
        assert dp.update.handlers[0].callback == dp._listen_update
        assert dp.update.outer_middlewares

    def test_parent_router(self):
        dp = Dispatcher()
        with pytest.raises(RuntimeError):
            dp.parent_router = Router()
        assert dp.parent_router is None
        dp._parent_router = Router()
        assert dp.parent_router is None

    @pytest.mark.asyncio
    async def test_feed_update(self):
        dp = Dispatcher()
        bot = Bot("42:TEST")

        @dp.message()
        async def my_handler(message: Message, **kwargs):
            assert "bot" in kwargs
            assert isinstance(kwargs["bot"], Bot)
            assert kwargs["bot"] == bot
            return message.text

        results_count = 0
        result = await dp.feed_update(
            bot=bot,
            update=Update(
                update_id=42,
                message=Message(
                    message_id=42,
                    date=datetime.datetime.now(),
                    text="test",
                    chat=Chat(id=42, type="private"),
                    from_user=User(id=42, is_bot=False, first_name="Test"),
                ),
            ),
        )
        results_count += 1
        assert result == "test"

    @pytest.mark.asyncio
    async def test_feed_raw_update(self):
        dp = Dispatcher()
        bot = Bot("42:TEST")

        @dp.message()
        async def my_handler(message: Message):
            assert message.text == "test"
            return message.text

        result = await dp.feed_raw_update(
            bot=bot,
            update={
                "update_id": 42,
                "message": {
                    "message_id": 42,
                    "date": int(time.time()),
                    "text": "test",
                    "chat": {"id": 42, "type": "private"},
                    "from": {"id": 42, "is_bot": False, "first_name": "Test"},
                },
            },
        )
        assert result == "test"

    @pytest.mark.asyncio
    async def test_listen_updates(self, bot: MockedBot):
        dispatcher = Dispatcher()
        bot.add_result_for(
            GetUpdates, ok=True, result=[Update(update_id=update_id) for update_id in range(42)]
        )
        index = 0
        async for update in dispatcher._listen_updates(bot=bot):
            assert update.update_id == index
            index += 1
            if index == 42:
                break
        assert index == 42

    @pytest.mark.asyncio
    async def test_silent_call_request(self, bot: MockedBot, caplog):
        dispatcher = Dispatcher()
        bot.add_result_for(SendMessage, ok=False, error_code=400, description="Kaboom")
        await dispatcher._silent_call_request(bot, SendMessage(chat_id=42, text="test"))
        log_records = [rec.message for rec in caplog.records]
        assert len(log_records) == 1
        assert "Failed to make answer" in log_records[0]

    @pytest.mark.asyncio
    async def test_process_update_empty(self, bot: MockedBot):
        dispatcher = Dispatcher()

        result = await dispatcher._process_update(bot=bot, update=Update(update_id=42))
        assert result

    @pytest.mark.asyncio
    async def test_process_update_handled(self, bot: MockedBot):
        dispatcher = Dispatcher()

        @dispatcher.update()
        async def update_handler(update: Update):
            pass

        assert await dispatcher._process_update(bot=bot, update=Update(update_id=42))

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "event_type,update,has_chat,has_user",
        [
            pytest.param(
                "message",
                Update(
                    update_id=42,
                    message=Message(
                        message_id=42,
                        date=datetime.datetime.now(),
                        text="test",
                        chat=Chat(id=42, type="private"),
                        from_user=User(id=42, is_bot=False, first_name="Test"),
                    ),
                ),
                True,
                True,
            ),
            pytest.param(
                "edited_message",
                Update(
                    update_id=42,
                    edited_message=Message(
                        message_id=42,
                        date=datetime.datetime.now(),
                        text="edited test",
                        chat=Chat(id=42, type="private"),
                        from_user=User(id=42, is_bot=False, first_name="Test"),
                    ),
                ),
                True,
                True,
            ),
            pytest.param(
                "channel_post",
                Update(
                    update_id=42,
                    channel_post=Message(
                        message_id=42,
                        date=datetime.datetime.now(),
                        text="test",
                        chat=Chat(id=-42, type="private"),
                    ),
                ),
                True,
                False,
            ),
            pytest.param(
                "edited_channel_post",
                Update(
                    update_id=42,
                    edited_channel_post=Message(
                        message_id=42,
                        date=datetime.datetime.now(),
                        text="test",
                        chat=Chat(id=-42, type="private"),
                    ),
                ),
                True,
                False,
            ),
            pytest.param(
                "inline_query",
                Update(
                    update_id=42,
                    inline_query=InlineQuery(
                        id="query id",
                        from_user=User(id=42, is_bot=False, first_name="Test"),
                        query="query",
                        offset="offser",
                    ),
                ),
                False,
                True,
            ),
            pytest.param(
                "chosen_inline_result",
                Update(
                    update_id=42,
                    chosen_inline_result=ChosenInlineResult(
                        result_id="result id",
                        from_user=User(id=42, is_bot=False, first_name="Test"),
                        query="query",
                    ),
                ),
                False,
                True,
            ),
            pytest.param(
                "callback_query",
                Update(
                    update_id=42,
                    callback_query=CallbackQuery(
                        id="query id",
                        from_user=User(id=42, is_bot=False, first_name="Test"),
                        chat_instance="instance",
                        data="placeholder",
                    ),
                ),
                False,
                True,
            ),
            pytest.param(
                "callback_query",
                Update(
                    update_id=42,
                    callback_query=CallbackQuery(
                        id="query id",
                        from_user=User(id=42, is_bot=False, first_name="Test"),
                        chat_instance="instance",
                        data="placeholder",
                        message=Message(
                            message_id=42,
                            date=datetime.datetime.now(),
                            text="test",
                            chat=Chat(id=42, type="private"),
                            from_user=User(id=42, is_bot=False, first_name="Test"),
                        ),
                    ),
                ),
                True,
                True,
            ),
            pytest.param(
                "shipping_query",
                Update(
                    update_id=42,
                    shipping_query=ShippingQuery(
                        id="id",
                        from_user=User(id=42, is_bot=False, first_name="Test"),
                        invoice_payload="payload",
                        shipping_address=ShippingAddress(
                            country_code="placeholder",
                            state="placeholder",
                            city="placeholder",
                            street_line1="placeholder",
                            street_line2="placeholder",
                            post_code="placeholder",
                        ),
                    ),
                ),
                False,
                True,
            ),
            pytest.param(
                "pre_checkout_query",
                Update(
                    update_id=42,
                    pre_checkout_query=PreCheckoutQuery(
                        id="query id",
                        from_user=User(id=42, is_bot=False, first_name="Test"),
                        currency="BTC",
                        total_amount=1,
                        invoice_payload="payload",
                    ),
                ),
                False,
                True,
            ),
            pytest.param(
                "poll",
                Update(
                    update_id=42,
                    poll=Poll(
                        id="poll id",
                        question="Q?",
                        options=[
                            PollOption(text="A1", voter_count=2),
                            PollOption(text="A2", voter_count=3),
                        ],
                        is_closed=False,
                        is_anonymous=False,
                        type="quiz",
                        allows_multiple_answers=False,
                        total_voter_count=0,
                        correct_option_id=1,
                    ),
                ),
                False,
                False,
            ),
            pytest.param(
                "poll_answer",
                Update(
                    update_id=42,
                    poll_answer=PollAnswer(
                        poll_id="poll id",
                        user=User(id=42, is_bot=False, first_name="Test"),
                        option_ids=[42],
                    ),
                ),
                False,
                True,
            ),
        ],
    )
    async def test_listen_update(
        self, event_type: str, update: Update, has_chat: bool, has_user: bool
    ):
        router = Dispatcher()
        observer = router.observers[event_type]

        @observer()
        async def my_handler(event: Any, **kwargs: Any):
            assert event == getattr(update, event_type)
            if has_chat:
                assert Chat.get_current(False)
            if has_user:
                assert User.get_current(False)
            return kwargs

        result = await router.update.trigger(update, test="PASS")
        assert isinstance(result, dict)
        assert result["event_update"] == update
        assert result["event_router"] == router
        assert result["test"] == "PASS"

    @pytest.mark.asyncio
    async def test_listen_unknown_update(self):
        dp = Dispatcher()

        with pytest.raises(SkipHandler):
            await dp._listen_update(Update(update_id=42))

    @pytest.mark.asyncio
    async def test_listen_unhandled_update(self):
        dp = Dispatcher()
        observer = dp.observers["message"]

        @observer(lambda event: False)
        async def handler(event: Any):
            pass

        response = await dp._listen_update(
            Update(
                update_id=42,
                poll=Poll(
                    id="poll id",
                    question="Q?",
                    options=[
                        PollOption(text="A1", voter_count=2),
                        PollOption(text="A2", voter_count=3),
                    ],
                    is_closed=False,
                    is_anonymous=False,
                    type="quiz",
                    allows_multiple_answers=False,
                    total_voter_count=0,
                    correct_option_id=0,
                ),
            )
        )
        assert response is UNHANDLED

    @pytest.mark.asyncio
    async def test_nested_router_listen_update(self):
        dp = Dispatcher()
        router0 = Router()
        router1 = Router()
        dp.include_router(router0)
        router0.include_router(router1)
        observer = router1.message

        @observer()
        async def my_handler(event: Message, **kwargs: Any):
            return kwargs

        update = Update(
            update_id=42,
            message=Message(
                message_id=42,
                date=datetime.datetime.now(),
                text="test",
                chat=Chat(id=42, type="private"),
                from_user=User(id=42, is_bot=False, first_name="Test"),
            ),
        )
        result = await dp._listen_update(update, test="PASS")
        assert isinstance(result, dict)
        assert result["event_update"] == update
        assert result["event_router"] == router1
        assert result["test"] == "PASS"

    @pytest.mark.asyncio
    async def test_process_update_call_request(self, bot: MockedBot):
        dispatcher = Dispatcher()

        @dispatcher.update()
        async def message_handler(update: Update):
            return GetMe()

        dispatcher.update.handlers.reverse()

        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher._silent_call_request",
            new_callable=CoroutineMock,
        ) as mocked_silent_call_request:
            result = await dispatcher._process_update(bot=bot, update=Update(update_id=42))
            print(result)
            mocked_silent_call_request.assert_awaited()

    @pytest.mark.asyncio
    async def test_process_update_exception(self, bot: MockedBot, caplog):
        dispatcher = Dispatcher()

        @dispatcher.update()
        async def update_handler(update: Update):
            raise Exception("Kaboom!")

        assert await dispatcher._process_update(bot=bot, update=Update(update_id=42))
        log_records = [rec.message for rec in caplog.records]
        assert len(log_records) == 1
        assert "Cause exception while process update" in log_records[0]

    @pytest.mark.asyncio
    async def test_polling(self, bot: MockedBot):
        dispatcher = Dispatcher()

        async def _mock_updates(*_):
            yield Update(update_id=42)

        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher._process_update", new_callable=CoroutineMock
        ) as mocked_process_update, patch(
            "aiogram.dispatcher.dispatcher.Dispatcher._listen_updates"
        ) as patched_listen_updates:
            patched_listen_updates.return_value = _mock_updates()
            await dispatcher._polling(bot=bot)
            mocked_process_update.assert_awaited()

    @pytest.mark.asyncio
    async def test_exception_handler_catch_exceptions(self):
        dp = Dispatcher()
        router = Router()
        dp.include_router(router)

        @router.message()
        async def message_handler(message: Message):
            raise Exception("KABOOM")

        update = Update(
            update_id=42,
            message=Message(
                message_id=42,
                date=datetime.datetime.now(),
                text="test",
                chat=Chat(id=42, type="private"),
                from_user=User(id=42, is_bot=False, first_name="Test"),
            ),
        )
        with pytest.raises(Exception, match="KABOOM"):
            await dp.update.trigger(update)

        @router.errors()
        async def error_handler(event: Update, exception: Exception):
            return "KABOOM"

        response = await dp.update.trigger(update)
        assert response == "KABOOM"

        @dp.errors()
        async def root_error_handler(event: Update, exception: Exception):
            return exception

        response = await dp.update.trigger(update)

        assert isinstance(response, Exception)
        assert str(response) == "KABOOM"

    @pytest.mark.asyncio
    async def test_start_polling(self, bot: MockedBot):
        dispatcher = Dispatcher()
        bot.add_result_for(
            GetMe, ok=True, result=User(id=42, is_bot=True, first_name="The bot", username="tbot")
        )

        async def _mock_updates(*_):
            yield Update(update_id=42)

        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher._process_update", new_callable=CoroutineMock
        ) as mocked_process_update, patch(
            "aiogram.dispatcher.router.Router.emit_startup", new_callable=CoroutineMock
        ) as mocked_emit_startup, patch(
            "aiogram.dispatcher.router.Router.emit_shutdown", new_callable=CoroutineMock
        ) as mocked_emit_shutdown, patch(
            "aiogram.dispatcher.dispatcher.Dispatcher._listen_updates"
        ) as patched_listen_updates:
            patched_listen_updates.return_value = _mock_updates()
            await dispatcher.start_polling(bot)

            mocked_emit_startup.assert_awaited()
            mocked_process_update.assert_awaited()
            mocked_emit_shutdown.assert_awaited()

    def test_run_polling(self, bot: MockedBot):
        dispatcher = Dispatcher()
        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher.start_polling"
        ) as patched_start_polling:
            dispatcher.run_polling(bot)
            patched_start_polling.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_feed_webhook_update_fast_process(self, bot: MockedBot):
        dispatcher = Dispatcher()
        dispatcher.message.register(simple_message_handler)

        response = await dispatcher.feed_webhook_update(bot, RAW_UPDATE, _timeout=0.3)
        assert isinstance(response, dict)
        assert response["method"] == "sendMessage"
        assert response["text"] == "ok"

    @pytest.mark.asyncio
    async def test_feed_webhook_update_slow_process(self, bot: MockedBot, recwarn):
        warnings.simplefilter("always")

        dispatcher = Dispatcher()
        dispatcher.message.register(simple_message_handler)

        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher._silent_call_request",
            new_callable=CoroutineMock,
        ) as mocked_silent_call_request:
            response = await dispatcher.feed_webhook_update(bot, RAW_UPDATE, _timeout=0.1)
            assert response is None
            await asyncio.sleep(0.5)
            mocked_silent_call_request.assert_awaited()

    @pytest.mark.asyncio
    async def test_feed_webhook_update_fast_process_error(self, bot: MockedBot, caplog):
        warnings.simplefilter("always")

        dispatcher = Dispatcher()
        dispatcher.message.register(invalid_message_handler)

        response = await dispatcher.feed_webhook_update(bot, RAW_UPDATE, _timeout=0.1)
        assert response is None
        await asyncio.sleep(0.5)

        log_records = [rec.message for rec in caplog.records]
        assert "Cause exception while process update" in log_records[0]
