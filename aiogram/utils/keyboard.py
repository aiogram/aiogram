from __future__ import annotations

from abc import ABC
from copy import deepcopy
from itertools import chain
from itertools import cycle as repeat_all
from typing import (
    TYPE_CHECKING,
    Any,
    Generator,
    Generic,
    Iterable,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    CallbackGame,
    CopyTextButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonPollType,
    KeyboardButtonRequestChat,
    KeyboardButtonRequestUsers,
    LoginUrl,
    ReplyKeyboardMarkup,
    SwitchInlineQueryChosenChat,
    WebAppInfo,
)

ButtonType = TypeVar("ButtonType", InlineKeyboardButton, KeyboardButton)
T = TypeVar("T")


class KeyboardBuilder(Generic[ButtonType], ABC):
    """
    Generic keyboard builder that helps to adjust your markup with defined shape of lines.

    Works both of InlineKeyboardMarkup and ReplyKeyboardMarkup.
    """

    max_width: int = 0
    min_width: int = 0
    max_buttons: int = 0

    def __init__(
        self, button_type: Type[ButtonType], markup: Optional[List[List[ButtonType]]] = None
    ) -> None:
        if not issubclass(button_type, (InlineKeyboardButton, KeyboardButton)):
            raise ValueError(f"Button type {button_type} are not allowed here")
        self._button_type: Type[ButtonType] = button_type
        if markup:
            self._validate_markup(markup)
        else:
            markup = []
        self._markup: List[List[ButtonType]] = markup

    @property
    def buttons(self) -> Generator[ButtonType, None, None]:
        """
        Get flatten set of all buttons

        :return:
        """
        yield from chain.from_iterable(self.export())

    def _validate_button(self, button: ButtonType) -> bool:
        """
        Check that button item has correct type

        :param button:
        :return:
        """
        allowed = self._button_type
        if not isinstance(button, allowed):
            raise ValueError(
                f"{button!r} should be type {allowed.__name__!r} not {type(button).__name__!r}"
            )
        return True

    def _validate_buttons(self, *buttons: ButtonType) -> bool:
        """
        Check that all passed button has correct type

        :param buttons:
        :return:
        """
        return all(map(self._validate_button, buttons))

    def _validate_row(self, row: List[ButtonType]) -> bool:
        """
        Check that row of buttons are correct
        Row can be only list of allowed button types and has length 0 <= n <= 8

        :param row:
        :return:
        """
        if not isinstance(row, list):
            raise ValueError(
                f"Row {row!r} should be type 'List[{self._button_type.__name__}]' "
                f"not type {type(row).__name__}"
            )
        if len(row) > self.max_width:
            raise ValueError(f"Row {row!r} is too long (max width: {self.max_width})")
        self._validate_buttons(*row)
        return True

    def _validate_markup(self, markup: List[List[ButtonType]]) -> bool:
        """
        Check that passed markup has correct data structure
        Markup is list of lists of buttons

        :param markup:
        :return:
        """
        count = 0
        if not isinstance(markup, list):
            raise ValueError(
                f"Markup should be type 'List[List[{self._button_type.__name__}]]' "
                f"not type {type(markup).__name__!r}"
            )
        for row in markup:
            self._validate_row(row)
            count += len(row)
        if count > self.max_buttons:
            raise ValueError(f"Too much buttons detected Max allowed count - {self.max_buttons}")
        return True

    def _validate_size(self, size: Any) -> int:
        """
        Validate that passed size is legit

        :param size:
        :return:
        """
        if not isinstance(size, int):
            raise ValueError("Only int sizes are allowed")
        if size not in range(self.min_width, self.max_width + 1):
            raise ValueError(
                f"Row size {size} is not allowed, range: [{self.min_width}, {self.max_width}]"
            )
        return size

    def export(self) -> List[List[ButtonType]]:
        """
        Export configured markup as list of lists of buttons

        .. code-block:: python

            >>> builder = KeyboardBuilder(button_type=InlineKeyboardButton)
            >>> ... # Add buttons to builder
            >>> markup = InlineKeyboardMarkup(inline_keyboard=builder.export())

        :return:
        """
        return deepcopy(self._markup)

    def add(self, *buttons: ButtonType) -> "KeyboardBuilder[ButtonType]":
        """
        Add one or many buttons to markup.

        :param buttons:
        :return:
        """
        self._validate_buttons(*buttons)
        markup = self.export()

        # Try to add new buttons to the end of last row if it possible
        if markup and len(markup[-1]) < self.max_width:
            last_row = markup[-1]
            pos = self.max_width - len(last_row)
            head, buttons = buttons[:pos], buttons[pos:]
            last_row.extend(head)

        # Separate buttons to exclusive rows with max possible row width
        if self.max_width > 0:
            while buttons:
                row, buttons = buttons[: self.max_width], buttons[self.max_width :]
                markup.append(list(row))
        else:
            markup.append(list(buttons))

        self._markup = markup
        return self

    def row(
        self, *buttons: ButtonType, width: Optional[int] = None
    ) -> "KeyboardBuilder[ButtonType]":
        """
        Add row to markup

        When too much buttons is passed it will be separated to many rows

        :param buttons:
        :param width:
        :return:
        """
        if width is None:
            width = self.max_width

        self._validate_size(width)
        self._validate_buttons(*buttons)
        self._markup.extend(
            list(buttons[pos : pos + width]) for pos in range(0, len(buttons), width)
        )
        return self

    def adjust(self, *sizes: int, repeat: bool = False) -> "KeyboardBuilder[ButtonType]":
        """
        Adjust previously added buttons to specific row sizes.

        By default, when the sum of passed sizes is lower than buttons count the last
        one size will be used for tail of the markup.
        If repeat=True is passed - all sizes will be cycled when available more buttons
        count than all sizes

        :param sizes:
        :param repeat:
        :return:
        """
        if not sizes:
            sizes = (self.max_width,)

        validated_sizes = map(self._validate_size, sizes)
        sizes_iter = repeat_all(validated_sizes) if repeat else repeat_last(validated_sizes)
        size = next(sizes_iter)

        markup = []
        row: List[ButtonType] = []
        for button in self.buttons:
            if len(row) >= size:
                markup.append(row)
                size = next(sizes_iter)
                row = []
            row.append(button)
        if row:
            markup.append(row)
        self._markup = markup
        return self

    def _button(self, **kwargs: Any) -> "KeyboardBuilder[ButtonType]":
        """
        Add button to markup

        :param kwargs:
        :return:
        """
        if isinstance(callback_data := kwargs.get("callback_data", None), CallbackData):
            kwargs["callback_data"] = callback_data.pack()
        button = self._button_type(**kwargs)
        return self.add(button)

    def as_markup(self, **kwargs: Any) -> Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]:
        if self._button_type is KeyboardButton:
            keyboard = cast(List[List[KeyboardButton]], self.export())  # type: ignore
            return ReplyKeyboardMarkup(keyboard=keyboard, **kwargs)
        inline_keyboard = cast(List[List[InlineKeyboardButton]], self.export())  # type: ignore
        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    def attach(self, builder: "KeyboardBuilder[ButtonType]") -> "KeyboardBuilder[ButtonType]":
        if not isinstance(builder, KeyboardBuilder):
            raise ValueError(f"Only KeyboardBuilder can be attached, not {type(builder).__name__}")
        if builder._button_type is not self._button_type:
            raise ValueError(
                f"Only builders with same button type can be attached, "
                f"not {self._button_type.__name__} and {builder._button_type.__name__}"
            )
        self._markup.extend(builder.export())
        return self


