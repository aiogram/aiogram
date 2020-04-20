import datetime
from typing import Any, Dict, Type

import pytest

from aiogram.api.types import (
    CallbackQuery,
    Chat,
    ChosenInlineResult,
    InlineQuery,
    Message,
    Poll,
    PollAnswer,
    PreCheckoutQuery,
    ShippingQuery,
    Update,
    User,
)
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.dispatcher.middlewares.types import MiddlewareStep, UpdateType

try:
    from asynctest import CoroutineMock, patch
except ImportError:
    from unittest.mock import AsyncMock as CoroutineMock, patch  # type: ignore


class MyMiddleware(BaseMiddleware):
    async def on_pre_process_update(self, update: Update, data: Dict[str, Any]) -> Any:
        return "update"

    async def on_pre_process_message(self, message: Message, data: Dict[str, Any]) -> Any:
        return "message"

    async def on_pre_process_edited_message(
        self, edited_message: Message, data: Dict[str, Any]
    ) -> Any:
        return "edited_message"

    async def on_pre_process_channel_post(
        self, channel_post: Message, data: Dict[str, Any]
    ) -> Any:
        return "channel_post"

    async def on_pre_process_edited_channel_post(
        self, edited_channel_post: Message, data: Dict[str, Any]
    ) -> Any:
        return "edited_channel_post"

    async def on_pre_process_inline_query(
        self, inline_query: InlineQuery, data: Dict[str, Any]
    ) -> Any:
        return "inline_query"

    async def on_pre_process_chosen_inline_result(
        self, chosen_inline_result: ChosenInlineResult, data: Dict[str, Any]
    ) -> Any:
        return "chosen_inline_result"

    async def on_pre_process_callback_query(
        self, callback_query: CallbackQuery, data: Dict[str, Any]
    ) -> Any:
        return "callback_query"

    async def on_pre_process_shipping_query(
        self, shipping_query: ShippingQuery, data: Dict[str, Any]
    ) -> Any:
        return "shipping_query"

    async def on_pre_process_pre_checkout_query(
        self, pre_checkout_query: PreCheckoutQuery, data: Dict[str, Any]
    ) -> Any:
        return "pre_checkout_query"

    async def on_pre_process_poll(self, poll: Poll, data: Dict[str, Any]) -> Any:
        return "poll"

    async def on_pre_process_poll_answer(
        self, poll_answer: PollAnswer, data: Dict[str, Any]
    ) -> Any:
        return "poll_answer"

    async def on_pre_process_error(self, exception: Exception, data: Dict[str, Any]) -> Any:
        return "error"

    async def on_process_update(self, update: Update, data: Dict[str, Any]) -> Any:
        return "update"

    async def on_process_message(self, message: Message, data: Dict[str, Any]) -> Any:
        return "message"

    async def on_process_edited_message(
        self, edited_message: Message, data: Dict[str, Any]
    ) -> Any:
        return "edited_message"

    async def on_process_channel_post(self, channel_post: Message, data: Dict[str, Any]) -> Any:
        return "channel_post"

    async def on_process_edited_channel_post(
        self, edited_channel_post: Message, data: Dict[str, Any]
    ) -> Any:
        return "edited_channel_post"

    async def on_process_inline_query(
        self, inline_query: InlineQuery, data: Dict[str, Any]
    ) -> Any:
        return "inline_query"

    async def on_process_chosen_inline_result(
        self, chosen_inline_result: ChosenInlineResult, data: Dict[str, Any]
    ) -> Any:
        return "chosen_inline_result"

    async def on_process_callback_query(
        self, callback_query: CallbackQuery, data: Dict[str, Any]
    ) -> Any:
        return "callback_query"

    async def on_process_shipping_query(
        self, shipping_query: ShippingQuery, data: Dict[str, Any]
    ) -> Any:
        return "shipping_query"

    async def on_process_pre_checkout_query(
        self, pre_checkout_query: PreCheckoutQuery, data: Dict[str, Any]
    ) -> Any:
        return "pre_checkout_query"

    async def on_process_poll(self, poll: Poll, data: Dict[str, Any]) -> Any:
        return "poll"

    async def on_process_poll_answer(self, poll_answer: PollAnswer, data: Dict[str, Any]) -> Any:
        return "poll_answer"

    async def on_process_error(self, exception: Exception, data: Dict[str, Any]) -> Any:
        return "error"

    async def on_post_process_update(
        self, update: Update, data: Dict[str, Any], result: Any
    ) -> Any:
        return "update"

    async def on_post_process_message(
        self, message: Message, data: Dict[str, Any], result: Any
    ) -> Any:
        return "message"

    async def on_post_process_edited_message(
        self, edited_message: Message, data: Dict[str, Any], result: Any
    ) -> Any:
        return "edited_message"

    async def on_post_process_channel_post(
        self, channel_post: Message, data: Dict[str, Any], result: Any
    ) -> Any:
        return "channel_post"

    async def on_post_process_edited_channel_post(
        self, edited_channel_post: Message, data: Dict[str, Any], result: Any
    ) -> Any:
        return "edited_channel_post"

    async def on_post_process_inline_query(
        self, inline_query: InlineQuery, data: Dict[str, Any], result: Any
    ) -> Any:
        return "inline_query"

    async def on_post_process_chosen_inline_result(
        self, chosen_inline_result: ChosenInlineResult, data: Dict[str, Any], result: Any
    ) -> Any:
        return "chosen_inline_result"

    async def on_post_process_callback_query(
        self, callback_query: CallbackQuery, data: Dict[str, Any], result: Any
    ) -> Any:
        return "callback_query"

    async def on_post_process_shipping_query(
        self, shipping_query: ShippingQuery, data: Dict[str, Any], result: Any
    ) -> Any:
        return "shipping_query"

    async def on_post_process_pre_checkout_query(
        self, pre_checkout_query: PreCheckoutQuery, data: Dict[str, Any], result: Any
    ) -> Any:
        return "pre_checkout_query"

    async def on_post_process_poll(self, poll: Poll, data: Dict[str, Any], result: Any) -> Any:
        return "poll"

    async def on_post_process_poll_answer(
        self, poll_answer: PollAnswer, data: Dict[str, Any], result: Any
    ) -> Any:
        return "poll_answer"

    async def on_post_process_error(
        self, exception: Exception, data: Dict[str, Any], result: Any
    ) -> Any:
        return "error"


