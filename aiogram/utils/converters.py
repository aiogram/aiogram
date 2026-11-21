"""
Converters for typed FSM data and callback data: the declarations users write.

``FSMData`` / ``CallbackData`` fields are plain annotations; this module holds what can go next
to them:

- :func:`field` (and ``dataclasses.field``) for defaults and per-field options;
- ``Annotated`` markers: :class:`Key` (stored key, keys read on load), :class:`Discriminator`
  (tagged unions), a converter (per-field format);
- ready-made converters that select a native format (no Python call per value):
  :class:`IsoDatetime`, :class:`EpochDatetime`, :class:`DecimalAsNumber`, :class:`EnumByName`,
  :class:`UuidHex`;
- :class:`Converter`, the base of user converters (Python callbacks);
- :class:`ConversionError`, raised for data that does not convert.

The module needs only the standard library; the conversion itself runs in ``aiogram._core``
(F-08, PD-36).
"""

from __future__ import annotations

import dataclasses
import reprlib
from collections.abc import Callable, Sequence
from typing import Any, Literal, NamedTuple, TypeVar, overload

__all__ = [
    "MISSING",
    "ConversionError",
    "Converter",
    "DecimalAsNumber",
    "Discriminator",
    "EnumByName",
    "EpochDatetime",
    "ErrorDetail",
    "IsoDatetime",
    "Key",
    "UuidHex",
    "field",
]

_T = TypeVar("_T")

MISSING: Any = dataclasses.MISSING
"""The "no value" sentinel (``ErrorDetail.value`` of a missing field, unset defaults)."""

_repr = reprlib.Repr()  # keyword arguments only from 3.12
_repr.maxstring = _repr.maxother = 80
_repr.maxlist = _repr.maxdict = 10


class ErrorDetail(NamedTuple):
    """One conversion error: where (``loc``: stored keys and list indexes), what, and the value."""

    loc: tuple[str | int, ...]
    message: str
    value: Any = MISSING


def render_loc(loc: Sequence[str | int]) -> str:
    """``('address', 'zip')`` -> ``address.zip``; ``('tags', 2)`` -> ``tags[2]``."""
    text = ""
    for segment in loc:
        if isinstance(segment, int):
            text += f"[{segment}]"
        else:
            text += f".{segment}" if text else segment
    return text


class ConversionError(ValueError):
    """Data that does not convert, with every error found (:attr:`errors`).

    The JSON codec collects all errors (up to 100); unions and the flat codec report the first.
    """

    def __init__(self, title: str, errors: Sequence[ErrorDetail]) -> None:
        self.title = title
        """What failed: ``loading Form``, ``dumping Form``, ``constructing Form``."""
        self.errors = list(errors)
        super().__init__(title, self.errors)

    def __str__(self) -> str:
        count = len(self.errors)
        lines = [f"{count} error{'' if count == 1 else 's'} {self.title}"]
        for error in self.errors:
            path = render_loc(error.loc)
            text = f"{path}: {error.message}" if path else error.message
            if error.value is not MISSING:
                text += f", got {_repr.repr(error.value)}"
            lines.append(f"  {text}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.title!r}, errors={self.errors!r})"


class Converter:
    """A user converter: the converter core calls these methods for every value.

    ``to_json`` returns a JSON-shaped value (``str``, ``int``, ``float``, ``bool``, ``None``,
    ``list``, ``dict`` with ``str`` keys); ``from_json`` gets one and returns the Python value.
    A converter that also overrides ``to_str`` / ``from_str`` has a flat-string form (callback
    data). A ``ValueError`` raised here becomes a :class:`ConversionError` at the field's path.

    Use it as ``Annotated[T, MyConverter()]``, ``field(converter=MyConverter())``, in a class's
    ``converters={T: MyConverter()}``, or return it from a type's ``__aiogram_converter__``.
    """

    def to_json(self, value: Any) -> Any:
        raise NotImplementedError

    def from_json(self, value: Any) -> Any:
        raise NotImplementedError

    def to_str(self, value: Any) -> str:
        msg = f"{self!r} has no flat-string form"
        raise TypeError(msg)

    def from_str(self, value: str) -> Any:
        msg = f"{self!r} has no flat-string form"
        raise TypeError(msg)

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class _Native(Converter):
    """A ready-made converter: it selects a native format and is not called per value."""

    def _unused(self) -> Any:
        msg = f"{self!r} converts only through a schema"
        raise TypeError(msg)

    def to_json(self, value: Any) -> Any:
        return self._unused()

    def from_json(self, value: Any) -> Any:
        return self._unused()


_Timespec = Literal["auto", "hours", "minutes", "seconds", "milliseconds", "microseconds"]


@dataclasses.dataclass(frozen=True)
class IsoDatetime(_Native):
    """``datetime`` as ISO 8601 text, ``isoformat(sep, timespec)``; any ISO text loads."""

    timespec: _Timespec = "auto"
    sep: str = "T"


@dataclasses.dataclass(frozen=True)
class EpochDatetime(_Native):
    """``datetime`` as a Unix timestamp (seconds or milliseconds); loads as an aware UTC
    ``datetime``. A naive ``datetime`` is local time, as ``datetime.timestamp()`` reads it."""

    unit: Literal["s", "ms"] = "s"


@dataclasses.dataclass(frozen=True)
class DecimalAsNumber(_Native):
    """``Decimal`` as a JSON number. Exact on the JSON-bytes paths (``load_json`` /
    ``dump_json``); a dumped dict holds a ``float``, which is lossy (Memory and Mongo storages)."""


@dataclasses.dataclass(frozen=True)
class EnumByName(_Native):
    """An ``Enum`` stored by member name instead of value."""


@dataclasses.dataclass(frozen=True)
class UuidHex(_Native):
    """``UUID`` as 32 hex digits in JSON (the flat form always is)."""


@dataclasses.dataclass(frozen=True)
class Key:
    """``Annotated[T, Key("x", load=("old_name",))]``: store the field under ``"x"``; when it is
    missing, read the ``load`` keys in order (data written by an older deploy)."""

    name: str
    load: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.load, str):
            msg = "Key(load=...) takes a sequence of keys, not a str"
            raise TypeError(msg)
        object.__setattr__(self, "load", tuple(self.load))


