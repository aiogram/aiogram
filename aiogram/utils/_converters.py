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

This module compiles annotations into converters; all per-value conversion runs in
Rust, in ``aiogram._core`` (PD-36: Rust-only, since PyPy is dropped from 4.x, PD-35). The
module imports only the standard library: ``aiogram._core`` is imported on first use.
"""

from __future__ import annotations

import contextlib
import dataclasses
import importlib
import sys
import threading
import types
import typing
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from enum import Enum, Flag
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


class Converter:
    """A converter: ``to_json`` / ``from_json``, and, when ``flat``, ``to_str`` / ``from_str``.

    Subclass it for :func:`register_converter` or a per-field ``Annotated[T, MyConverter()]``;
    the Rust core calls these methods. The built-in converters below carry only compile data
    (a ``kind`` tag, types, tables): their per-value work runs in Rust (PD-36).
    """

    flat: bool = False
    kind: ClassVar[str] = "python"
    """Tag the Rust core dispatches on; ``"python"`` means "call this converter's methods"."""

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


class _Native(Converter):
    """A built-in converter: its methods run on its compiled Rust core."""

    def _core(self) -> Any:
        core = self.__dict__.get("_core_")
        if core is None:
            core = self.__dict__["_core_"] = _rust().KindCore(self)
        return core

    def to_json(self, value: Any) -> Any:
        return self._core().to_json(value)

    def from_json(self, value: Any) -> Any:
        return self._core().from_json(value)

    def to_str(self, value: Any) -> str:
        return self._core().to_str(value)  # type: ignore[no-any-return]

    def from_str(self, value: str) -> Any:
        return self._core().from_str(value)


class _Str(_Native):
    flat = True
    kind = "str"


class _Int(_Native):
    flat = True
    kind = "int"


class _Float(_Native):
    flat = True
    kind = "float"


# The flat bool text: 3.x packs "1"/"0"; the rest is pydantic's lax set, kept for hand-built data.
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


class _Bool(_Native):
    flat = True
    kind = "bool"


class _Text(_Native):
    """A value stored as text in both codecs (``Decimal``, ``UUID``, ``datetime``...).

    ``parse`` reads the text (a ``ValueError`` / ``ArithmeticError`` is a conversion error),
    ``to_text`` / ``to_flat`` write it; an instance of ``reject`` (``datetime`` for ``date``)
    is refused.
    """

    kind = "text"

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


class _Enum(_Native):
    """An ``Enum``: its JSON form is the member value, matched by ``(type, value)`` so that
    ``true`` or ``1.0`` never load an ``IntEnum`` member."""

    flat = True
    kind = "enum"

    def __init__(self, tp: type[Enum]) -> None:
        if issubclass(tp, Flag):
            # composite and zero flags are not members: they could not round-trip
            msg = f"{tp.__name__} is a Flag enum, which is not supported"
            raise TypeError(msg)
        for member in tp:
            if type(member.value) not in _JSON_SCALARS:
                msg = f"{tp.__name__}.{member.name} value {member.value!r} is not a JSON scalar"
                raise TypeError(msg)
        self.tp = tp
        # an overridden _missing_ (a tolerant enum: unknown values -> UNKNOWN) is called on a miss
        default_missing = vars(Enum)["_missing_"].__func__
        self.has_missing = getattr(tp._missing_, "__func__", None) is not default_missing
        self._by_json = {(type(member.value), member.value): member for member in tp}
        self._by_text = {str(member.value): member for member in tp}
        # Values with the same text (1 and "1") cannot round-trip through a flat string.
        self.flat = len(self._by_text) == len(tp)


_JSON_SCALARS = {str, int, float, bool, types.NoneType}


def _literal_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


class _Literal(_Native):
    flat = True
    kind = "literal"

    def __init__(self, values: tuple[Any, ...]) -> None:
        for value in values:
            if value is not None and type(value) not in {str, int, bool}:
                msg = f"unsupported Literal value {value!r}; use str, int, bool or None"
                raise TypeError(msg)
        self.values = values
        self.label = f"one of {list(values)}"
        # Keyed by type too, so True does not match Literal[1].
        self._json = {(type(value), value) for value in values}
        self._text = {_literal_text(value): value for value in values}
        self.flat = len(self._text) == len(values)  # Literal[1, "1"]: same text


class _Optional(_Native):
    kind = "optional"

    def __init__(self, inner: Converter) -> None:
        self.inner = inner
        self.flat = inner.flat  # "" is None in the flat codec (3.x pack writes None as "")


class _Sequence(_Native):
    """``list[T]``, ``tuple[T, ...]``, ``set[T]``, ``frozenset[T]``; the JSON form is a list."""

    kind = "sequence"

    def __init__(self, item: Converter, tp: type) -> None:
        self.item = item
        self.tp: Any = tp


class _Dict(_Native):
    """``dict[str, T]``."""

    kind = "dict"

    def __init__(self, item: Converter) -> None:
        self.item = item


class _TypedDict(_Native):
    """A ``TypedDict``: a plain ``dict`` of the declared keys present in the input.

    ``Required`` keys must be there; ``NotRequired`` keys that are missing stay missing (the
    dict is its own "set fields" record). Unknown keys are dropped, as for models.
    """

    kind = "typeddict"

    def __init__(self, tp: type) -> None:
        self.tp = tp
        self._fields: tuple[tuple[str, Converter, bool], ...] | None = None
        self._compiling = False
        self._lock = threading.RLock()

    @property
    def fields(self) -> tuple[tuple[str, Converter, bool], ...]:
        if self._fields is not None:
            return self._fields
        with self._lock:  # another thread waits; a recursive reference in this one is _NotReady
            if self._fields is None:
                if self._compiling:
                    raise _NotReady(self.tp)
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


class _Union(_Native):
    """``A | B | ...`` (with or without ``None``), smart mode (PD-36).

    A member whose type matches the value exactly is tried first (``int | str`` keeps ``1`` and
    ``"1"`` apart, ``float | int`` keeps ``1`` an int), then every member left to right; the
    first that accepts wins. With a :class:`Discriminator`, the tag field picks the member.
    """

    kind = "union"

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
        self.tag_label = ""
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
            self.tag_label = f"one of {[value for _, value in tags]}"
            self._tags = tags
        return self._tags


@dataclasses.dataclass(frozen=True, slots=True)
class FieldSpec:
    name: str
    converter: Converter
    default: Any = MISSING
    default_factory: Callable[[], Any] | None = None


class ModelConverter(Converter):
    """Converter for a registered model class, a stdlib dataclass or a NamedTuple.

    The fields are compiled here, in Python; loading and dumping run on the compiled Rust
    schema (``aiogram._core.ModelSchema``), which replaces these methods per instance on first
    use. Registered models are built without calling ``__init__`` and must have an instance
    ``__dict__``; dataclasses and NamedTuples are built with ``tp(**values)``, so
    ``__post_init__`` runs (a ``ValueError`` there becomes a :class:`ConversionError`).
    """

    kind = "model"

    def __init__(self, tp: type, *, is_model: bool) -> None:
        self.tp = tp
        self.is_model = is_model
        self._fields: tuple[FieldSpec, ...] | None = None
        self._compiling = False
        self._lock = threading.RLock()

    @property
    def fields(self) -> tuple[FieldSpec, ...]:
        # Lazy: a class may refer to itself (or to a class defined later) through its fields.
        if self._fields is not None:
            return self._fields
        with self._lock:  # another thread waits; a recursive reference in this one is _NotReady
            if self._fields is None:
                if self._compiling:
                    raise _NotReady(self.tp)
                self._compiling = True
                try:
                    self._fields = _compile(self.tp)
                finally:
                    self._compiling = False
            return self._fields

    def _rust_schema(self) -> Any:
        """The compiled Rust schema (compiling the fields first); also used for nested models."""
        schema = self.__dict__.get("_schema")
        if schema is None:
            self.fields  # noqa: B018
            schema = _rust().ModelSchema(self)
            # Instance attributes shadow the methods below: later calls go straight to Rust.
            vars(self).update(
                _schema=schema,
                from_json=schema.load_dict,
                load_json=schema.load_json,
                to_json=schema.to_json,
                dump=schema.dump,
                from_flat=schema.from_flat,
                to_flat=schema.to_flat,
            )
        return schema

    def from_json(self, value: Any) -> Any:
        """A JSON-shaped mapping -> instance (unknown keys ignored)."""
        return self._rust_schema().load_dict(value)

    def load_json(self, data: bytes | bytearray | str) -> Any:
        """JSON text -> instance in one pass, as ``json.loads`` + :meth:`from_json` would."""
        return self._rust_schema().load_json(data)

    def to_json(self, value: Any) -> Any:
        return self._rust_schema().to_json(value)

    def dump(self, value: Any, *, exclude_unset: bool = False) -> dict[str, Any]:
        """Instance -> JSON-shaped dict; validates the values."""
        return self._rust_schema().dump(value, exclude_unset=exclude_unset)  # type: ignore[no-any-return]

    def from_flat(self, parts: Sequence[str]) -> Any:
        """Callback-data parts (one string per field, in field order) -> instance."""
        return self._rust_schema().from_flat(parts)

    def to_flat(self, value: Any) -> list[str]:
        """Instance -> callback-data parts, one string per field in field order."""
        return self._rust_schema().to_flat(value)  # type: ignore[no-any-return]

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

_CORE: Any = None


def _rust() -> Any:
    """``aiogram._core``, imported on first use: importing this module stays stdlib-only."""
    global _CORE  # noqa: PLW0603
    if _CORE is None:
        _CORE = importlib.import_module("aiogram._core")
    return _CORE


def _generated_hash(tp: type) -> bool:
    """Whether a dataclass's ``__hash__`` was generated by ``dataclasses`` (from its fields)."""
    code = getattr(vars(tp).get("__hash__"), "__code__", None)
    return code is not None and code.co_filename.startswith("<")  # exec'd, not in a source file