def repeat_last(items: Iterable[T]) -> Generator[T, None, None]:
    items_iter = iter(items)
    try:
        value = next(items_iter)
    except StopIteration:  # pragma: no cover
        # Possible case but not in place where this function is used
        return
    yield value
    finished = False
    while True:
        if not finished:
            try:
                value = next(items_iter)
            except StopIteration:
                finished = True
        yield value


class InlineKeyboardBuilder(KeyboardBuilder[InlineKeyboardButton]):
    """
    Inline keyboard builder inherits all methods from generic builder
    """

    max_width: int = 8
    min_width: int = 1
    max_buttons: int = 100

    def button(
        self,
        *,
        text: str,
        url: Optional[str] = None,
        callback_data: Optional[Union[str, CallbackData]] = None,
        web_app: Optional[WebAppInfo] = None,
        login_url: Optional[LoginUrl] = None,
        switch_inline_query: Optional[str] = None,
        switch_inline_query_current_chat: Optional[str] = None,
        switch_inline_query_chosen_chat: Optional[SwitchInlineQueryChosenChat] = None,
        copy_text: Optional[CopyTextButton] = None,
        callback_game: Optional[CallbackGame] = None,
        pay: Optional[bool] = None,
        **kwargs: Any,
    ) -> "InlineKeyboardBuilder":
        return cast(
            InlineKeyboardBuilder,
            self._button(
                text=text,
                url=url,
                callback_data=callback_data,
                web_app=web_app,
                login_url=login_url,
                switch_inline_query=switch_inline_query,
                switch_inline_query_current_chat=switch_inline_query_current_chat,
                switch_inline_query_chosen_chat=switch_inline_query_chosen_chat,
                copy_text=copy_text,
                callback_game=callback_game,
                pay=pay,
                **kwargs,
            ),
        )

    if TYPE_CHECKING:

        def as_markup(self, **kwargs: Any) -> InlineKeyboardMarkup:
            """Construct an InlineKeyboardMarkup"""
            ...

    def __init__(self, markup: Optional[List[List[InlineKeyboardButton]]] = None) -> None:
        super().__init__(button_type=InlineKeyboardButton, markup=markup)

    def copy(self: "InlineKeyboardBuilder") -> "InlineKeyboardBuilder":
        """
        Make full copy of current builder with markup

        :return:
        """
        return InlineKeyboardBuilder(markup=self.export())

    @classmethod
    def from_markup(
        cls: Type["InlineKeyboardBuilder"], markup: InlineKeyboardMarkup
    ) -> "InlineKeyboardBuilder":
        """
        Create builder from existing markup

        :param markup:
        :return:
        """
        return cls(markup=markup.inline_keyboard)


