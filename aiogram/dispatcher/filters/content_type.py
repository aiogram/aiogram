from typing import Any, Dict, List, Optional, Union

from pydantic import root_validator

from ...api.types import Message
from ...api.types.message import ContentType
from .base import BaseFilter


class ContentTypesFilter(BaseFilter):
    content_types: Optional[List[str]] = None

    @root_validator
    def validate_constraints(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "content_types" not in values or not values["content_types"]:
            values["content_types"] = [ContentType.TEXT]
        allowed_content_types = set(ContentType.all())
        bad_content_types = set(values["content_types"]) - allowed_content_types
        if bad_content_types:
            raise ValueError(f"Invalid content types {bad_content_types} is not allowed here")
        return values

    async def __call__(self, message: Message) -> Union[bool, Dict[str, Any]]:
        if not self.content_types:
            return False
        return ContentType.ANY in self.content_types or message.content_type in self.content_types
