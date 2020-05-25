import datetime
from typing import Any

import pytest

from aiogram.api.types import (
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
from aiogram.dispatcher.event.bases import NOT_HANDLED, SkipHandler, skip
from aiogram.dispatcher.middlewares.update_processing_context import UserContextMiddleware
from aiogram.dispatcher.router import Router
from aiogram.utils.warnings import CodeHasNoEffect

importable_router = Router()


class TestRouter:
    def test_including_routers(self):
        router1 = Router()
        router2 = Router()
        router3 = Router()
        assert router1.parent_router is None
        assert router2.parent_router is None
        assert router3.parent_router is None

        with pytest.raises(RuntimeError, match="Self-referencing routers is not allowed"):
            router1.include_router(router1)

        router1.include_router(router2)

        with pytest.raises(RuntimeError, match="Router is already attached"):
            router1.include_router(router2)

        router2.include_router(router3)

        with pytest.raises(RuntimeError, match="Circular referencing of Router is not allowed"):
            router3.include_router(router1)

        assert router1.parent_router is None
        assert router1.sub_routers == [router2]
        assert router2.parent_router is router1
        assert router2.sub_routers == [router3]
        assert router3.parent_router is router2
        assert router3.sub_routers == []

    def test_include_router_code_has_no_effect(self):
        router1 = Router()
        router2 = Router(use_builtin_filters=False)

        assert router1.use_builtin_filters
        assert not router2.use_builtin_filters
        with pytest.warns(CodeHasNoEffect):
            assert router1.include_router(router2)

    def test_include_router_by_string(self):
        router = Router()
        router.include_router("tests.test_dispatcher.test_router:importable_router")

    def test_include_router_by_string_bad_type(self):
        router = Router()
        with pytest.raises(ValueError, match=r"router should be instance of Router"):
            router.include_router("tests.test_dispatcher.test_router:TestRouter")

    def test_set_parent_router_bad_type(self):
        router = Router()
        with pytest.raises(ValueError, match=r"router should be instance of Router"):
            router.parent_router = object()

    def test_observers_config(self):
        router = Router()
        assert router.update.handlers
        assert router.update.handlers[0].callback == router._listen_update
        assert router.observers["message"] == router.message
        assert router.observers["edited_message"] == router.edited_message
        assert router.observers["channel_post"] == router.channel_post
        assert router.observers["edited_channel_post"] == router.edited_channel_post
        assert router.observers["inline_query"] == router.inline_query
        assert router.observers["chosen_inline_result"] == router.chosen_inline_result
        assert router.observers["callback_query"] == router.callback_query
        assert router.observers["shipping_query"] == router.shipping_query
        assert router.observers["pre_checkout_query"] == router.pre_checkout_query
        assert router.observers["poll"] == router.poll

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
        router = Router()
        router.update.outer_middleware(UserContextMiddleware())
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
        router = Router()

        with pytest.raises(SkipHandler):
            await router._listen_update(Update(update_id=42))

    @pytest.mark.asyncio
    async def test_listen_unhandled_update(self):
        router = Router()
        observer = router.observers["message"]

        @observer(lambda event: False)
        async def handler(event: Any):
            pass

        response = await router._listen_update(
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
        assert response is NOT_HANDLED

    @pytest.mark.asyncio
    async def test_nested_router_listen_update(self):
        router1 = Router()
        router2 = Router()
        router3 = Router()
        router1.include_router(router2)
        router1.include_router(router3)
        observer = router3.message

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
        result = await router1._listen_update(update, test="PASS")
        assert isinstance(result, dict)
        assert result["event_update"] == update
        assert result["event_router"] == router3
        assert result["test"] == "PASS"

    @pytest.mark.asyncio
    async def test_emit_startup(self):
        router1 = Router()
        router2 = Router()
        router1.include_router(router2)

        results = []

        @router1.startup()
        async def startup1():
            results.append(1)

        @router2.startup()
        async def startup2():
            results.append(2)

        await router2.emit_startup()
        assert results == [2]

        await router1.emit_startup()
        assert results == [2, 1, 2]

    @pytest.mark.asyncio
    async def test_emit_shutdown(self):
        router1 = Router()
        router2 = Router()
        router1.include_router(router2)

        results = []

        @router1.shutdown()
        async def shutdown1():
            results.append(1)

        @router2.shutdown()
        async def shutdown2():
            results.append(2)

        await router2.emit_shutdown()
        assert results == [2]

        await router1.emit_shutdown()
        assert results == [2, 1, 2]

    def test_skip(self):
        with pytest.raises(SkipHandler):
            skip()
        with pytest.raises(SkipHandler, match="KABOOM"):
            skip("KABOOM")

    @pytest.mark.asyncio
    async def test_exception_handler_catch_exceptions(self):
        root_router = Router()
        router = Router()
        root_router.include_router(router)

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
            await root_router.update.trigger(update)

        @root_router.errors()
        async def root_error_handler(event: Update, exception: Exception):
            return exception

        response = await root_router.update.trigger(update)

        assert isinstance(response, Exception)
        assert str(response) == "KABOOM"

        @router.errors()
        async def error_handler(event: Update, exception: Exception):
            return "KABOOM"

        response = await root_router.update.trigger(update)
        assert response == "KABOOM"
