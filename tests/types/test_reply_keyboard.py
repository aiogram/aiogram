from aiogram import types
from .dataset import REPLY_KEYBOARD_MARKUP

reply_keyboard = types.ReplyKeyboardMarkup(**REPLY_KEYBOARD_MARKUP)


def test_serialize():
    assert reply_keyboard.to_python() == REPLY_KEYBOARD_MARKUP


def test_deserialize():
    assert reply_keyboard.to_object(reply_keyboard.to_python()) == reply_keyboard