@dataclasses.dataclass(frozen=True)
class Discriminator:
    """``Annotated[A | B, Discriminator("kind")]``: pick the union member by its ``Literal`` tag.

    Every member must be a model, dataclass, NamedTuple or TypedDict whose ``kind`` field is a
    ``Literal``; the tag in the input selects the member, so loading never guesses.
    """

    field: str


@dataclasses.dataclass(frozen=True, slots=True)
class _FieldInfo:
    """What :func:`field` returns; the resolver reads it from the class body."""

    default: Any = MISSING
    default_factory: Any = MISSING
    init: bool = True
    kw_only: bool | None = None
    repr: bool = True
    compare: bool = True
    key: str | None = None
    load: tuple[str, ...] = ()
    converter: Converter | None = None


@overload
def field(
    *,
    default: _T,
    init: bool = ...,
    kw_only: bool = ...,
    repr: bool = ...,
    compare: bool = ...,
    key: str | None = ...,
    load: Sequence[str] = ...,
    converter: Converter | None = ...,
) -> _T: ...
@overload
def field(
    *,
    default_factory: Callable[[], _T],
    init: bool = ...,
    kw_only: bool = ...,
    repr: bool = ...,
    compare: bool = ...,
    key: str | None = ...,
    load: Sequence[str] = ...,
    converter: Converter | None = ...,
) -> _T: ...
@overload
def field(
    *,
    init: bool = ...,
    kw_only: bool = ...,
    repr: bool = ...,
    compare: bool = ...,
    key: str | None = ...,
    load: Sequence[str] = ...,
    converter: Converter | None = ...,
) -> Any: ...
def field(  # noqa: PLR0913
    *,
    default: Any = MISSING,
    default_factory: Any = MISSING,
    init: bool = True,
    kw_only: bool | None = None,
    repr: bool = True,  # noqa: A002
    compare: bool = True,
    key: str | None = None,
    load: Sequence[str] = (),
    converter: Converter | None = None,
) -> Any:
    """A field with options, as ``dataclasses.field``.

    ``key`` / ``load`` / ``converter`` are short for ``Annotated[T, Key(key, load=load)]`` and
    ``Annotated[T, converter]`` on this field (``Annotated`` also works inside containers);
    giving one both ways is a ``TypeError``. ``repr`` / ``compare`` drop the field from
    ``repr()`` / ``==`` and ``hash()``.
    """
    if default is not MISSING and default_factory is not MISSING:
        msg = "cannot specify both default and default_factory"
        raise ValueError(msg)
    if isinstance(load, str):
        msg = "field(load=...) takes a sequence of keys, not a str"
        raise TypeError(msg)
    return _FieldInfo(
        default=default,
        default_factory=default_factory,
        init=init,
        kw_only=kw_only,
        repr=repr,
        compare=compare,
        key=key,
        load=tuple(load),
        converter=converter,
    )
