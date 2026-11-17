"""
Shared converter core for ``FSMData`` and ``CallbackData`` (private).

One converter table serves both (D14, D30): every converter has a JSON codec
(``to_json`` / ``from_json``, JSON-shaped values for FSM storages) and, for the
flat subset (scalars, enums, ``Literal``, ``X | None``), a string codec
(``to_str`` / ``from_str``, callback data parts).

Field specs are compiled once per class (:func:`register_model` from
``__init_subclass__``), so loading does no per-call reflection. An unsupported
annotation raises :class:`TypeError` at class creation; bad input raises
:class:`ConversionError` carrying the field path (``address.zip``, ``tags[2]``).

The module imports only the standard library.
"""

from __future__ import annotations

import dataclasses
import sys
import types
import typing
from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from functools import partial
from typing import Annotated, Any, ClassVar, ForwardRef, Literal, get_args, get_origin
from uuid import UUID

MISSING: Any = dataclasses.MISSING
FIELDS_SET = "__fields_set__"
"""Instance attribute holding the frozenset of explicitly set field names (``exclude_unset``)."""

if sys.version_info >= (3, 14):
    import annotationlib

    # Under deferred annotations a name that is not bound yet (the class itself while
    # ``__init_subclass__`` runs) raises NameError in the default format even with localns.
    _HINTS_OPTIONS: dict[str, Any] = {"format": annotationlib.Format.FORWARDREF}
else:  # pragma: no cover
    _HINTS_OPTIONS: dict[str, Any] = {}


class ConversionError(ValueError):
    """A value could not be converted; :attr:`path` points at the offending field."""

    def __init__(self, reason: str, value: Any = MISSING) -> None:
        super().__init__(reason)
        self.reason = reason
        self.value = value
        self._segments: list[str] = []

    def _at(self, segment: str) -> ConversionError:
        self._segments.append(segment)
        return self

    @property
    def path(self) -> str:
        return "".join(reversed(self._segments)).removeprefix(".")

    def __str__(self) -> str:
        text = f"{self.path}: {self.reason}" if self._segments else self.reason
        if self.value is not MISSING:
            text += f" (got {self.value!r})"
        return text


def _expected(what: str, value: Any) -> ConversionError:
    return ConversionError(f"expected {what}", value)


class Converter:
    """Base converter. ``flat`` converters also implement the string codec."""

    flat: bool = False

    def to_json(self, value: Any) -> Any:  # pragma: no cover
        raise NotImplementedError

    def from_json(self, value: Any) -> Any:  # pragma: no cover
        raise NotImplementedError

    def to_str(self, value: Any) -> str:
        msg = f"{self!r} has no flat-string form"
        raise TypeError(msg)

    def from_str(self, value: str) -> Any:
        msg = f"{self!r} has no flat-string form"
        raise TypeError(msg)

    def __repr__(self) -> str:
        return f"<{type(self).__name__}>"


class _Str(Converter):
    flat = True

    def to_json(self, value: Any) -> Any:
        if isinstance(value, str):
            return value
        raise _expected("a string", value)

    from_json = to_json
    to_str = to_json

    def from_str(self, value: str) -> Any:
        return value


class _Int(Converter):
    flat = True

    def to_json(self, value: Any) -> Any:
        if type(value) is int:
            return value
        if isinstance(value, int) and not isinstance(value, bool):
            return int(value)
        raise _expected("an integer", value)

    from_json = to_json

    def to_str(self, value: Any) -> str:
        return str(self.to_json(value))

    def from_str(self, value: str) -> Any:
        try:
            return int(value)
        except ValueError:
            raise _expected("an integer", value) from None


class _Float(Converter):
    flat = True

    def to_json(self, value: Any) -> Any:
        if type(value) is float:
            return value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        raise _expected("a number", value)

    from_json = to_json

    def to_str(self, value: Any) -> str:
        return str(self.to_json(value))

    def from_str(self, value: str) -> Any:
        try:
            return float(value)
        except ValueError:
            raise _expected("a number", value) from None