def _unhashable(converter: Converter) -> bool:
    """Whether ``converter`` can produce a value that cannot go in a set."""
    if isinstance(converter, (_Dict, _TypedDict)):
        return True
    if isinstance(converter, _Sequence):
        return converter.tp in {list, set} or _unhashable(converter.item)
    if isinstance(converter, _Optional):
        return _unhashable(converter.inner)
    if isinstance(converter, _Union):
        return any(_unhashable(member) for member in converter.members)
    if isinstance(converter, ModelConverter):
        tp = converter.tp
        if getattr(tp, "__hash__", None) is None:  # a non-frozen dataclass
            return True
        hashed: set[str] | None = None  # the fields a generated __hash__ uses
        if _is_namedtuple(tp):
            hashed = set(tp._fields)  # type: ignore[attr-defined]
        elif dataclasses.is_dataclass(tp) and _generated_hash(tp):
            hashed = {
                field.name
                for field in dataclasses.fields(tp)
                if field.hash or (field.hash is None and field.compare)
            }
        if hashed:
            with contextlib.suppress(NameError):  # a field type defined later
                return any(_unhashable(f.converter) for f in converter.fields if f.name in hashed)
    return False


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
            if isinstance(marker, Converter):  # a per-field converter (PD-36)
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
        if _unhashable(item):
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
