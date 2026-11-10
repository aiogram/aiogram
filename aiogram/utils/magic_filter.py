import warnings
from collections.abc import Iterable
from typing import Any

from magic_filter import MagicFilter as _MagicFilter
from magic_filter import MagicT as _MagicT
from magic_filter.operations import BaseOperation

_WARN_OR = (
    "Possible operator precedence mistake: {value!r} is on the left side of '|'.\n"
    "Because '|' binds tighter than '==', the expression\n"
    "    F.x == 'a' | F.x == 'b'\n"
    "is parsed by Python as:\n"
    "    F.x == ('a' | F.x) == 'b'   # likely not what you intended\n"
    "Correct forms:\n"
    "    (F.x == 'a') | (F.x == 'b')\n"
    "    F.x.in_({{'a', 'b'}})"
)

_WARN_AND = (
    "Possible operator precedence mistake: {value!r} is on the left side of '&'.\n"
    "Because '&' binds tighter than '==', the expression\n"
    "    F.x == 'a' & F.y == 'b'\n"
    "is parsed by Python as:\n"
    "    F.x == ('a' & F.y) == 'b'   # likely not what you intended\n"
    "Correct form:\n"
    "    (F.x == 'a') & (F.y == 'b')"
)


class AsFilterResultOperation(BaseOperation):
    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        self.name = name

    def resolve(self, value: Any, initial_value: Any) -> Any:
        if value is None or (isinstance(value, Iterable) and not value):
            return None
        return {self.name: value}


class MagicFilter(_MagicFilter):
    def as_(self: _MagicT, name: str) -> _MagicT:
        return self._extend(AsFilterResultOperation(name=name))

    def __ror__(self: _MagicT, other: Any) -> _MagicT:
        if not isinstance(other, _MagicFilter):
            warnings.warn(
                message=_WARN_OR.format(value=other),
                category=UserWarning,
                stacklevel=2,
            )
        return super().__ror__(other)

    def __rand__(self: _MagicT, other: Any) -> _MagicT:
        if not isinstance(other, _MagicFilter):
            warnings.warn(
                message=_WARN_AND.format(value=other),
                category=UserWarning,
                stacklevel=2,
            )
        return super().__rand__(other)