class ReplyKeyboardBuilder(KeyboardBuilder[KeyboardButton]):
    """
    Reply keyboard builder inherits all methods from generic builder
    """

    max_width: int = 10
    min_width: int = 1
    max_buttons: int = 300

    def button(
        self,
        *,
        text: str,
        request_users: Optional[KeyboardButtonRequestUsers] = None,
        request_chat: Optional[KeyboardButtonRequestChat] = None,
        request_contact: Optional[bool] = None,
        request_location: Optional[bool] = None,
        request_poll: Optional[KeyboardButtonPollType] = None,
        web_app: Optional[WebAppInfo] = None,
        **kwargs: Any,
    ) -> "ReplyKeyboardBuilder":
        return cast(
            ReplyKeyboardBuilder,
            self._button(
                text=text,
                request_users=request_users,
                request_chat=request_chat,
                request_contact=request_contact,
                request_location=request_location,
                request_poll=request_poll,
                web_app=web_app,
                **kwargs,
            ),
        )

    if TYPE_CHECKING:

        def as_markup(self, **kwargs: Any) -> ReplyKeyboardMarkup: ...

    def __init__(self, markup: Optional[List[List[KeyboardButton]]] = None) -> None:
        super().__init__(button_type=KeyboardButton, markup=markup)

    def copy(self: "ReplyKeyboardBuilder") -> "ReplyKeyboardBuilder":
        """
        Make full copy of current builder with markup

        :return:
        """
        return ReplyKeyboardBuilder(markup=self.export())

    @classmethod
    def from_markup(cls, markup: ReplyKeyboardMarkup) -> "ReplyKeyboardBuilder":
        """
        Create builder from existing markup

        :param markup:
        :return:
        """
        return cls(markup=markup.keyboard)
