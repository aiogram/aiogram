import re
from typing import Any, Dict, Pattern, Tuple, Type, Union, cast

from pydantic import validator

from aiogram.dispatcher.filters import BaseFilter


class ExceptionTypeFilter(BaseFilter):
    exception: Union[Type[Exception], Tuple[Type[Exception]]]

    class Config:
        arbitrary_types_allowed = True

    async def __call__(self, exception: Exception) -> Union[bool, Dict[str, Any]]:
        return isinstance(exception, self.exception)


class ExceptionMessageFilter(BaseFilter):
    match: Union[str, Pattern[str]]

    class Config:
        arbitrary_types_allowed = True

    @validator("match")
    def _validate_match(cls, value: Union[str, Pattern[str]]) -> Union[str, Pattern[str]]:
        if isinstance(value, str):
            return re.compile(value)
        return value

    async def __call__(self, exception: Exception) -> Union[bool, Dict[str, Any]]:
        pattern = cast(Pattern[str], self.match)
        result = pattern.match(str(exception))
        if not result:
            return False
        return {"match_exception": result}
