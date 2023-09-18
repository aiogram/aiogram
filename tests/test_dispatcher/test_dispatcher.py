import asyncio
import datetime
import signal
import time
import warnings
from asyncio import Event
from collections import Counter
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from aiogram import Bot
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.dispatcher.event.bases import UNHANDLED, SkipHandler
from aiogram.dispatcher.router import Router
from aiogram.methods import GetMe, GetUpdates, SendMessage, TelegramMethod
from aiogram.types import (
    CallbackQuery,
    Chat,
    ChatJoinRequest,
    ChatMemberMember,
    ChatMemberUpdated,
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
from aiogram.types.error_event import ErrorEvent
from tests.mocked_bot import MockedBot


async def simple_message_handler(message: Message):
    await asyncio.sleep(0.2)
    return message.answer("ok")


async def invalid_message_handler(message: Message):
    await asyncio.sleep(0.2)
    raise Exception(42)


async def anext(ait):
    return await ait.__anext__()


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
        assert dp.update.outer_middleware

    def test_init_args(self, bot: MockedBot):
        with pytest.raises(TypeError):
            Dispatcher(bot)
        with pytest.raises(TypeError):
            Dispatcher(storage=bot)

    def test_data_bind(self):
        dp = Dispatcher()
        assert dp.get("foo") is None
        assert dp.get("foo", 42) == 42

        dp["foo"] = 1
        assert dp.workflow_data["foo"] == 1
        assert dp["foo"] == 1

        del dp["foo"]
        assert "foo" not in dp.workflow_data

    def test_storage_property(self, dispatcher: Dispatcher):
        assert dispatcher.storage is dispatcher.fsm.storage

    def test_parent_router(self, dispatcher: Dispatcher):
        with pytest.raises(RuntimeError):
            dispatcher.parent_router = Router()
        assert dispatcher.parent_router is None
        dispatcher._parent_router = Router()
        assert dispatcher.parent_router is None

    async def test_feed_update(self, dispatcher: Dispatcher, bot: MockedBot):
        @dispatcher.message()
        async def my_handler(message: Message, **kwargs):
            assert "bot" in kwargs
            assert isinstance(kwargs["bot"], Bot)
            assert kwargs["bot"] == bot
            return message.text

        results_count = 0
        result = await dispatcher.feed_update(
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

    async def test_listen_update_with_error(self, bot: MockedBot):
        dispatcher = Dispatcher()
        listen = dispatcher._listen_updates(bot=bot)
        bot.add_result_for(
            GetUpdates, ok=True, result=[Update(update_id=update_id) for update_id in range(42)]
        )
        bot.add_result_for(GetUpdates, ok=False, error_code=500, description="restarting")
        with patch(
            "aiogram.utils.backoff.Backoff.asleep",
            new_callable=AsyncMock,
        ) as mocked_asleep:
            assert isinstance(await anext(listen), Update)
            assert mocked_asleep.awaited

    async def test_silent_call_request(self, bot: MockedBot, caplog):
        dispatcher = Dispatcher()
        bot.add_result_for(SendMessage, ok=False, error_code=400, description="Kaboom")
        await dispatcher.silent_call_request(bot, SendMessage(chat_id=42, text="test"))
        log_records = [rec.message for rec in caplog.records]
        assert len(log_records) == 1
        assert "Failed to make answer" in log_records[0]

    async def test_process_update_empty(self, bot: MockedBot):
        dispatcher = Dispatcher()

        with pytest.warns(RuntimeWarning, match="Detected unknown update type") as record:
            result = await dispatcher._process_update(bot=bot, update=Update(update_id=42))
            assert not result

    async def test_process_update_handled(self, bot: MockedBot):
        dispatcher = Dispatcher()

        @dispatcher.update()
        async def update_handler(update: Update):
            pass

        with pytest.warns(RuntimeWarning, match="Detected unknown update type"):
            assert await dispatcher._process_update(bot=bot, update=Update(update_id=42))

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
            pytest.param(
                "my_chat_member",
                Update(
                    update_id=42,
                    my_chat_member=ChatMemberUpdated(
                        chat=Chat(id=42, type="private"),
                        from_user=User(id=42, is_bot=False, first_name="Test"),
                        date=datetime.datetime.now(),
                        old_chat_member=ChatMemberMember(
                            user=User(id=42, is_bot=False, first_name="Test")
                        ),
                        new_chat_member=ChatMemberMember(
                            user=User(id=42, is_bot=False, first_name="Test")
                        ),
                    ),
                ),
                True,
                True,
            ),
            pytest.param(
                "chat_member",
                Update(
                    update_id=42,
                    chat_member=ChatMemberUpdated(
                        chat=Chat(id=42, type="private"),
                        from_user=User(id=42, is_bot=False, first_name="Test"),
                        date=datetime.datetime.now(),
                        old_chat_member=ChatMemberMember(
                            user=User(id=42, is_bot=False, first_name="Test")
                        ),
                        new_chat_member=ChatMemberMember(
                            user=User(id=42, is_bot=False, first_name="Test")
                        ),
                    ),
                ),
                True,
                True,
            ),
            pytest.param(
                "chat_join_request",
                Update(
                    update_id=42,
                    chat_join_request=ChatJoinRequest(
                        chat=Chat(id=-42, type="private"),
                        from_user=User(id=42, is_bot=False, first_name="Test"),
                        user_chat_id=42,
                        date=datetime.datetime.now(),
                    ),
                ),
                True,
                True,
            ),
        ],
    )
    async def test_listen_update(
        self,
        event_type: str,
        update: Update,
        has_chat: bool,
        has_user: bool,
        bot: MockedBot,
    ):
        router = Dispatcher()
        observer = router.observers[event_type]

        @observer()
        async def my_handler(event: Any, **kwargs: Any):
            assert event.model_dump(exclude_defaults=True) == getattr(
                update, event_type
            ).model_dump(exclude_defaults=True)
            if has_chat:
                assert kwargs["event_chat"]
            if has_user:
                assert kwargs["event_from_user"]
            return kwargs

        result = await router.feed_update(bot, update, test="PASS")
        assert isinstance(result, dict)
        assert result["event_update"].model_dump(exclude_defaults=True) == update.model_dump(
            exclude_defaults=True
        )
        assert result["event_router"] == router
        assert result["test"] == "PASS"

    async def test_listen_unknown_update(self):
        dp = Dispatcher()
        pattern = "Detected unknown update type"
        with pytest.raises(SkipHandler), pytest.warns(RuntimeWarning, match=pattern) as record:
            await dp._listen_update(Update(update_id=42))
            if not record:
                pytest.fail("Expected 'Detected unknown update type' warning.")

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

    async def test_nested_router_listen_update(self, bot: MockedBot):
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
        result = await dp.feed_update(bot, update, test="PASS")
        assert isinstance(result, dict)
        assert result["event_update"].model_dump(exclude_defaults=True) == update.model_dump(
            exclude_defaults=True
        )
        assert result["event_router"] == router1
        assert result["test"] == "PASS"

    async def test_nested_router_middleware_resolution(self, bot: MockedBot):
        counter = Counter()

        def mw(type_: str, inject_data: dict):
            async def middleware(h, event, data):
                counter[type_] += 1
                data.update(inject_data)
                return await h(event, data)

            return middleware

        async def handler(event, foo, bar, baz, fizz, buzz):
            counter["child.handler"] += 1

        root = Dispatcher()
        child = Router()

        root.message.outer_middleware(mw("root.outer_middleware", {"foo": True}))
        root.message.middleware(mw("root.middleware", {"bar": None}))
        child.message.outer_middleware(mw("child.outer_middleware", {"fizz": 42}))
        child.message.middleware(mw("child.middleware", {"buzz": -42}))
        child.message.register(handler)

        root.include_router(child)
        await root.feed_update(
            bot=bot,
            update=Update(
                update_id=42,
                message=Message(
                    message_id=42,
                    date=datetime.datetime.fromtimestamp(0),
                    chat=Chat(id=-42, type="group"),
                ),
            ),
            baz=...,
        )

        assert counter["root.outer_middleware"] == 1
        assert counter["root.middleware"] == 1
        assert counter["child.outer_middleware"] == 1
        assert counter["child.middleware"] == 1
        assert counter["child.handler"] == 1

    async def test_process_update_call_request(self, bot: MockedBot):
        dispatcher = Dispatcher()

        @dispatcher.update()
        async def message_handler(update: Update):
            return GetMe()

        dispatcher.update.handlers.reverse()

        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher.silent_call_request",
            new_callable=AsyncMock,
        ) as mocked_silent_call_request:
            await dispatcher._process_update(bot=bot, update=Update(update_id=42))
            mocked_silent_call_request.assert_awaited()

    async def test_process_update_exception(self, bot: MockedBot, caplog):
        dispatcher = Dispatcher()

        @dispatcher.update()
        async def update_handler(update: Update):
            raise Exception("Kaboom!")

        with pytest.warns(RuntimeWarning, match="Detected unknown update type"):
            assert await dispatcher._process_update(bot=bot, update=Update(update_id=42))

        log_records = [rec.message for rec in caplog.records]
        assert len(log_records) == 1
        assert "Cause exception while process update" in log_records[0]

    @pytest.mark.parametrize("as_task", [True, False])
    async def test_polling(self, bot: MockedBot, as_task: bool):
        dispatcher = Dispatcher()

        async def _mock_updates(*_):
            yield Update(update_id=42)

        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher._process_update", new_callable=AsyncMock
        ) as mocked_process_update, patch(
            "aiogram.dispatcher.dispatcher.Dispatcher._listen_updates"
        ) as patched_listen_updates:
            patched_listen_updates.return_value = _mock_updates()
            await dispatcher._polling(bot=bot, handle_as_tasks=as_task)
            if as_task:
                pass
            else:
                mocked_process_update.assert_awaited()

    async def test_exception_handler_catch_exceptions(self, bot: MockedBot):
        dp = Dispatcher()
        router = Router()
        dp.include_router(router)

        class CustomException(Exception):
            pass

        @router.message()
        async def message_handler(message: Message):
            raise CustomException("KABOOM")

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
        with pytest.raises(CustomException, match="KABOOM"):
            await dp.feed_update(bot, update)

        @router.errors()
        async def error_handler(event: ErrorEvent):
            return "KABOOM"

        response = await dp.feed_update(bot, update)
        assert response == "KABOOM"

        @dp.errors()
        async def root_error_handler(event: ErrorEvent):
            return event.exception

        response = await dp.feed_update(bot, update)

        assert isinstance(response, CustomException)
        assert str(response) == "KABOOM"

    async def test_start_polling(self, bot: MockedBot):
        dispatcher = Dispatcher()
        dispatcher.workflow_data["bot"] = 42
        with pytest.raises(
            ValueError, match="At least one bot instance is required to start polling"
        ):
            await dispatcher.start_polling()
        with pytest.raises(
            ValueError,
            match="Keyword argument 'bot' is not acceptable, "
            "the bot instance should be passed as positional argument",
        ):
            await dispatcher.start_polling(bot, bot=bot)

        bot.add_result_for(
            GetMe, ok=True, result=User(id=42, is_bot=True, first_name="The bot", username="tbot")
        )

        async def _mock_updates(*_):
            yield Update(update_id=42)

        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher._process_update", new_callable=AsyncMock
        ) as mocked_process_update, patch(
            "aiogram.dispatcher.router.Router.emit_startup", new_callable=AsyncMock
        ) as mocked_emit_startup, patch(
            "aiogram.dispatcher.router.Router.emit_shutdown", new_callable=AsyncMock
        ) as mocked_emit_shutdown, patch(
            "aiogram.dispatcher.dispatcher.Dispatcher._listen_updates"
        ) as patched_listen_updates:
            patched_listen_updates.return_value = _mock_updates()
            await dispatcher.start_polling(bot)

            mocked_emit_startup.assert_awaited()
            mocked_process_update.assert_awaited()
            mocked_emit_shutdown.assert_awaited()
            assert dispatcher.workflow_data["bot"] == 42
            assert mocked_emit_shutdown.call_args.kwargs["bot"] == bot

    async def test_stop_polling(self):
        dispatcher = Dispatcher()
        with pytest.raises(RuntimeError):
            await dispatcher.stop_polling()

        assert not dispatcher._stop_signal
        assert not dispatcher._stopped_signal
        with patch("asyncio.locks.Event.wait", new_callable=AsyncMock) as mocked_wait:
            async with dispatcher._running_lock:
                await dispatcher.stop_polling()
                assert not dispatcher._stop_signal

                dispatcher._stop_signal = Event()
                dispatcher._stopped_signal = Event()
                await dispatcher.stop_polling()
                assert dispatcher._stop_signal.is_set()
                mocked_wait.assert_awaited()

    async def test_signal_stop_polling(self):
        dispatcher = Dispatcher()
        with patch("asyncio.locks.Event.set") as mocked_set:
            dispatcher._signal_stop_polling(signal.SIGINT)
            mocked_set.assert_not_called()

            async with dispatcher._running_lock:
                dispatcher._signal_stop_polling(signal.SIGINT)
                mocked_set.assert_not_called()

                dispatcher._stop_signal = Event()
                dispatcher._stopped_signal = Event()
                dispatcher._signal_stop_polling(signal.SIGINT)
                mocked_set.assert_called()

    async def test_stop_polling_by_method(self, bot: MockedBot):
        dispatcher = Dispatcher()
        bot.add_result_for(
            GetMe, ok=True, result=User(id=42, is_bot=True, first_name="The bot", username="tbot")
        )
        running = Event()

        async def _mock_updates(*_):
            running.set()
            while True:
                yield Update(update_id=42)
                await asyncio.sleep(1)

        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher._process_update", new_callable=AsyncMock
        ) as mocked_process_update, patch(
            "aiogram.dispatcher.dispatcher.Dispatcher._listen_updates",
            return_value=_mock_updates(),
        ):
            task = asyncio.ensure_future(dispatcher.start_polling(bot))
            await running.wait()

            assert not dispatcher._stop_signal.is_set()
            assert not dispatcher._stopped_signal.is_set()

            await dispatcher.stop_polling()
            assert dispatcher._stop_signal.is_set()
            assert dispatcher._stopped_signal.is_set()
            assert not task.exception()

            mocked_process_update.assert_awaited()

    @pytest.mark.skip("Stopping by signal should also be tested as the same as stopping by method")
    async def test_stop_polling_by_signal(self, bot: MockedBot):
        pass

    def test_run_polling(self, bot: MockedBot):
        dispatcher = Dispatcher()

        async def stop():
            await asyncio.sleep(0.5)
            await dispatcher.stop_polling()

        start_called = False

        @dispatcher.startup()
        async def startup():
            nonlocal start_called
            start_called = True
            asyncio.create_task(stop())

        original_start_polling = dispatcher.start_polling
        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher.start_polling",
            side_effect=original_start_polling,
        ) as patched_start_polling:
            dispatcher.run_polling(bot)
            patched_start_polling.assert_awaited_once()

        assert start_called

    async def test_feed_webhook_update_fast_process(self, bot: MockedBot):
        dispatcher = Dispatcher()
        dispatcher.message.register(simple_message_handler)

        response = await dispatcher.feed_webhook_update(bot, RAW_UPDATE, _timeout=0.3)
        assert isinstance(response, TelegramMethod)

    async def test_feed_webhook_update_slow_process(self, bot: MockedBot, recwarn):
        warnings.simplefilter("always")

        dispatcher = Dispatcher()
        dispatcher.message.register(simple_message_handler)

        with patch(
            "aiogram.dispatcher.dispatcher.Dispatcher.silent_call_request",
            new_callable=AsyncMock,
        ) as mocked_silent_call_request:
            response = await dispatcher.feed_webhook_update(bot, RAW_UPDATE, _timeout=0.1)
            assert response is None
            await asyncio.sleep(0.5)
            mocked_silent_call_request.assert_awaited()

    async def test_feed_webhook_update_fast_process_error(self, bot: MockedBot, caplog):
        warnings.simplefilter("always")

        dispatcher = Dispatcher()
        dispatcher.message.register(invalid_message_handler)

        pattern = r"Detected slow response into webhook"
        with pytest.warns(RuntimeWarning, match=pattern) as record:
            response = await dispatcher.feed_webhook_update(bot, RAW_UPDATE, _timeout=0.1)
            assert response is None
            await asyncio.sleep(0.5)

            log_records = [rec.message for rec in caplog.records]
            assert "Cause exception while process update" in log_records[0]

            if not record:
                pytest.fail("Expected 'Detected slow response into webhook' warning.")

    def test_specify_updates_calculation(self):
        def simple_msg_handler() -> None:
            ...

        def simple_callback_query_handler() -> None:
            ...

        def simple_poll_handler() -> None:
            ...

        def simple_edited_msg_handler() -> None:
            ...

        dispatcher = Dispatcher()
        dispatcher.message.register(simple_msg_handler)

        router1 = Router()
        router1.callback_query.register(simple_callback_query_handler)

        router2 = Router()
        router2.poll.register(simple_poll_handler)

        router21 = Router()
        router21.edited_message.register(simple_edited_msg_handler)

        useful_updates1 = dispatcher.resolve_used_update_types()

        assert sorted(useful_updates1) == sorted(["message"])

        dispatcher.include_router(router1)

        useful_updates2 = dispatcher.resolve_used_update_types()

        assert sorted(useful_updates2) == sorted(["message", "callback_query"])

        dispatcher.include_router(router2)

        useful_updates3 = dispatcher.resolve_used_update_types()

        assert sorted(useful_updates3) == sorted(["message", "callback_query", "poll"])

        router2.include_router(router21)

        useful_updates4 = dispatcher.resolve_used_update_types()

        assert sorted(useful_updates4) == sorted(
            ["message", "callback_query", "poll", "edited_message"]
        )

        useful_updates5 = router2.resolve_used_update_types()

        assert sorted(useful_updates5) == sorted(["poll", "edited_message"])
