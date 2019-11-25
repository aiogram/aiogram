import datetime
from typing import Any

import pytest

from aiogram.api.types import (
    CallbackQuery,
    Chat,
    ChosenInlineResult,
    InlineQuery,
    Message,
    ShippingAddress,
    ShippingQuery,
    Update,
    User,
)
from aiogram.dispatcher.router import Router


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

    def test_observers_config(self):
        router = Router()
        assert router.update_handler.handlers
        assert router.update_handler.handlers[0].callback == router._listen_update
        assert router.observers["message"] == router.message_handler
        assert router.observers["edited_message"] == router.edited_message_handler
        assert router.observers["channel_post"] == router.channel_post_handler
        assert router.observers["edited_channel_post"] == router.edited_channel_post_handler
        assert router.observers["inline_query"] == router.inline_query_handler
        assert router.observers["chosen_inline_result"] == router.chosen_inline_result_handler
        assert router.observers["callback_query"] == router.callback_query_handler
        assert router.observers["shipping_query"] == router.shipping_query_handler
        assert router.observers["pre_checkout_query"] == router.pre_checkout_query_handler
        assert router.observers["poll"] == router.poll_handler

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
            # pytest.param("pre_checkout_query", Update(update_id=42, pre_checkout_query=...), False, False),
            # pytest.param("poll", Update(update_id=42, poll=...), False, False),
        ],
    )
    async def test_listen_update(
        self, event_type: str, update: Update, has_chat: bool, has_user: bool
    ):
        router = Router()
        observer = router.observers[event_type]

        @observer()
        async def my_handler(event: Any, **kwargs: Any):
            assert event == getattr(update, event_type)
            if has_chat:
                assert Chat.get_current(False)
            if has_user:
                assert User.get_current(False)
            return kwargs

        result = await router._listen_update(update, test="PASS")
        assert isinstance(result, dict)
        assert result["event_update"] == update
        assert result["event_router"] == router
        assert result["test"] == "PASS"
