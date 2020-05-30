import pytest

from aiogram.api.types import InlineKeyboardButton, InlineKeyboardMarkup

test_row_width = [1, 2, 3, 10]
test_inline_keyboard = [
    [],
    [
        [
            InlineKeyboardButton(text="foo", url="https://google.com"),
            InlineKeyboardButton(text="foo", url="https://google.com"),
        ]
    ],
]


class TestInlineKeyboardMarkup:
    @pytest.mark.parametrize("row_width", test_row_width)
    def test_keyboard_markup_add(self, row_width):
        kwargs = dict(row_width=row_width, inline_keyboard=[])

        button = InlineKeyboardButton(text="foo", url="https://google.com")

        keyboard_markup = InlineKeyboardMarkup(**kwargs)

        api_method = keyboard_markup.add(button)

        assert button in api_method.inline_keyboard[0]

    @pytest.mark.parametrize("row_width", test_row_width)
    def test_keyboard_markup_row(self, row_width):
        kwargs = dict(row_width=row_width, inline_keyboard=[])
        buttons = [
            InlineKeyboardButton(text="foo", url="https://google.com"),
            InlineKeyboardButton(text="bar", callback_data="test"),
        ]

        keyboard_markup = InlineKeyboardMarkup(**kwargs)

        api_method = keyboard_markup.row(*buttons)

        assert buttons == api_method.inline_keyboard[0]

    @pytest.mark.parametrize("row_width", test_row_width)
    @pytest.mark.parametrize("inline_keyboard", test_inline_keyboard)
    def test_keyboard_markup_insert(self, row_width, inline_keyboard):
        kwargs = dict(row_width=row_width, inline_keyboard=inline_keyboard)
        button = InlineKeyboardButton(text="foo", url="https://google.com")

        keyboard_markup = InlineKeyboardMarkup(**kwargs)

        api_method = keyboard_markup.insert(button)

        assert button in api_method.inline_keyboard[0]
