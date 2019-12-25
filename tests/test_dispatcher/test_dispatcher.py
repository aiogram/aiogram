import datetime
import time

import pytest
from asynctest import CoroutineMock, patch

from aiogram import Bot
from aiogram.api.methods import GetMe, GetUpdates, SendMessage
from aiogram.api.types import Chat, Message, Update, User
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.dispatcher.router import Router
from tests.mocked_bot import MockedBot


class TestDispatcher:
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

        @dp.message_handler()
        async def my_handler(message: Message, **kwargs):
            assert "bot" in kwargs
            assert isinstance(kwargs["bot"], Bot)
            assert kwargs["bot"] == bot
            return message.text

        results_count = 0
        async for result in dp.feed_update(
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
        ):
            results_count += 1
            assert result == "test"

        assert results_count == 1

    @pytest.mark.asyncio
    async def test_feed_raw_update(self):
        dp = Dispatcher()
        bot = Bot("42:TEST")

        @dp.message_handler()
        async def my_handler(message: Message):
            assert message.text == "test"
            return message.text

        handled = False
        async for result in dp.feed_raw_update(
            bot=bot,
            update={
                "update_id": 42,
                "message": {
                    "message_id": 42,
                    "date": int(time.time()),
                    "text": "test",
                    "chat": {"id": 42, "type": "private"},
                    "user": {"id": 42, "is_bot": False, "first_name": "Test"},
                },
            },
        ):
            handled = True
            assert result == "test"
        assert handled

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
        await dispatcher._silent_call_request(SendMessage(chat_id=42, text="test"))
        log_records = [rec.message for rec in caplog.records]
        assert len(log_records) == 1
        assert "Failed to make answer" in log_records[0]

    @pytest.mark.asyncio
    async def test_process_update_empty(self, bot: MockedBot):
        dispatcher = Dispatcher()

        assert not await dispatcher.process_update(Update(update_id=42), bot=bot)

    @pytest.mark.asyncio
    async def test_process_update_handled(self, bot: MockedBot):
        dispatcher = Dispatcher()

        @dispatcher.update_handler()
        async def update_handler(update: Update):
            pass

        assert await dispatcher.process_update(Update(update_id=42), bot=bot)

    @pytest.mark.asyncio
    async def test_process_update_call_request(self, bot: MockedBot):
        dispatcher = Dispatcher()

        @dispatcher.update_handler()
        async def update_handler(update: Update):
            return GetMe()

        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher._silent_call_request",
            new_callable=CoroutineMock,
        ) as mocked_silent_call_request:
            assert await dispatcher.process_update(Update(update_id=42), bot=bot)
            mocked_silent_call_request.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_update_exception(self, bot: MockedBot, caplog):
        dispatcher = Dispatcher()

        @dispatcher.update_handler()
        async def update_handler(update: Update):
            raise Exception("Kaboom!")

        assert await dispatcher.process_update(Update(update_id=42), bot=bot)
        log_records = [rec.message for rec in caplog.records]
        assert len(log_records) == 1
        assert "Cause exception while process update" in log_records[0]

    @pytest.mark.asyncio
    async def test_polling(self, bot: MockedBot):
        dispatcher = Dispatcher()

        async def _mock_updates(*_):
            yield Update(update_id=42)

        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher.process_update", new_callable=CoroutineMock
        ) as mocked_process_update, patch(
            "aiogram.dispatcher.dispatcher.Dispatcher._listen_updates"
        ) as patched_listen_updates:
            patched_listen_updates.return_value = _mock_updates()
            await dispatcher._polling(bot=bot)
            mocked_process_update.assert_awaited()

    @pytest.mark.asyncio
    async def test_start_polling(self, bot: MockedBot):
        dispatcher = Dispatcher()
        bot.add_result_for(
            GetMe, ok=True, result=User(id=42, is_bot=True, first_name="The bot", username="tbot")
        )

        async def _mock_updates(*_):
            yield Update(update_id=42)

        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher.process_update", new_callable=CoroutineMock
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
