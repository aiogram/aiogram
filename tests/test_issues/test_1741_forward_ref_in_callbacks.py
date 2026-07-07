from sys import version_info
from typing import TYPE_CHECKING

import pytest

from aiogram.dispatcher.event.handler import HandlerObject


@pytest.mark.skipif(
    version_info < (3, 14), reason="Requires Python >=3.14 for TypeError on unresolved ForwardRef"
)
def test_forward_ref_in_callback():
    if TYPE_CHECKING:
        from aiogram.types import Message

    def my_handler(message: Message):
        pass

    HandlerObject(callback=my_handler)


def test_forward_ref_in_callback_with_str_annotation():
    def my_handler(message: "Message"):
        pass

    handler = HandlerObject(callback=my_handler)
    assert "message" in handler.params