_BOOL_TEXT = {
    "1": True,
    "0": False,
    "true": True,
    "false": False,
    "t": True,
    "f": False,
    "yes": True,
    "no": False,
    "y": True,
    "n": False,
    "on": True,
    "off": False,
}


class _Bool(Converter):
    flat = True

    def to_json(self, value: Any) -> Any:
        if isinstance(value, bool):
            return value
        raise _expected("a boolean", value)

    from_json = to_json

    def to_str(self, value: Any) -> str:
        return "1" if self.to_json(value) else "0"

    def from_str(self, value: str) -> Any:
        # 3.x packs "1"/"0"; the rest is pydantic's lax set, kept for hand-built data.
        try:
            return _BOOL_TEXT[value.lower()]
        except KeyError:
            raise _expected("a boolean", value) from None


class _Text(Converter):
    """A value stored as text in both codecs (``Decimal``, ``UUID``, ``datetime``...)."""

    def __init__(
        self,
        tp: type,
        parse: Callable[[str], Any],
        *,
        flat: bool = True,
        to_text: Callable[[Any], str] = str,
        to_flat: Callable[[Any], str] | None = None,
        reject: type | None = None,
    ) -> None:
        self.tp = tp
        self.parse = parse
        self.flat = flat
        self.to_text = to_text
        self.to_flat = to_flat or to_text
        self.reject = reject

    def _check(self, value: Any) -> Any:
        if isinstance(value, self.tp) and not (self.reject and isinstance(value, self.reject)):
            return value
        raise _expected(f"a {self.tp.__name__}", value)

    def to_json(self, value: Any) -> Any:
        return self.to_text(self._check(value))

    def from_json(self, value: Any) -> Any:
        if not isinstance(value, str):
            raise _expected(f"a {self.tp.__name__} string", value)
        return self._parse(value)

    def to_str(self, value: Any) -> str:
        if not self.flat:
            return super().to_str(value)
        return self.to_flat(self._check(value))

    def from_str(self, value: str) -> Any:
        if not self.flat:
            return super().from_str(value)
        return self._parse(value)

    def _parse(self, value: str) -> Any:
        try:
            return self.parse(value)
        except (ValueError, ArithmeticError):  # InvalidOperation, ZeroDivisionError
            raise _expected(f"a {self.tp.__name__} string", value) from None


class _Enum(Converter):
    flat = True

    def __init__(self, tp: type[Enum]) -> None:
        for member in tp:
            if type(member.value) not in _JSON_SCALARS:
                msg = f"{tp.__name__}.{member.name} value {member.value!r} is not a JSON scalar"
                raise TypeError(msg)
        self.tp = tp
        self._by_text = {str(member.value): member for member in tp}
        # Values with the same text (1 and "1") cannot round-trip through a flat string.
        self.flat = len(self._by_text) == len(tp)

    def _check(self, value: Any) -> Enum:
        if isinstance(value, self.tp):
            return value
        raise _expected(f"a {self.tp.__name__} member", value)

    def to_json(self, value: Any) -> Any:
        return self._check(value).value

    def from_json(self, value: Any) -> Any:
        try:
            return self.tp(value)
        except ValueError:
            raise _expected(f"a {self.tp.__name__} value", value) from None

    def to_str(self, value: Any) -> str:
        if not self.flat:
            return super().to_str(value)
        return str(self._check(value).value)

    def from_str(self, value: str) -> Any:
        if not self.flat:
            return super().from_str(value)
        try:
            return self._by_text[value]
        except KeyError:
            raise _expected(f"a {self.tp.__name__} value", value) from None


_JSON_SCALARS = {str, int, float, bool, types.NoneType}


def _literal_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


