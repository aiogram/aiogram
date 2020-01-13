from typing import Any, Dict, List, Optional, Union

from pydantic import validator

from ...api.types import Message
from ...api.types.message import ContentType
from .base import BaseFilter


class ContentTypesFilter(BaseFilter):
    content_types: Optional[List[str]] = None

    @validator("content_types")
    def _validate_content_types(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if not value:
            value = [ContentType.TEXT]
        allowed_content_types = set(ContentType.all())
        bad_content_types = set(value) - allowed_content_types
        if bad_content_types:
            raise ValueError(f"Invalid content types {bad_content_types} is not allowed here")
        return value

    async def __call__(self, message: Message) -> Union[bool, Dict[str, Any]]:
        if not self.content_types:  # pragma: no cover
            # Is impossible but needed for valid typechecking
            self.content_types = [ContentType.TEXT]
        return ContentType.ANY in self.content_types or message.content_type in self.content_types
