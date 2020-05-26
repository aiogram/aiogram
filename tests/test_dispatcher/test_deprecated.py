import pytest

from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.dispatcher.router import Router
from tests.deprecated import check_deprecated

OBSERVERS = {
    "callback_query",
    "channel_post",
    "chosen_inline_result",
    "edited_channel_post",
    "edited_message",
    "errors",
    "inline_query",
    "message",
    "poll",
    "poll_answer",
    "pre_checkout_query",
    "shipping_query",
    "update",
}

DEPRECATED_OBSERVERS = {observer + "_handler" for observer in OBSERVERS}


@pytest.mark.parametrize("observer_name", DEPRECATED_OBSERVERS)
def test_deprecated_handlers_name(observer_name: str):
    router = Router()

    with check_deprecated("3.2", exception=AttributeError):
        observer = getattr(router, observer_name)
        assert isinstance(observer, TelegramEventObserver)
