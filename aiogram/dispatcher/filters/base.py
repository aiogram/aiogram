from abc import ABC, abstractmethod
from typing import (
    Awaitable,
    Callable,
    Any,
    Dict,
    Union,
)

from pydantic import BaseModel


async def _call_for_override(*args: Any, **kwargs: Any) -> Union[bool, Dict[str, Any]]:  # pragma: no cover
    pass


class BaseFilter(ABC, BaseModel):
    # This little hack with typehint is needed because mypy checks validity of overrides and raises:
    # error: Signature of "__call__" incompatible with supertype "BaseFilter"  [override]
    # https://mypy.readthedocs.io/en/latest/error_code_list.html#check-validity-of-overrides-override
    __call__: Callable[..., Awaitable[Union[bool, Dict[str, Any]]]] = _call_for_override
    abstractmethod(__call__)

    def __await__(self):  # type: ignore  # pragma: no cover
        # Is needed only for inspection and this method is never be called
        return self.__call__
