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

The module imports only the standard library. On CPython, :class:`ModelConverter`
switches to the Rust backend in ``aiogram._core`` (imported lazily, on first compile)
when it is available; the Python code here is the reference and the PyPy backend.
"""

from __future__ import annotations

import contextlib
import dataclasses
import importlib
import json
import sys
import types
import typing
from collections.abc import Callable, Iterable, Mapping, Sequence
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from functools import partial
from typing import (
    Annotated,
    Any,
    ClassVar,
    ForwardRef,
    Literal,
    NotRequired,
    Required,
    get_args,
    get_origin,
    is_typeddict,
)
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


class _NotReady(NameError):
    """A class's fields were needed while they were being compiled (a recursive reference)."""


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
    kind: ClassVar[str] = "python"
    """Tag the Rust backend dispatches on; ``"python"`` means "call this converter"."""

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
    kind = "str"

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
    kind = "int"

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
    kind = "float"

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
    kind = "bool"

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
    kind = "enum"

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
    kind = "literal"

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
    kind = "optional"

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
    """``list[T]``, ``tuple[T, ...]``, ``set[T]``, ``frozenset[T]``; the JSON form is a list."""

    kind = "sequence"

    def __init__(self, item: Converter, tp: type) -> None:
        self.item = item
        self.tp: Any = tp

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
        return result if self.tp is list else self.tp(result)


class _Dict(Converter):
    """``dict[str, T]``."""

    kind = "dict"

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


class _TypedDict(Converter):
    """A ``TypedDict``: a plain ``dict`` of the declared keys present in the input.

    ``Required`` keys must be there; ``NotRequired`` keys that are missing stay missing (the
    dict is its own "set fields" record). Unknown keys are dropped, as for models.
    """

    def __init__(self, tp: type) -> None:
        self.tp = tp
        self._fields: tuple[tuple[str, Converter, bool], ...] | None = None
        self._compiling = False

    @property
    def fields(self) -> tuple[tuple[str, Converter, bool], ...]:
        if self._fields is None and self._compiling:
            raise _NotReady(self.tp)
        if self._fields is None:  # lazy: a TypedDict may refer to itself
            self._compiling = True
            try:
                self._fields = self._compile()
            finally:
                self._compiling = False
        return self._fields

    def _compile(self) -> tuple[tuple[str, Converter, bool], ...]:
        hints = typing.get_type_hints(
            self.tp, localns={self.tp.__name__: self.tp}, include_extras=True, **_HINTS_OPTIONS
        )
        required_keys = self.tp.__required_keys__  # type: ignore[attr-defined]
        fields = []
        for name, hint in hints.items():
            # The wrapper wins: under string annotations __required_keys__ can miss it.
            inner = hint
            while get_origin(inner) is Annotated:
                inner = get_args(inner)[0]
            wrapper = get_origin(inner)
            required = wrapper is Required or (
                wrapper is not NotRequired and name in required_keys
            )
            try:
                fields.append((name, converter_for(hint), required))
            except TypeError as e:
                msg = f"{self.tp.__qualname__}.{name}: {e}"
                raise TypeError(msg) from None
        return tuple(fields)

    def _convert(self, value: Any, method: str) -> dict[str, Any]:
        if not isinstance(value, Mapping):
            raise _expected("an object", value)
        result = {}
        for name, converter, required in self.fields:
            raw = value.get(name, MISSING)
            if raw is MISSING:
                if required:
                    raise ConversionError("field required")._at("." + name)
                continue
            try:
                result[name] = getattr(converter, method)(raw)
            except ConversionError as e:
                raise e._at("." + name) from None
        return result

    def to_json(self, value: Any) -> Any:
        return self._convert(value, "to_json")

    def from_json(self, value: Any) -> Any:
        return self._convert(value, "from_json")


@dataclasses.dataclass(frozen=True, slots=True)
class Discriminator:
    """``Annotated[A | B, Discriminator("kind")]``: pick the union member by its ``Literal`` tag.

    Every member must be a model, dataclass, NamedTuple or TypedDict whose ``kind`` field is a
    ``Literal``; the tag of the input selects the member, so loading never guesses.
    """

    field: str