class _Literal(Converter):
    flat = True

    def __init__(self, values: tuple[Any, ...]) -> None:
        for value in values:
            if value is not None and type(value) not in {str, int, bool}:
                msg = f"unsupported Literal value {value!r}; use str, int, bool or None"
                raise TypeError(msg)
        self.values = values
        # Keyed by type too, so True does not match Literal[1].
        self._json = {(type(value), value) for value in values}
        self._text = {_literal_text(value): value for value in values}
        self.flat = len(self._text) == len(values)  # Literal[1, "1"]: same text

    def to_json(self, value: Any) -> Any:
        try:
            if (type(value), value) in self._json:
                return value
        except TypeError:  # unhashable
            pass
        raise _expected(f"one of {list(self.values)}", value)

    from_json = to_json

    def to_str(self, value: Any) -> str:
        if not self.flat:
            return super().to_str(value)
        return _literal_text(self.to_json(value))

    def from_str(self, value: str) -> Any:
        if not self.flat:
            return super().from_str(value)
        try:
            return self._text[value]
        except KeyError:
            raise _expected(f"one of {list(self.values)}", value) from None


class _Optional(Converter):
    def __init__(self, inner: Converter) -> None:
        self.inner = inner
        self.flat = inner.flat

    def to_json(self, value: Any) -> Any:
        return None if value is None else self.inner.to_json(value)

    def from_json(self, value: Any) -> Any:
        return None if value is None else self.inner.from_json(value)

    def to_str(self, value: Any) -> str:
        # An empty part means None (3.x pack writes None as "").
        if not self.flat:
            return super().to_str(value)
        return "" if value is None else self.inner.to_str(value)

    def from_str(self, value: str) -> Any:
        if not self.flat:
            return super().from_str(value)
        return None if value == "" else self.inner.from_str(value)


class _Sequence(Converter):
    """``list[T]`` and ``tuple[T, ...]``; JSON form is a list either way."""

    def __init__(self, item: Converter, tp: type[list[Any]] | type[tuple[Any, ...]]) -> None:
        self.item = item
        self.tp = tp

    def _convert(self, values: Iterable[Any], convert: Callable[[Any], Any]) -> list[Any]:
        result = []
        for index, value in enumerate(values):
            try:
                result.append(convert(value))
            except ConversionError as e:
                raise e._at(f"[{index}]") from None
        return result

    def to_json(self, value: Any) -> Any:
        if not isinstance(value, self.tp):
            raise _expected(f"a {self.tp.__name__}", value)
        return self._convert(value, self.item.to_json)

    def from_json(self, value: Any) -> Any:
        if not isinstance(value, (list, tuple)):
            raise _expected("an array", value)
        result = self._convert(value, self.item.from_json)
        return result if self.tp is list else tuple(result)


