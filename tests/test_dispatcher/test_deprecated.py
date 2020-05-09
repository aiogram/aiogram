import pytest

from aiogram.dispatcher.event.observer import TelegramEventObserver
from aiogram.dispatcher.router import Router

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


def test_deprecated_handlers_name():
    from aiogram import __version__

    minor_partial = int(__version__.split(".")[1])

    if minor_partial >= 2:
        do_assert = pytest.raises(AttributeError)
    else:
        do_assert = pytest.warns(DeprecationWarning)

    router = Router()

    async def _(__):
        ...

    with do_assert:
        for decor in OBSERVERS:
            getattr(router, decor + "_handler")

        assert all(
            isinstance(getattr(router, handler + "_handler"), TelegramEventObserver)
            for handler in OBSERVERS
        )

    assert all(
        isinstance(getattr(router, handler), TelegramEventObserver) for handler in OBSERVERS
    )
