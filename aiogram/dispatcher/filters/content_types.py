from typing import Any, Dict, Optional, Sequence, Union

from pydantic import validator

from aiogram.types.message import ContentType

from ...types import Message
from .base import BaseFilter


class ContentTypesFilter(BaseFilter):
    """
    Is useful for handling specific types of messages (For example separate text and stickers handlers).
    """

    content_types: Union[Sequence[str], str]
    """Sequence of allowed content types"""

    @validator("content_types")
    def _validate_content_types(
        cls, value: Optional[Union[Sequence[str], str]]
    ) -> Optional[Sequence[str]]:
        if not value:
            return value
        if isinstance(value, str):
            value = [value]
        allowed_content_types = set(ContentType.all())
        bad_content_types = set(value) - allowed_content_types
        if bad_content_types:
            raise ValueError(f"Invalid content types {bad_content_types} is not allowed here")
        return value

    async def __call__(self, message: Message) -> Union[bool, Dict[str, Any]]:
        return ContentType.ANY in self.content_types or message.content_type in self.content_types
