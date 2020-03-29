from typing import Any, Dict, Optional, Sequence, Union

from pydantic import root_validator

from aiogram.api.types import CallbackQuery, InlineQuery, Message, Poll
from aiogram.dispatcher.filters import BaseFilter

TextType = str


class Text(BaseFilter):
    """
    Is useful for filtering text Message, any CallbackQuery with `data`,
    InlineQuery or Poll question.
    """

    text: Optional[Union[Sequence[TextType], TextType]] = None
    text_contains: Optional[Union[Sequence[TextType], TextType]] = None
    text_startswith: Optional[Union[Sequence[TextType], TextType]] = None
    text_endswith: Optional[Union[Sequence[TextType], TextType]] = None
    text_ignore_case: bool = False

    @root_validator
    def _validate_constraints(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # Validate that only one text filter type is presented
        used_args = set(
            key for key, value in values.items() if key != "text_ignore_case" and value is not None
        )
        if len(used_args) < 1:
            raise ValueError(
                "Filter should contain one of arguments: {'text', 'text_contains', 'text_startswith', 'text_endswith'}"
            )
        if len(used_args) > 1:
            raise ValueError(f"Arguments {used_args} cannot be used together")

        # Convert single value to list
        for arg in used_args:
            if isinstance(values[arg], str):
                values[arg] = [values[arg]]

        return values

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
        if self.text_ignore_case:
            text = text.lower()

        if self.text is not None:
            equals = list(map(self.prepare_text, self.text))
            return text in equals

        if self.text_contains is not None:
            contains = list(map(self.prepare_text, self.text_contains))
            return all(map(text.__contains__, contains))

        if self.text_startswith is not None:
            startswith = list(map(self.prepare_text, self.text_startswith))
            return any(map(text.startswith, startswith))

        if self.text_endswith is not None:
            endswith = list(map(self.prepare_text, self.text_endswith))
            return any(map(text.endswith, endswith))

        # Impossible because the validator prevents this situation
        return False  # pragma: no cover

    def prepare_text(self, text: str) -> str:
        if self.text_ignore_case:
            return str(text).lower()
        else:
            return str(text)
