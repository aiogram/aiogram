import re
from typing import Any, Dict, Pattern, Type, Union, cast

from aiogram.filters.base import Filter
from aiogram.types import TelegramObject
from aiogram.types.error_event import ErrorEvent


class ExceptionTypeFilter(Filter):
    """
    Allows to match exception by type
    """

    def __init__(self, *exceptions: Type[Exception]):
        """
        :param exceptions: Exception type(s)
        """
        if not exceptions:
            raise ValueError("At least one exception type is required")
        self.exceptions = exceptions

    async def __call__(self, obj: TelegramObject) -> Union[bool, Dict[str, Any]]:
        return isinstance(cast(ErrorEvent, obj).exception, self.exceptions)


class ExceptionMessageFilter(Filter):
    """
    Allow to match exception by message
    """

    def __init__(self, pattern: Union[str, Pattern[str]]):
        """
        :param pattern: Regexp pattern
        """
        if not isinstance(pattern, str):
            pattern = re.compile(pattern)
        self.pattern = pattern

    async def __call__(
        self,
        obj: TelegramObject,
    ) -> Union[bool, Dict[str, Any]]:
        pattern = cast(Pattern[str], self.pattern)
        result = pattern.match(str(cast(ErrorEvent, obj).exception))
        if not result:
            return False
        return {"match_exception": result}
