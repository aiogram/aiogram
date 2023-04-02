import pytest

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import (
    InlineKeyboardBuilder,
    KeyboardBuilder,
    ReplyKeyboardBuilder,
)


class MyCallback(CallbackData, prefix="test"):
    value: str


class TestKeyboardBuilder:
    def test_init(self):
        with pytest.raises(ValueError):
            KeyboardBuilder(button_type=object)

    def test_init_success(self):
        builder = KeyboardBuilder(button_type=KeyboardButton)
        assert builder._button_type is KeyboardButton
        builder = InlineKeyboardBuilder()
        assert builder._button_type is InlineKeyboardButton
        builder = ReplyKeyboardBuilder()
        assert builder._button_type is KeyboardButton

    def test_validate_button(self):
        builder = InlineKeyboardBuilder()
        with pytest.raises(ValueError):
            builder._validate_button(button=object())
        with pytest.raises(ValueError):
            builder._validate_button(button=KeyboardButton(text="test"))
        assert builder._validate_button(
            button=InlineKeyboardButton(text="test", callback_data="callback")
        )

    def test_validate_buttons(self):
        builder = InlineKeyboardBuilder()
        with pytest.raises(ValueError):
            builder._validate_buttons(object(), object())
        with pytest.raises(ValueError):
            builder._validate_buttons(KeyboardButton(text="test"))
        with pytest.raises(ValueError):
            builder._validate_buttons(
                InlineKeyboardButton(text="test", callback_data="callback"),
                KeyboardButton(text="test"),
            )
        assert builder._validate_button(
            InlineKeyboardButton(text="test", callback_data="callback")
        )

    def test_validate_row(self):
        builder = ReplyKeyboardBuilder()

        with pytest.raises(ValueError):
            assert builder._validate_row(
                row=(KeyboardButton(text=f"test {index}") for index in range(10))
            )

        with pytest.raises(ValueError):
            assert builder._validate_row(
                row=[KeyboardButton(text=f"test {index}") for index in range(10)]
            )

        for count in range(9):
            assert builder._validate_row(
                row=[KeyboardButton(text=f"test {index}") for index in range(count)]
            )

    def test_validate_markup(self):
        builder = ReplyKeyboardBuilder()

        with pytest.raises(ValueError):
            builder._validate_markup(markup=())

        with pytest.raises(ValueError):
            builder._validate_markup(
                markup=[
                    [KeyboardButton(text=f"{row}.{col}") for col in range(8)] for row in range(15)
                ]
            )

        assert builder._validate_markup(
            markup=[[KeyboardButton(text=f"{row}.{col}") for col in range(8)] for row in range(8)]
        )

    def test_validate_size(self):
        builder = ReplyKeyboardBuilder()
        with pytest.raises(ValueError):
            builder._validate_size(None)
        with pytest.raises(ValueError):
            builder._validate_size(2.0)

        with pytest.raises(ValueError):
            builder._validate_size(0)

        with pytest.raises(ValueError):
            builder._validate_size(10)
        for size in range(1, 9):
            builder._validate_size(size)

    def test_export(self):
        builder = ReplyKeyboardBuilder(markup=[[KeyboardButton(text="test")]])
        markup = builder.export()
        assert id(builder._markup) != id(markup)

        markup.clear()
        assert len(builder._markup) == 1
        assert len(markup) == 0

    @pytest.mark.parametrize(
        "builder,button",
        [
            [
                ReplyKeyboardBuilder(markup=[[KeyboardButton(text="test")]]),
                KeyboardButton(text="test2"),
            ],
            [
                InlineKeyboardBuilder(markup=[[InlineKeyboardButton(text="test")]]),
                InlineKeyboardButton(text="test2"),
            ],
            [
                KeyboardBuilder(
                    button_type=InlineKeyboardButton, markup=[[InlineKeyboardButton(text="test")]]
                ),
                InlineKeyboardButton(text="test2"),
            ],
        ],
    )
    def test_copy(self, builder, button):
        builder1 = builder
        builder2 = builder1.copy()
        assert builder1 != builder2

        builder1.add(button)
        builder2.row(button)

        markup1 = builder1.export()
        markup2 = builder2.export()
        assert markup1 != markup2

        assert len(markup1) == 1
        assert len(markup2) == 2
        assert len(markup1[0]) == 2
        assert len(markup2[0]) == 1

    @pytest.mark.parametrize(
        "count,rows,last_columns",
        [[0, 0, 0], [3, 1, 3], [8, 1, 8], [9, 2, 1], [16, 2, 8], [19, 3, 3]],
    )
    def test_add(self, count: int, rows: int, last_columns: int):
        builder = ReplyKeyboardBuilder()

        for index in range(count):
            builder.add(KeyboardButton(text=f"btn-{index}"))
        markup = builder.export()

        assert len(list(builder.buttons)) == count
        assert len(markup) == rows
        if last_columns:
            assert len(markup[-1]) == last_columns

    def test_row(
        self,
    ):
        builder = ReplyKeyboardBuilder(markup=[[KeyboardButton(text="test")]])
        builder.row(*(KeyboardButton(text=f"test-{index}") for index in range(10)), width=3)
        markup = builder.export()
        assert len(markup) == 5

    @pytest.mark.parametrize(
        "count,repeat,sizes,shape",
        [
            [0, False, [], []],
            [0, False, [2], []],
            [1, False, [2], [1]],
            [3, False, [2], [2, 1]],
            [10, False, [], [8, 2]],
            [10, False, [3, 2, 1], [3, 2, 1, 1, 1, 1, 1]],
            [12, True, [3, 2, 1], [3, 2, 1, 3, 2, 1]],
        ],
    )
    def test_adjust(self, count, repeat, sizes, shape):
        builder = ReplyKeyboardBuilder()
        builder.row(*(KeyboardButton(text=f"test-{index}") for index in range(count)))
        builder.adjust(*sizes, repeat=repeat)
        markup = builder.export()

        assert len(markup) == len(shape)
        for row, expected_size in zip(markup, shape):
            assert len(row) == expected_size

    @pytest.mark.parametrize(
        "builder_type,kwargs,expected",
        [
            [ReplyKeyboardBuilder, dict(text="test"), KeyboardButton(text="test")],
            [
                InlineKeyboardBuilder,
                dict(text="test", callback_data="callback"),
                InlineKeyboardButton(text="test", callback_data="callback"),
            ],
            [
                InlineKeyboardBuilder,
                dict(text="test", callback_data=MyCallback(value="test")),
                InlineKeyboardButton(text="test", callback_data="test:test"),
            ],
        ],
    )
    def test_button(self, builder_type, kwargs, expected):
        builder = builder_type()
        builder.button(**kwargs)
        markup = builder.export()
        assert markup[0][0] == expected

    @pytest.mark.parametrize(
        "builder,expected",
        [
            [ReplyKeyboardBuilder(), ReplyKeyboardMarkup],
            [InlineKeyboardBuilder(), InlineKeyboardMarkup],
        ],
    )
    def test_as_markup(self, builder, expected):
        assert isinstance(builder.as_markup(), expected)
