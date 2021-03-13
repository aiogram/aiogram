from sentry_sdk import (start_transaction, Hub,
                        set_user, set_tag, set_context, )
from sentry_sdk.tracing import Span

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Chat, User


class SentryMiddleware(BaseMiddleware):
    """
    Add support for Sentry performance monitoring

    More info:
    https://docs.sentry.io/platforms/python/performance/
    """

    def __init__(self):
        super().__init__()
        self._bot_username = None

    async def on_pre_process_update(self, update, *_, **__):
        if self._bot_username is None:
            me = await update.bot.me
            self._bot_username = me.username

        set_tag("bot.username", self._bot_username)
        self._start_span("process_update")

    async def on_post_process_update(self, *_, **__):
        self._finish_span()

    async def on_pre_process_message(self, message, *_, **__):
        self._save_base_context()
        self._start_span("process_message")
        set_context("message", message.to_python())

    async def on_post_process_message(self, *_, **__):
        self._finish_span()

    async def on_pre_process_edited_message(self, edited_message, *_, **__):
        self._save_base_context()
        self._start_span("process_edited_message")
        set_context("message", edited_message.to_python())

    async def on_post_process_edited_message(self, *_, **__):
        self._finish_span()

    async def on_pre_process_channel_post(self, channel_post, *_, **__):
        self._save_base_context()
        self._start_span("process_channel_post")
        set_context("message", channel_post.to_python())

    async def on_post_process_channel_post(self, *_, **__):
        self._finish_span()

    async def on_pre_process_edited_channel_post(self, edited_channel_post,
                                                 *_, **__):
        self._save_base_context()
        self._start_span("process_edited_channel_post")
        set_context("message", edited_channel_post.to_python())

    async def on_post_process_edited_channel_post(self, *_, **__):
        self._finish_span()

    async def on_pre_process_inline_query(self, inline_query, *_, **__):
        self._save_base_context()
        self._start_span("process_inline_query")
        set_context("message", inline_query.to_python())

    async def on_post_process_inline_query(self, *_, **__):
        self._finish_span()

    async def on_pre_process_chosen_inline_result(self, chosen_inline_result,
                                                  *_, **__):
        self._save_base_context()
        self._start_span("process_chosen_inline_result")
        set_context("inline_result", chosen_inline_result.to_python())

    async def on_post_process_chosen_inline_result(self, *_, **__):
        self._finish_span()

    async def on_pre_process_callback_query(self, callback_query, *_, **__):
        self._save_base_context()
        self._start_span("process_callback_query")
        set_context("callback_query", callback_query.to_python())

    async def on_post_process_callback_query(self, *_, **__):
        self._finish_span()

    async def on_pre_process_shipping_query(self, shipping_query, *_, **__):
        self._save_base_context()
        self._start_span("process_shipping_query")
        set_context("shipping_query", shipping_query.to_python())

    async def on_post_process_shipping_query(self, *_, **__):
        self._finish_span()

    async def on_pre_process_pre_checkout_query(self, pre_checkout_query, *_, **__):
        self._save_base_context()
        self._start_span("process_pre_checkout_query")
        set_context("pre_checkout_query", pre_checkout_query.to_python())

    async def on_post_process_pre_checkout_query(self, *_, **__):
        self._finish_span()

    async def on_pre_process_poll(self, poll, *_, **__):
        self._save_base_context()
        self._start_span("process_poll")
        set_context("poll", poll.to_python())

    async def on_post_process_poll(self, *_, **__):
        self._finish_span()

    async def on_pre_process_poll_answer(self, poll_answer, *_, **__):
        self._save_base_context()
        self._start_span("process_poll_answer")
        set_context("poll_answer", poll_answer.to_python())

    async def on_post_process_poll_answer(self, *_, **__):
        self._finish_span()

    @staticmethod
    def _start_span(name):
        """
        Trying to get current span, then:
         - if no span in progress, create new transaction;
         - if span exists - create new task span as child of current span;
        """
        span = Hub.current.scope.span
        if span is None:
            start_transaction(name=name)
        else:
            span.start_child(op=name)

    @staticmethod
    def _save_base_context():
        """ Saving contexts if User and Chat. """
        user = User.get_current()
        if isinstance(user, User):
            user_data = {"id": user.id}
            if user.username is not None:
                user_data["username"] = user.username
            set_user(user_data)
            set_context("user", user.to_python())

        chat = Chat.get_current()
        if isinstance(chat, Chat):
            set_context("chat", chat.to_python())

    @staticmethod
    def _finish_span():
        """ Finish current span. """
        span = Hub.current.scope.span
        if isinstance(span, Span):
            return span.finish()
