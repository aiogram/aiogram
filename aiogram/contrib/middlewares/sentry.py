from typing import Dict

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import User
from aiogram.types.base import TelegramObject
from sentry_sdk import (start_transaction, Hub,
                        set_user, set_tag, set_context, )
from sentry_sdk.tracing import Span, Transaction

TRANSACTION_KEY = "sentry_transaction"
TRANSACTION_NAME = "aiogram_process_update"
UPDATE_TYPE_TAG = "update.type"


class SentryMiddleware(BaseMiddleware):
    """
    Add support for Sentry performance monitoring.
    More info:
    https://docs.sentry.io/platforms/python/performance/

    WARNING!
    This middleware not working correctly with Dispatcher setting
    `run_tasks_by_default=True`, cause `on_post_process_update` method
    runs immediately and didn't waiting for real process_update.
    You'll face the same behavior with handlers registered with `run_task=True`.
    """

    def __init__(self, update_type_tag=UPDATE_TYPE_TAG):
        super().__init__()
        self._bot_username = None
        self._mapper: Dict[TelegramObject, Span] = {}
        self._update_type_tag = update_type_tag

    async def on_pre_process_update(self, update, data):
        if self._bot_username is None:
            me = await update.bot.me
            self._bot_username = me.username

        self._start_transaction(data)
        set_tag("bot.username", self._bot_username)

    async def on_post_process_update(self, update, result, data):
        self._finish_transaction(data)

    async def on_pre_process_message(self, message, data):
        self._save_base_context()
        set_context("message", message.to_python())
        set_tag(self._update_type_tag, "message")

    async def on_pre_process_edited_message(self, edited_message, data):
        self._save_base_context()
        set_context("edited_message", edited_message.to_python())
        set_tag(self._update_type_tag, "edited_message")

    async def on_pre_process_channel_post(self, channel_post, data):
        self._save_base_context()
        set_context("channel_post", channel_post.to_python())
        set_tag(self._update_type_tag, "channel_post")

    async def on_pre_process_edited_channel_post(self, edited_channel_post, data):
        self._save_base_context()
        set_context("edited_channel_post", edited_channel_post.to_python())
        set_tag(self._update_type_tag, "edited_channel_post")

    async def on_pre_process_inline_query(self, inline_query, data):
        self._save_base_context()
        set_context("inline_query", inline_query.to_python())
        set_tag(self._update_type_tag, "inline_query")

    async def on_pre_process_chosen_inline_result(self, chosen_inline_result, data):
        self._save_base_context()
        set_context("inline_result", chosen_inline_result.to_python())
        set_tag(self._update_type_tag, "inline_result")

    async def on_pre_process_callback_query(self, callback_query, data):
        self._save_base_context()
        set_context("callback_query", callback_query.to_python())
        set_tag(self._update_type_tag, "callback_query")

    async def on_pre_process_shipping_query(self, shipping_query, data):
        self._save_base_context()
        set_context("shipping_query", shipping_query.to_python())
        set_tag(self._update_type_tag, "shipping_query")

    async def on_pre_process_pre_checkout_query(self, pre_checkout_query, data):
        self._save_base_context()
        set_context("pre_checkout_query", pre_checkout_query.to_python())
        set_tag(self._update_type_tag, "pre_checkout_query")

    async def on_pre_process_poll(self, poll, data):
        self._save_base_context()
        set_context("poll", poll.to_python())
        set_tag(self._update_type_tag, "poll")

    async def on_pre_process_poll_answer(self, poll_answer, data):
        self._save_base_context()
        set_context("poll_answer", poll_answer.to_python())
        set_tag(self._update_type_tag, "poll_answer")

    @staticmethod
    def _start_transaction(data, name=TRANSACTION_NAME):
        """ Start new transaction or it's child if exists. """
        transaction = Hub.current.scope.transaction

        if isinstance(transaction, Transaction):
            child = transaction.start_child(op=name)
            data[TRANSACTION_KEY] = child
            return child
        else:
            transaction = start_transaction(op=name, name=name)
            data[TRANSACTION_KEY] = transaction
            return transaction

    @staticmethod
    def _finish_transaction(data: dict):
        """ Finish current transaction. """
        transaction = data.get(TRANSACTION_KEY)
        if isinstance(transaction, (Transaction, Span)):
            del data[TRANSACTION_KEY]
            return transaction.finish()

    @staticmethod
    def _save_base_context():
        """ Saving contexts if User and Chat. """
        user = User.get_current()
        if isinstance(user, User):
            user_data = {"id": user.id}
            if user.username is not None:
                user_data["username"] = user.username
            set_user(user_data)