UPDATE = Update(update_id=42)
MESSAGE = Message(message_id=42, date=datetime.datetime.now(), chat=Chat(id=42, type="private"))
POLL_ANSWER = PollAnswer(
    poll_id="poll", user=User(id=42, is_bot=False, first_name="Test"), option_ids=[0]
)


class TestBaseMiddleware:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "middleware_cls,should_be_awaited", [[MyMiddleware, True], [BaseMiddleware, False]]
    )
    @pytest.mark.parametrize(
        "step", [MiddlewareStep.PRE_PROCESS, MiddlewareStep.PROCESS, MiddlewareStep.POST_PROCESS]
    )
    @pytest.mark.parametrize(
        "event_name,event",
        [
            ["update", UPDATE],
            ["message", MESSAGE],
            ["poll_answer", POLL_ANSWER],
            ["error", Exception("KABOOM")],
        ],
    )
    async def test_trigger(
        self,
        step: MiddlewareStep,
        event_name: str,
        event: UpdateType,
        middleware_cls: Type[BaseMiddleware],
        should_be_awaited: bool,
    ):
        middleware = middleware_cls()

        with patch(
            f"tests.test_dispatcher.test_middlewares.test_base."
            f"MyMiddleware.on_{step.value}_{event_name}",
            new_callable=CoroutineMock,
        ) as mocked_call:
            response = await middleware.trigger(
                step=step, event_name=event_name, event=event, data={}
            )
            if should_be_awaited:
                mocked_call.assert_awaited()
                assert response is not None
            else:
                mocked_call.assert_not_awaited()
                assert response is None

    def test_not_configured(self):
        middleware = BaseMiddleware()
        assert not middleware.configured

        with pytest.raises(RuntimeError):
            manager = middleware.manager
