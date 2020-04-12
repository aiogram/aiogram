from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from aiogram.dispatcher.middlewares.abstract import AbstractMiddleware
from aiogram.dispatcher.middlewares.types import MiddlewareStep, UpdateType

if TYPE_CHECKING:  # pragma: no cover
    from aiogram.api.types import (
        CallbackQuery,
        ChosenInlineResult,
        InlineQuery,
        Message,
        Poll,
        PollAnswer,
        PreCheckoutQuery,
        ShippingQuery,
        Update,
    )


class BaseMiddleware(AbstractMiddleware):
    """
    Base class for middleware.

    All methods on the middle always must be coroutines and name starts with "on_" like "on_process_message".
    """

    async def trigger(
        self,
        step: MiddlewareStep,
        event_name: str,
        event: UpdateType,
        data: Dict[str, Any],
        result: Any = None,
    ) -> Any:
        """
        Trigger action.

        :param step:
        :param event_name:
        :param event:
        :param data:
        :param result:
        :return:
        """
        handler_name = f"on_{step.value}_{event_name}"
        handler = getattr(self, handler_name, None)
        if not handler:
            return None
        args = (event, result, data) if step == MiddlewareStep.POST_PROCESS else (event, data)
        return await handler(*args)

    if TYPE_CHECKING:  # pragma: no cover
        # =============================================================================================
        # Event that triggers before process <event>
        # =============================================================================================
        async def on_pre_process_update(self, update: Update, data: Dict[str, Any]) -> Any:
            """
            Event that triggers before process update
            """

        async def on_pre_process_message(self, message: Message, data: Dict[str, Any]) -> Any:
            """
            Event that triggers before process message
            """

        async def on_pre_process_edited_message(
            self, edited_message: Message, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers before process edited_message
            """

        async def on_pre_process_channel_post(
            self, channel_post: Message, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers before process channel_post
            """

        async def on_pre_process_edited_channel_post(
            self, edited_channel_post: Message, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers before process edited_channel_post
            """

        async def on_pre_process_inline_query(
            self, inline_query: InlineQuery, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers before process inline_query
            """

        async def on_pre_process_chosen_inline_result(
            self, chosen_inline_result: ChosenInlineResult, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers before process chosen_inline_result
            """

        async def on_pre_process_callback_query(
            self, callback_query: CallbackQuery, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers before process callback_query
            """

        async def on_pre_process_shipping_query(
            self, shipping_query: ShippingQuery, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers before process shipping_query
            """

        async def on_pre_process_pre_checkout_query(
            self, pre_checkout_query: PreCheckoutQuery, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers before process pre_checkout_query
            """

        async def on_pre_process_poll(self, poll: Poll, data: Dict[str, Any]) -> Any:
            """
            Event that triggers before process poll
            """

        async def on_pre_process_poll_answer(
            self, poll_answer: PollAnswer, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers before process poll_answer
            """

        async def on_pre_process_error(self, exception: Exception, data: Dict[str, Any]) -> Any:
            """
            Event that triggers before process error
            """

        # =============================================================================================
        # Event that triggers on process <event> after filters.
        # =============================================================================================
        async def on_process_update(self, update: Update, data: Dict[str, Any]) -> Any:
            """
            Event that triggers on process update
            """

        async def on_process_message(self, message: Message, data: Dict[str, Any]) -> Any:
            """
            Event that triggers on process message
            """

        async def on_process_edited_message(
            self, edited_message: Message, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers on process edited_message
            """

        async def on_process_channel_post(
            self, channel_post: Message, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers on process channel_post
            """

        async def on_process_edited_channel_post(
            self, edited_channel_post: Message, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers on process edited_channel_post
            """

        async def on_process_inline_query(
            self, inline_query: InlineQuery, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers on process inline_query
            """

        async def on_process_chosen_inline_result(
            self, chosen_inline_result: ChosenInlineResult, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers on process chosen_inline_result
            """

        async def on_process_callback_query(
            self, callback_query: CallbackQuery, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers on process callback_query
            """

        async def on_process_shipping_query(
            self, shipping_query: ShippingQuery, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers on process shipping_query
            """

        async def on_process_pre_checkout_query(
            self, pre_checkout_query: PreCheckoutQuery, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers on process pre_checkout_query
            """

        async def on_process_poll(self, poll: Poll, data: Dict[str, Any]) -> Any:
            """
            Event that triggers on process poll
            """

        async def on_process_poll_answer(
            self, poll_answer: PollAnswer, data: Dict[str, Any]
        ) -> Any:
            """
            Event that triggers on process poll_answer
            """

        async def on_process_error(self, exception: Exception, data: Dict[str, Any]) -> Any:
            """
            Event that triggers on process error
            """

        # =============================================================================================
        # Event that triggers after process <event>.
        # =============================================================================================
        async def on_post_process_update(
            self, update: Update, data: Dict[str, Any], result: Any
        ) -> Any:
            """
            Event that triggers after processing update
            """

        async def on_post_process_message(
            self, message: Message, data: Dict[str, Any], result: Any
        ) -> Any:
            """
            Event that triggers after processing message
            """

        async def on_post_process_edited_message(
            self, edited_message: Message, data: Dict[str, Any], result: Any
        ) -> Any:
            """
            Event that triggers after processing edited_message
            """

        async def on_post_process_channel_post(
            self, channel_post: Message, data: Dict[str, Any], result: Any
        ) -> Any:
            """
            Event that triggers after processing channel_post
            """

        async def on_post_process_edited_channel_post(
            self, edited_channel_post: Message, data: Dict[str, Any], result: Any
        ) -> Any:
            """
            Event that triggers after processing edited_channel_post
            """

        async def on_post_process_inline_query(
            self, inline_query: InlineQuery, data: Dict[str, Any], result: Any
        ) -> Any:
            """
            Event that triggers after processing inline_query
            """

        async def on_post_process_chosen_inline_result(
            self, chosen_inline_result: ChosenInlineResult, data: Dict[str, Any], result: Any
        ) -> Any:
            """
            Event that triggers after processing chosen_inline_result
            """

        async def on_post_process_callback_query(
            self, callback_query: CallbackQuery, data: Dict[str, Any], result: Any
        ) -> Any:
            """
            Event that triggers after processing callback_query
            """

        async def on_post_process_shipping_query(
            self, shipping_query: ShippingQuery, data: Dict[str, Any], result: Any
        ) -> Any:
            """
            Event that triggers after processing shipping_query
            """

        async def on_post_process_pre_checkout_query(
            self, pre_checkout_query: PreCheckoutQuery, data: Dict[str, Any], result: Any
        ) -> Any:
            """
            Event that triggers after processing pre_checkout_query
            """

        async def on_post_process_poll(self, poll: Poll, data: Dict[str, Any], result: Any) -> Any:
            """
            Event that triggers after processing poll
            """

        async def on_post_process_poll_answer(
            self, poll_answer: PollAnswer, data: Dict[str, Any], result: Any
        ) -> Any:
            """
            Event that triggers after processing poll_answer
            """

        async def on_post_process_error(
            self, exception: Exception, data: Dict[str, Any], result: Any
        ) -> Any:
            """
            Event that triggers after processing error
            """