class _Dict(Converter):
    """``dict[str, T]``."""

    def __init__(self, item: Converter) -> None:
        self.item = item

    def _convert(self, value: Any, convert: Callable[[Any], Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise _expected("an object", value)
        result = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise _expected("a string key", key)
            try:
                result[key] = convert(item)
            except ConversionError as e:
                raise e._at(f"[{key!r}]") from None
        return result

    def to_json(self, value: Any) -> Any:
        return self._convert(value, self.item.to_json)

    def from_json(self, value: Any) -> Any:
        return self._convert(value, self.item.from_json)


@dataclasses.dataclass(frozen=True, slots=True)
class FieldSpec:
    name: str
    converter: Converter
    default: Any = MISSING
    default_factory: Callable[[], Any] | None = None


class ModelConverter(Converter):
    """Converter for a registered model class or a stdlib dataclass.

    Registered models are built without calling ``__init__`` and must have an
    instance ``__dict__``; dataclasses are built with ``tp(**values)`` so
    ``__post_init__`` runs (a ``ValueError`` there becomes a :class:`ConversionError`).
    """

    def __init__(self, tp: type, *, is_model: bool) -> None:
        self.tp = tp
        self.is_model = is_model
        self._fields: tuple[FieldSpec, ...] | None = None

    @property
    def fields(self) -> tuple[FieldSpec, ...]:
        # Lazy: a class may refer to itself (or to a class defined later) through its fields.
        if self._fields is None:
            self._fields = _compile(self.tp)
        return self._fields

    def from_json(self, value: Any) -> Any:
        if not isinstance(value, Mapping):
            raise _expected("an object", value)
        values: dict[str, Any] = {}
        get = value.get
        for field in self._fields or self.fields:
            raw = get(field.name, MISSING)
            if raw is not MISSING:
                try:
                    values[field.name] = field.converter.from_json(raw)
                except ConversionError as e:
                    raise e._at("." + field.name) from None
            elif field.default is not MISSING:
                values[field.name] = field.default
            elif field.default_factory is not None:
                values[field.name] = field.default_factory()
            else:
                raise ConversionError("field required")._at("." + field.name)
        if not self.is_model:
            try:
                return self.tp(**values)
            except ValueError as e:
                raise ConversionError(str(e), value) from e
        # Keys present in the input count as set, so a round trip keeps exclude_unset.
        fields_set = frozenset(name for name in values if name in value)
        instance: Any = object.__new__(self.tp)
        instance.__dict__.update(values)
        instance.__dict__[FIELDS_SET] = fields_set
        return instance

    def to_json(self, value: Any) -> Any:
        if not isinstance(value, self.tp):
            raise _expected(f"a {self.tp.__qualname__} instance", value)
        return self.dump(value)

    def dump(self, value: Any, *, exclude_unset: bool = False) -> dict[str, Any]:
        fields_set = getattr(value, FIELDS_SET, None) if exclude_unset else None
        result = {}
        for field in self._fields or self.fields:
            if fields_set is not None and field.name not in fields_set:
                continue
            try:
                result[field.name] = field.converter.to_json(getattr(value, field.name))
            except ConversionError as e:
                raise e._at("." + field.name) from None
        return result

    def init(self, instance: Any, kwargs: Mapping[str, Any]) -> None:
        """``__init__`` body for a registered model: store kwargs, fill defaults, record set
        fields.

        Values are not converted; :meth:`dump` validates them.
        """
        values = {}
        for field in self.fields:
            if field.name in kwargs:
                values[field.name] = kwargs[field.name]
            elif field.default is not MISSING:
                values[field.name] = field.default
            elif field.default_factory is not None:
                values[field.name] = field.default_factory()
            else:
                msg = f"{self.tp.__qualname__}() missing required argument {field.name!r}"
                raise TypeError(msg)
        if unknown := kwargs.keys() - values.keys():
            msg = f"{self.tp.__qualname__}() got unexpected arguments {sorted(unknown)}"
            raise TypeError(msg)
        instance.__dict__.update(values)
        instance.__dict__[FIELDS_SET] = frozenset(kwargs)


# ponytail: plain dicts keep compiled classes alive; classes are module-level and immortal anyway.
_models: dict[type, ModelConverter] = {}
_extra: dict[Any, Converter] = {}

_SCALARS: dict[Any, Converter] = {
    str: _Str(),
    int: _Int(),
    float: _Float(),
    bool: _Bool(),
    Decimal: _Text(Decimal, Decimal),
    Fraction: _Text(Fraction, Fraction),
    UUID: _Text(UUID, UUID, to_flat=lambda value: value.hex),  # hex: 3.x pack, shorter
    datetime: _Text(datetime, datetime.fromisoformat, flat=False, to_text=datetime.isoformat),
    date: _Text(date, date.fromisoformat, flat=False, to_text=date.isoformat, reject=datetime),
}
_UNION_TYPES = (typing.Union, types.UnionType)


def register_converter(tp: Any, converter: Converter) -> None:
    """Extension hook: use ``converter`` for annotation ``tp`` (exact match, before the built-ins).

    Affects only classes compiled after the call.
    """
    _extra[tp] = converter


def register_model(cls: type) -> ModelConverter:
    """Compile ``cls``; call from ``__init_subclass__``. :class:`TypeError` on a bad field."""
    converter = _models[cls] = ModelConverter(cls, is_model=True)
    try:
        converter.fields  # noqa: B018
    except NameError:
        pass  # a name defined later in the module; compiled on first use
    except TypeError:
        del _models[cls]
        raise
    return converter


def model_converter(tp: type) -> ModelConverter:
    """The converter for a registered model or a stdlib dataclass."""
    converter = converter_for(tp)
    if not isinstance(converter, ModelConverter):
        msg = f"{tp!r} is neither a registered model nor a dataclass"
        raise TypeError(msg)
    return converter


def converter_for(tp: Any) -> Converter:
    """Resolve an annotation to its converter; :class:`TypeError` if unsupported."""
    if isinstance(tp, (str, ForwardRef)):
        msg = f"unresolved forward reference {tp!r}"
        raise NameError(msg)
    origin = get_origin(tp)
    try:
        converter = _extra.get(tp)
    except TypeError:  # Annotated with unhashable metadata
        converter = None
    if converter is not None:
        return converter
    if origin is Annotated:
        return converter_for(get_args(tp)[0])
    if (converter := _SCALARS.get(tp)) is not None:
        return converter
    args = get_args(tp)
    if origin in _UNION_TYPES:
        rest = [arg for arg in args if arg is not types.NoneType]
        if len(rest) == 1 and types.NoneType in args:
            return _Optional(converter_for(rest[0]))
    elif origin is Literal:
        return _Literal(args)
    elif origin is list and len(args) == 1:
        return _Sequence(converter_for(args[0]), list)
    elif origin is tuple and args[1:] == (Ellipsis,):
        return _Sequence(converter_for(args[0]), tuple)
    elif origin is dict and args[:1] == (str,):
        return _Dict(converter_for(args[-1]))
    elif isinstance(tp, type):
        if issubclass(tp, Enum):
            return _Enum(tp)
        if tp in _models:
            return _models[tp]
        if dataclasses.is_dataclass(tp):
            model = _models[tp] = ModelConverter(tp, is_model=False)
            try:
                model.fields  # noqa: B018  # eager, so a bad nested field fails at class creation
            except TypeError:
                del _models[tp]
                raise
            return model
    msg = f"unsupported annotation {tp!r}"
    raise TypeError(msg)


def _compile(cls: type) -> tuple[FieldSpec, ...]:
    hints = typing.get_type_hints(
        cls, localns={cls.__name__: cls}, include_extras=True, **_HINTS_OPTIONS
    )
    items: list[tuple[str, Any, Any]]
    if dataclasses.is_dataclass(cls):
        for name, hint in hints.items():
            if isinstance(hint, dataclasses.InitVar) and getattr(cls, name, MISSING) is MISSING:
                # Loading cannot supply it: dataclasses.fields() leaves InitVars out.
                msg = f"{cls.__qualname__}.{name}: required InitVar is not supported"
                raise TypeError(msg)
        items = [
            (field.name, field.default, field.default_factory)
            for field in dataclasses.fields(cls)
            if field.init
        ]
    else:
        items = []
        for name, hint in hints.items():
            if name.startswith("_") or hint is ClassVar or get_origin(hint) is ClassVar:
                continue
            default = getattr(cls, name, MISSING)
            if isinstance(default, dataclasses.Field):
                items.append((name, default.default, default.default_factory))
            else:
                items.append((name, default, MISSING))
    specs = []
    for name, default, factory in items:
        try:
            converter = converter_for(hints[name])
        except TypeError as e:
            msg = f"{cls.__qualname__}.{name}: {e}"
            raise TypeError(msg) from None
        if default is not MISSING and not _is_hashable(default):
            # D115: a mutable default ([], {}, set()) is copied per instance.
            default, factory = MISSING, partial(deepcopy, default)
        specs.append(FieldSpec(name, converter, default, None if factory is MISSING else factory))
    return tuple(specs)


def _is_hashable(value: Any) -> bool:
    try:
        hash(value)
    except TypeError:
        return False
    return True