_SCALAR_TYPES: dict[str, type] = {"str": str, "int": int, "float": float, "bool": bool}


def _types(converter: Converter, *, json_form: bool) -> frozenset[type]:
    """The value types ``converter`` takes without coercion (JSON or Python form); for Union."""
    if isinstance(converter, (_Str, _Int, _Float, _Bool)):
        return frozenset({_SCALAR_TYPES[converter.kind]})
    if isinstance(converter, _Text):
        return frozenset({str if json_form else converter.tp})
    if isinstance(converter, _Enum):
        return (
            frozenset({type(m.value) for m in converter.tp})
            if json_form
            else frozenset({converter.tp})
        )
    if isinstance(converter, _Literal):
        return frozenset(type(value) for value in converter.values)
    if isinstance(converter, _Sequence):
        return frozenset({list} if json_form else {converter.tp})
    if isinstance(converter, (_Dict, _TypedDict)):
        return frozenset({dict})
    if isinstance(converter, ModelConverter):
        return frozenset({dict if json_form else converter.tp})
    return frozenset()  # a user converter: tried in order, after the exact matches


class _Union(Converter):
    """``A | B | ...`` (with or without ``None``), smart mode (PD-35).

    A member whose type matches the value exactly is tried first (``int | str`` keeps ``1`` and
    ``"1"`` apart, ``float | int`` keeps ``1`` an int), then every member left to right; the
    first that accepts wins. With a :class:`Discriminator`, the tag field picks the member.
    """

    def __init__(
        self,
        members: list[Converter],
        *,
        nullable: bool,
        label: str,
        discriminator: str | None = None,
    ) -> None:
        self.members = members
        self.nullable = nullable
        self.label = label
        self.discriminator = discriminator
        self._json = [(member, _types(member, json_form=True)) for member in members]
        self._python = [(member, _types(member, json_form=False)) for member in members]
        self._tags: dict[tuple[type, Any], Converter] | None = None
        if discriminator is not None:
            with contextlib.suppress(NameError):  # a member defined later: built on first use
                self._tag_table()

    def _tag_table(self) -> dict[tuple[type, Any], Converter]:
        if self._tags is None:
            tags: dict[tuple[type, Any], Converter] = {}
            for member in self.members:
                fields: dict[str, Converter] = {}
                if isinstance(member, ModelConverter):
                    fields = {field.name: field.converter for field in member.fields}
                elif isinstance(member, _TypedDict):
                    fields = {name: converter for name, converter, _ in member.fields}
                tag = fields.get(self.discriminator)  # type: ignore[arg-type]
                if not isinstance(tag, _Literal):
                    msg = (
                        f"{self.label}: every member needs a Literal {self.discriminator!r} field"
                    )
                    raise TypeError(msg)
                for value in tag.values:
                    if tags.setdefault((type(value), value), member) is not member:
                        msg = f"{self.label}: tag {value!r} is used by more than one member"
                        raise TypeError(msg)
            self._tags = tags
        return self._tags

    @staticmethod
    def _order(table: list[tuple[Converter, frozenset[type]]], tp: type) -> list[Converter]:
        exact = [member for member, types_ in table if tp in types_]
        return exact + [member for member, _ in table if member not in exact]

    def _first(self, members: list[Converter], method: str, value: Any) -> Any:
        for member in members:
            try:
                return getattr(member, method)(value)
            except ConversionError:
                continue
        raise _expected(self.label, value)

    def from_json(self, value: Any) -> Any:
        if value is None and self.nullable:
            return None
        if self.discriminator is None:
            return self._first(self._order(self._json, type(value)), "from_json", value)
        if not isinstance(value, Mapping):
            raise _expected("an object", value)
        tag = value.get(self.discriminator, MISSING)
        if tag is MISSING:
            raise ConversionError("field required")._at("." + self.discriminator)
        try:
            member = self._tag_table()[type(tag), tag]
        except (KeyError, TypeError):
            expected = [value for _, value in self._tag_table()]
            raise _expected(f"one of {expected}", tag)._at("." + self.discriminator) from None
        return member.from_json(value)

    def to_json(self, value: Any) -> Any:
        if value is None and self.nullable:
            return None
        return self._first(self._order(self._python, type(value)), "to_json", value)


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

    On the Rust backend, :meth:`from_json`, :meth:`load_json`, :meth:`from_flat` and
    :meth:`to_flat` are replaced per instance by the compiled schema. It handles the common
    shapes and hands anything else (bad input included) back to the ``_py_*`` methods, so
    results and errors are the Python ones.
    """

    kind = "model"

    def __init__(self, tp: type, *, is_model: bool) -> None:
        self.tp = tp
        self.is_model = is_model
        self._fields: tuple[FieldSpec, ...] | None = None
        self._compiling = False

    @property
    def fields(self) -> tuple[FieldSpec, ...]:
        # Lazy: a class may refer to itself (or to a class defined later) through its fields.
        if self._fields is None:
            if self._compiling:
                raise _NotReady(self.tp)
            self._compiling = True
            try:
                self._fields = _compile(self.tp)
            finally:
                self._compiling = False
            self._accelerate()
        return self._fields

    def _accelerate(self) -> None:
        core = _backend()
        if core is None:
            return
        schema = core.ModelSchema(self)
        # Instance attributes shadow the Python methods; the Rust backend calls the _py_* ones.
        vars(self).update(
            _schema=schema,
            from_json=schema.load_dict,
            load_json=schema.load_json,
            from_flat=schema.from_flat,
            to_flat=schema.to_flat,
        )

    def _rust_schema(self) -> Any:
        """The compiled Rust schema (compiling the fields first); used for nested models."""
        self.fields  # noqa: B018
        return vars(self)["_schema"]

    def _build(self, values: dict[str, Any], fields_set: Iterable[str], source: Any) -> Any:
        if not self.is_model:
            try:
                return self.tp(**values)
            except ValueError as e:
                raise ConversionError(str(e), source) from e
        instance: Any = object.__new__(self.tp)
        instance.__dict__.update(values)
        instance.__dict__[FIELDS_SET] = frozenset(fields_set)
        return instance

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
        # Keys present in the input count as set, so a round trip keeps exclude_unset.
        return self._build(values, (name for name in values if name in value), value)

    def load_json(self, data: bytes | str) -> Any:
        """JSON text (``bytes`` or ``str``) -> instance; one pass on the Rust backend."""
        return self._py_from_json(json.loads(data))

    def from_flat(self, parts: Sequence[str]) -> Any:
        """Callback-data parts (one string per field, in field order) -> instance."""
        fields = self._fields or self.fields
        if len(parts) != len(fields):
            raise ConversionError(f"expected {len(fields)} parts", list(parts))
        values = {}
        for field, part in zip(fields, parts, strict=True):
            try:
                values[field.name] = field.converter.from_str(part)
            except ConversionError as e:
                raise e._at("." + field.name) from None
        return self._build(values, values, parts)

    def to_flat(self, value: Any) -> list[str]:
        """Instance -> callback-data parts, one string per field in field order."""
        if not isinstance(value, self.tp):
            raise _expected(f"a {self.tp.__qualname__} instance", value)
        result = []
        for field in self._fields or self.fields:
            try:
                result.append(field.converter.to_str(getattr(value, field.name)))
            except ConversionError as e:
                raise e._at("." + field.name) from None
        return result

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

    # The Python implementations, kept reachable for the Rust backend's fallback.
    _py_from_json = from_json
    _py_load_json = load_json
    _py_from_flat = from_flat
    _py_to_flat = to_flat


# ponytail: plain dicts keep compiled classes alive; classes are module-level and immortal anyway.
_models: dict[type, ModelConverter] = {}
_extra: dict[Any, Converter] = {}
_typeddicts: dict[type, _TypedDict] = {}

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


_RUST: Any = MISSING  # aiogram._core once resolved, None for the Python backend


def _backend() -> Any:
    global _RUST  # noqa: PLW0603
    if _RUST is MISSING:
        _RUST = None
        # ponytail: PyPy keeps the Python backend: through cpyext Rust is 3-9x slower (PD-35).
        if sys.implementation.name == "cpython":  # pragma: no branch
            with contextlib.suppress(ImportError):
                _RUST = importlib.import_module("aiogram._core")
    return _RUST


def _use_backend(*, rust: bool) -> None:
    """Switch every compiled model to the Rust (if available) or the Python backend (tests)."""
    global _RUST  # noqa: PLW0603
    _RUST = MISSING if rust else None
    for converter in _models.values():
        for name in ("_schema", "from_json", "load_json", "from_flat", "to_flat"):
            vars(converter).pop(name, None)
        if converter._fields is not None:
            converter._accelerate()


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
        base, *metadata = get_args(tp)
        for marker in metadata:
            if isinstance(marker, Converter):  # a per-field converter (PD-35)
                return marker
        for marker in metadata:
            if isinstance(marker, Discriminator):
                return _union(base, marker.field)
        return converter_for(base)
    if origin in {Required, NotRequired}:  # TypedDict keys; required-ness comes from the class
        return converter_for(get_args(tp)[0])
    if (converter := _SCALARS.get(tp)) is not None:
        return converter
    args = get_args(tp)
    if origin in _UNION_TYPES:
        rest = [arg for arg in args if arg is not types.NoneType]
        if len(rest) == 1:
            return _Optional(converter_for(rest[0]))
        return _union(tp, None)
    if origin is Literal:
        return _Literal(args)
    if origin is list and len(args) == 1:
        return _Sequence(converter_for(args[0]), list)
    if origin is tuple and args[1:] == (Ellipsis,):
        return _Sequence(converter_for(args[0]), tuple)
    if origin is dict and args[:1] == (str,):
        return _Dict(converter_for(args[-1]))
    if origin in {set, frozenset} and len(args) == 1:
        item = converter_for(args[0])
        if isinstance(item, (_Dict, _TypedDict)) or (
            isinstance(item, _Sequence) and item.tp in {list, set}
        ):
            msg = f"unhashable set item {args[0]!r}"
            raise TypeError(msg)
        return _Sequence(item, origin)
    if is_typeddict(tp):
        if (cached := _typeddicts.get(tp)) is not None:
            return cached
        converter = _typeddicts[tp] = _TypedDict(tp)
        try:
            converter.fields  # noqa: B018  # eager, so a bad key fails at class creation
        except TypeError:
            del _typeddicts[tp]
            raise
        return converter
    if isinstance(tp, type):
        if issubclass(tp, Enum):
            return _Enum(tp)
        if tp in _models:
            return _models[tp]
        if dataclasses.is_dataclass(tp) or _is_namedtuple(tp):
            model = _models[tp] = ModelConverter(tp, is_model=False)
            try:
                model.fields  # noqa: B018  # eager, so a bad nested field fails at class creation
            except TypeError:
                del _models[tp]
                raise
            return model
    msg = f"unsupported annotation {tp!r}"
    raise TypeError(msg)


def _union(tp: Any, discriminator: str | None) -> _Union:
    args = get_args(tp)
    if get_origin(tp) not in _UNION_TYPES or len(args) < 2:  # noqa: PLR2004
        msg = f"Discriminator needs a union of models, got {tp!r}"
        raise TypeError(msg)
    members = [converter_for(arg) for arg in args if arg is not types.NoneType]
    return _Union(
        members,
        nullable=types.NoneType in args,
        label=repr(tp).removeprefix("typing."),
        discriminator=discriminator,
    )


def _is_namedtuple(tp: type) -> bool:
    return issubclass(tp, tuple) and hasattr(tp, "_fields")


def _compile(cls: type) -> tuple[FieldSpec, ...]:
    hints = typing.get_type_hints(
        cls, localns={cls.__name__: cls}, include_extras=True, **_HINTS_OPTIONS
    )
    items: list[tuple[str, Any, Any]]
    if _is_namedtuple(cls):  # like a dataclass: a JSON object, built with cls(**values)
        defaults = cls._field_defaults  # type: ignore[attr-defined]
        items = [(name, defaults.get(name, MISSING), MISSING) for name in cls._fields]  # type: ignore[attr-defined]
    elif dataclasses.is_dataclass(cls):
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
            converter = converter_for(hints.get(name, Any))  # an untyped namedtuple field
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
