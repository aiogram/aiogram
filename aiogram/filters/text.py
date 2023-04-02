from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence, Union

from aiogram.filters.base import Filter
from aiogram.types import CallbackQuery, InlineQuery, Message, Poll

if TYPE_CHECKING:
    from aiogram.utils.i18n.lazy_proxy import LazyProxy  # NOQA

TextType = Union[str, "LazyProxy"]


class Text(Filter):
    """
    Is useful for filtering text :class:`aiogram.types.message.Message`,
    any :class:`aiogram.types.callback_query.CallbackQuery` with `data`,
    :class:`aiogram.types.inline_query.InlineQuery` or :class:`aiogram.types.poll.Poll` question.

    .. warning::

        Only one of `text`, `contains`, `startswith` or `endswith` argument can be used at once.
        Any of that arguments can be string, list, set or tuple of strings.

    .. deprecated:: 3.0

        use :ref:`magic-filter <magic-filters>`. For example do :pycode:`F.text == "text"` instead
    """

    __slots__ = (
        "text",
        "contains",
        "startswith",
        "endswith",
        "ignore_case",
    )

    def __init__(
        self,
        text: Optional[Union[Sequence[TextType], TextType]] = None,
        *,
        contains: Optional[Union[Sequence[TextType], TextType]] = None,
        startswith: Optional[Union[Sequence[TextType], TextType]] = None,
        endswith: Optional[Union[Sequence[TextType], TextType]] = None,
        ignore_case: bool = False,
    ):
        """

        :param text: Text equals value or one of values
        :param contains: Text contains value or one of values
        :param startswith: Text starts with value or one of values
        :param endswith: Text ends with value or one of values
        :param ignore_case: Ignore case when checks
        """
        self._validate_constraints(
            text=text,
            contains=contains,
            startswith=startswith,
            endswith=endswith,
        )
        self.text = self._prepare_argument(text)
        self.contains = self._prepare_argument(contains)
        self.startswith = self._prepare_argument(startswith)
        self.endswith = self._prepare_argument(endswith)
        self.ignore_case = ignore_case

    def __str__(self) -> str:
        return self._signature_to_string(
            text=self.text,
            contains=self.contains,
            startswith=self.startswith,
            endswith=self.endswith,
            ignore_case=self.ignore_case,
        )

    @classmethod
    def _prepare_argument(
        cls, value: Optional[Union[Sequence[TextType], TextType]]
    ) -> Optional[Sequence[TextType]]:
        from aiogram.utils.i18n.lazy_proxy import LazyProxy

        if isinstance(value, (str, LazyProxy)):
            return [value]
        return value

    @classmethod
    def _validate_constraints(cls, **values: Any) -> None:
        # Validate that only one text filter type is presented
        used_args = {key for key, value in values.items() if value is not None}
        if len(used_args) < 1:
            raise ValueError(f"Filter should contain one of arguments: {set(values.keys())}")
        if len(used_args) > 1:
            raise ValueError(f"Arguments {used_args} cannot be used together")

    async def __call__(
        self, obj: Union[Message, CallbackQuery, InlineQuery, Poll]
    ) -> Union[bool, Dict[str, Any]]:
        if isinstance(obj, Message):
            text = obj.text or obj.caption or ""
            if not text and obj.poll:
                text = obj.poll.question
        elif isinstance(obj, CallbackQuery) and obj.data:
            text = obj.data
        elif isinstance(obj, InlineQuery):
            text = obj.query
        elif isinstance(obj, Poll):
            text = obj.question
        else:
            return False

        if not text:
            return False
        if self.ignore_case:
            text = text.lower()

        if self.text is not None:
            equals = map(self.prepare_text, self.text)
            return text in equals

        if self.contains is not None:
            contains = map(self.prepare_text, self.contains)
            return all(map(text.__contains__, contains))

        if self.startswith is not None:
            startswith = map(self.prepare_text, self.startswith)
            return any(map(text.startswith, startswith))

        if self.endswith is not None:
            endswith = map(self.prepare_text, self.endswith)
            return any(map(text.endswith, endswith))

        # Impossible because the validator prevents this situation
        return False  # pragma: no cover

    def prepare_text(self, text: str) -> str:
        if self.ignore_case:
            return str(text).lower()
        return str(text)
