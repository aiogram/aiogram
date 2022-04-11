import pytest

from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.dispatcher.router import Router
from tests.deprecated import check_deprecated

OBSERVERS = {
    "message",
    "edited_message",
    "channel_post",
    "edited_channel_post",
    "inline_query",
    "chosen_inline_result",
    "callback_query",
    "shipping_query",
    "pre_checkout_query",
    "poll",
    "poll_answer",
    "my_chat_member",
    "chat_member",
    "chat_join_request",
    "errors",
}


@pytest.mark.parametrize("observer_name", OBSERVERS)
def test_deprecated_handlers_name(observer_name: str):
    router = Router()

    with check_deprecated("3.2", exception=AttributeError):
        observer = getattr(router, f"{observer_name}_handler")
        assert isinstance(observer, TelegramEventObserver)


@pytest.mark.parametrize("observer_name", OBSERVERS)
def test_deprecated_register_handlers(observer_name: str):
    router = Router()

    with check_deprecated("3.2", exception=AttributeError):
        register = getattr(router, f"register_{observer_name}")
        register(lambda event: True)
        assert callable(register)
