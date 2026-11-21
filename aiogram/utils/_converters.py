"""
Converter core, Python side (private; F-08, PD-36, plan-10).

Python resolves annotations and builds the typed ``aiogram._core`` objects (``Kind``, ``Field``,
``ModelCore``); Rust does every conversion. This module holds:

- the annotation resolver: forward references evaluated per field in the namespace of the class
  that declares it, ``Annotated`` markers, ``NewType`` and ``type X = ...`` aliases, defaults and
  stored keys. Converter lookup order: the field (``Annotated[T, Conv]``), the class
  (``converters={T: Conv}``), the type's own ``__aiogram_converter__`` hook (found along the MRO),
  the built-ins. There is no global registry;
- :class:`ModelBase`, the ``dataclass_transform`` base that ``FSMData`` (F-09) and
  ``CallbackData`` (F-11) build on;
- :func:`json_schema`, :func:`flat_schema` and :func:`json_codec`, the codecs consumers use.

``import aiogram`` does not import this module (B-01: it loads ``aiogram._core``).
"""

from __future__ import annotations

import contextlib
import dataclasses
import enum
import re
import reprlib
import sys
import threading
import types
import typing
from collections.abc import Callable, Iterable, Mapping
from copy import deepcopy
from datetime import date, datetime, time, timedelta
from decimal import Decimal
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
    TypeAlias,
    TypeVar,
    dataclass_transform,
    get_args,
    get_origin,
    is_typeddict,
)
from uuid import UUID

from aiogram import _core
from aiogram.utils.converters import (
    MISSING,
    ConversionError,
    Converter,
    DecimalAsNumber,
    Discriminator,
    EnumByName,
    EpochDatetime,
    ErrorDetail,
    IsoDatetime,
    Key,
    UuidHex,
    _FieldInfo,
    _Native,
    field,
)

__all__ = ["ModelBase", "fields_set", "flat_schema", "json_codec", "json_schema"]

_core.converters_init(ConversionError, ErrorDetail, MISSING)

_T = TypeVar("_T")

Rename: TypeAlias = Literal["camel", "snake", "kebab"] | Callable[[str], str]

# ---------------------------------------------------------------------------------------------
# Annotations and namespaces
# ---------------------------------------------------------------------------------------------

if sys.version_info >= (3, 14):
    import annotationlib

    def _own_annotations(cls: type) -> dict[str, Any]:
        # FORWARDREF: a name that is not bound yet (the class itself while __init_subclass__
        # runs, a class defined later) becomes a ForwardRef instead of raising NameError.
        return dict(annotationlib.get_annotations(cls, format=annotationlib.Format.FORWARDREF))

    def _string_annotation(cls: type, name: str) -> str | None:
        return annotationlib.get_annotations(cls, format=annotationlib.Format.STRING).get(name)

    def _namespace_annotations(namespace: Mapping[str, Any]) -> dict[str, Any]:
        annotate = annotationlib.get_annotate_from_class_namespace(namespace)
        if annotate is None:
            return dict(namespace.get("__annotations__", {}))
        return dict(
            annotationlib.call_annotate_function(annotate, annotationlib.Format.FORWARDREF)
        )

else:  # pragma: no cover

    def _own_annotations(cls: type) -> dict[str, Any]:
        return dict(cls.__dict__.get("__annotations__", {}))

    def _string_annotation(cls: type, name: str) -> str | None:  # noqa: ARG001
        return None

    def _namespace_annotations(namespace: Mapping[str, Any]) -> dict[str, Any]:
        return dict(namespace.get("__annotations__", {}))


if sys.version_info >= (3, 12):
    _ALIAS_TYPES: tuple[type, ...] = (typing.TypeAliasType,)
else:  # pragma: no cover
    _ALIAS_TYPES = ()

_UNION_TYPES = (typing.Union, types.UnionType)
# A ClassVar written as text (`from __future__ import annotations`), the way dataclasses detects it
_CLASSVAR_TEXT = re.compile(r"^\s*(?:\w+\s*\.\s*)*ClassVar\b")
_KW_ONLY_TEXT = re.compile(r"^\s*(?:\w+\s*\.\s*)*KW_ONLY\s*$")
_INITVAR_TEXT = re.compile(r"^\s*(?:\w+\s*\.\s*)*InitVar\b")


def _text_of(raw: Any) -> str | None:
    if isinstance(raw, ForwardRef):
        return raw.__forward_arg__
    return raw if isinstance(raw, str) else None


def _is_classvar(raw: Any) -> bool:
    text = _text_of(raw)
    if text is not None:
        return bool(_CLASSVAR_TEXT.match(text))
    return raw is ClassVar or get_origin(raw) is ClassVar


def _is_typeish(value: Any) -> bool:
    """A class-body name an annotation may refer to: a nested class or a type alias."""
    return isinstance(value, (type, typing.NewType, types.GenericAlias, *_ALIAS_TYPES))


@dataclasses.dataclass(slots=True)
class _Scope:
    """Where the annotations of one class are evaluated."""

    globals: dict[str, Any]
    locals: dict[str, Any]


def _scope(cls: type, fields: Iterable[str], frame_locals: Mapping[str, Any] | None) -> _Scope:
    """The namespace of ``cls``'s own annotations.

    Lookup order: the class itself by name (not bound in its module yet while
    ``__init_subclass__`` runs), class-body names that are types and not field names (nested
    classes; a field default or slot never shadows a type: ``date: date = date(...)``), the
    locals of the defining function, the module globals.
    """
    module = sys.modules.get(cls.__module__)
    namespace: dict[str, Any] = dict(frame_locals or {})
    skip = set(fields)
    namespace.update(
        (name, value)
        for name, value in vars(cls).items()
        if name not in skip and _is_typeish(value)
    )
    namespace[cls.__name__] = cls
    return _Scope(vars(module) if module is not None else {}, namespace)


def _evaluate(text: str, scope: _Scope) -> Any:
    """Evaluate an annotation written as text; ``NameError`` for a name not defined yet."""
    try:
        return eval(text, scope.globals, scope.locals)  # noqa: S307
    except NameError:
        raise
    except Exception as e:  # noqa: BLE001
        msg = f"cannot evaluate annotation {text!r}: {e}"
        raise TypeError(msg) from None


def _field_hint(owner: type, name: str, raw: Any, scope: _Scope) -> Any:
    """The annotation of field ``name`` declared on ``owner``, evaluated."""
    own = vars(owner).get(name, MISSING)
    if own is not MISSING and raw is own and not isinstance(raw, str):
        # Without `from __future__ import annotations` the annotation is evaluated in the class
        # body, where the field's default (or slot) has already replaced a type of that name.
        text = _string_annotation(owner, name)
        if text is None:
            msg = (
                f"the annotation evaluates to the field's own default ({raw!r}); quote it or use "
                f"`from __future__ import annotations`"
            )
            raise TypeError(msg)
        raw = text
    text = _text_of(raw)
    return _evaluate(text, scope) if text is not None else raw


def _class_hints(cls: type) -> dict[str, tuple[Any, type]]:
    """Field name -> (raw annotation, declaring class) over ``cls``'s MRO, later bases first."""
    hints: dict[str, tuple[Any, type]] = {}
    for base in reversed(cls.__mro__):
        if base is object or base.__module__ == "builtins":
            continue
        for name, raw in _own_annotations(base).items():
            hints[name] = (raw, base)
    return hints


# ---------------------------------------------------------------------------------------------
# The resolver
# ---------------------------------------------------------------------------------------------

_SCALARS: dict[type, _core.Kind] = {
    str: _core.Kind.str_(),
    int: _core.Kind.int_(),
    float: _core.Kind.float_(),
    bool: _core.Kind.bool_(),
    UUID: _core.Kind.uuid(),
    datetime: _core.Kind.datetime(),
    date: _core.Kind.date(),
    time: _core.Kind.time(),
    timedelta: _core.Kind.timedelta(),
    Decimal: _core.Kind.decimal(),
    bytes: _core.Kind.bytes_(),
    Fraction: _core.Kind.text(Fraction, Fraction, str, flat=True),
}
_JSON_SCALARS = (str, int, float, bool, type(None))


def _name(tp: Any) -> str:
    return tp.__qualname__ if isinstance(tp, type) else repr(tp).removeprefix("typing.")


def _is_namedtuple(tp: type) -> bool:
    return issubclass(tp, tuple) and hasattr(tp, "_fields")


def _is_foreign(tp: type) -> bool:
    return is_typeddict(tp) or dataclasses.is_dataclass(tp) or _is_namedtuple(tp)


def _enum_kind(tp: type[enum.Enum], *, by_name: bool = False) -> _core.Kind:
    if issubclass(tp, enum.Flag):
        # composite and zero flags are not members: they could not round-trip
        msg = f"{tp.__name__} is a Flag enum, which is not supported"
        raise TypeError(msg)
    if not by_name:
        for member in tp:
            if type(member.value) not in _JSON_SCALARS:
                msg = f"{tp.__name__}.{member.name} value {member.value!r} is not a JSON scalar"
                raise TypeError(msg)
    # an overridden _missing_ (a tolerant enum: unknown values -> UNKNOWN) is called on a miss
    missing = getattr(tp._missing_, "__func__", None) is not enum.Enum._missing_.__func__  # type: ignore[attr-defined]
    return _core.Kind.enum(tp, by_name=by_name, missing=missing)


def _literal_kind(values: tuple[Any, ...]) -> _core.Kind:
    for value in values:
        if value is not None and type(value) not in {str, int, bool}:
            msg = f"unsupported Literal value {value!r}; use str, int, bool or None"
            raise TypeError(msg)
    return _core.Kind.literal(values)


def _flat_converter(converter: Converter) -> bool:
    cls = type(converter)
    return cls.to_str is not Converter.to_str and cls.from_str is not Converter.from_str


class _Compiler:
    """One compile: resolves annotations for ``owner`` with its class-level converter map.

    Foreign dataclasses, NamedTuples and TypedDicts are compiled here, within the owner's
    compile (the class map reaches into them); the memo gives recursive ones one core.
    """

    def __init__(
        self,
        owner: Any,
        converters: Mapping[type, Converter],
        frame_locals: Mapping[str, Any] | None = None,
    ) -> None:
        self.owner = owner
        self.converters = converters
        self.frame_locals = frame_locals
        self.memo: dict[type, _core.ModelCore] = {}
        self.aliases: dict[int, tuple[_core.KindCell | None, _core.Kind | None]] = {}

    # annotations -> kinds

    def kind(self, tp: Any, scope: _Scope) -> _core.Kind:  # noqa: C901, PLR0911, PLR0912
        text = _text_of(tp)
        if text is not None:
            return self.kind(_evaluate(text, scope), scope)
        origin = get_origin(tp)
        if origin is Annotated:
            return self.annotated(tp, scope)
        if origin in {Required, NotRequired}:  # TypedDict keys; required-ness comes from the class
            return self.kind(get_args(tp)[0], scope)
        if isinstance(tp, typing.NewType):
            return self.kind(tp.__supertype__, scope)
        if isinstance(tp, _ALIAS_TYPES):
            return self.alias(tp, scope)
        if origin is not None and isinstance(origin, _ALIAS_TYPES):
            return self.kind(self.substitute(tp, origin), scope)
        if origin is None and isinstance(tp, type):
            return self.class_kind(tp)
        args = get_args(tp)
        if origin in _UNION_TYPES:
            return self.union(tp, scope, None)
        if origin is Literal:
            return _literal_kind(args)
        if origin is list and len(args) == 1:
            return _core.Kind.sequence(self.kind(args[0], scope), list)
        if origin is tuple and len(args) == 2 and args[1] is Ellipsis:  # noqa: PLR2004
            return _core.Kind.sequence(self.kind(args[0], scope), tuple)
        if origin is tuple and args and Ellipsis not in args:
            return _core.Kind.tuple_([self.kind(arg, scope) for arg in args])
        if origin in {set, frozenset} and len(args) == 1:
            if self.unhashable(args[0], scope, set()):
                msg = f"unhashable set item {_name(args[0])}"
                raise TypeError(msg)
            return _core.Kind.sequence(self.kind(args[0], scope), origin)
        if origin is dict and len(args) == 2:  # noqa: PLR2004
            if args[0] is not str:
                msg = f"dict keys must be str, not {_name(args[0])}"
                raise TypeError(msg)
            return _core.Kind.dict_(self.kind(args[1], scope))
        msg = f"unsupported annotation {_name(tp)}"
        raise TypeError(msg)

    def annotated(self, tp: Any, scope: _Scope) -> _core.Kind:
        base, *metadata = get_args(tp)
        if any(isinstance(marker, Key) for marker in metadata):
            msg = "Key applies to a field, not to a type inside a container"
            raise TypeError(msg)
        markers = [m for m in metadata if isinstance(m, (Converter, Discriminator))]
        if len(markers) > 1:
            msg = f"more than one converter or Discriminator in {_name(tp)}"
            raise TypeError(msg)
        if not markers:
            return self.kind(base, scope)
        marker = markers[0]
        if isinstance(marker, Discriminator):
            return self.union(base, scope, marker.field)
        return self.converter_kind(marker, base, scope)

    def class_kind(self, tp: type) -> _core.Kind:
        # the class map: exact type, then along the MRO (not through the built-in scalars, so
        # a `date` entry does not catch `datetime` fields)
        for base in tp.__mro__:
            if base is not tp and base in _SCALARS:
                continue
            converter = self.converters.get(base)
            if converter is not None:
                return self.converter_kind(converter, tp, None)
        hook = getattr(tp, "__aiogram_converter__", None)
        if hook is not None:
            converter = hook()
            if not isinstance(converter, Converter):
                msg = (
                    f"{tp.__qualname__}.__aiogram_converter__() returned {converter!r}, "
                    f"not a Converter"
                )
                raise TypeError(msg)
            return self.converter_kind(converter, tp, None)
        if (kind := _SCALARS.get(tp)) is not None:
            return kind
        if issubclass(tp, enum.Enum):
            return _enum_kind(tp)
        if (core := vars(tp).get("__aiogram_core__")) is not None:
            return _core.Kind.model(core)
        if _is_foreign(tp):
            return _core.Kind.model(self.foreign(tp))
        msg = f"unsupported annotation {_name(tp)}"
        raise TypeError(msg)

    def converter_kind(self, converter: Converter, base: Any, scope: _Scope | None) -> _core.Kind:
        if not isinstance(converter, _Native):
            return _core.Kind.python(converter, flat=_flat_converter(converter))
        tp = self.unwrap(base, scope or _Scope({}, {}))
        expected: type
        if isinstance(converter, (IsoDatetime, EpochDatetime)):
            expected = datetime
        elif isinstance(converter, DecimalAsNumber):
            expected = Decimal
        elif isinstance(converter, UuidHex):
            expected = UUID
        else:
            expected = enum.Enum
        if not (isinstance(tp, type) and issubclass(tp, expected)):
            msg = f"{converter!r} applies to {expected.__name__}, not {_name(tp)}"
            raise TypeError(msg)
        if isinstance(converter, IsoDatetime):
            return _core.Kind.datetime(timespec=converter.timespec, sep=converter.sep)
        if isinstance(converter, EpochDatetime):
            return _core.Kind.datetime(epoch=converter.unit)
        if isinstance(converter, DecimalAsNumber):
            return _core.Kind.decimal(number=True)
        if isinstance(converter, UuidHex):
            return _core.Kind.uuid(hex=True)
        if not isinstance(converter, EnumByName):  # pragma: no cover
            msg = f"unknown converter {converter!r}"
            raise TypeError(msg)
        return _enum_kind(typing.cast(type[enum.Enum], tp), by_name=True)

    def unwrap(self, tp: Any, scope: _Scope) -> Any:
        """The class under text, ``NewType`` and aliases (to check a converter applies)."""
        while True:
            text = _text_of(tp)
            if text is not None:
                tp = _evaluate(text, scope)
            elif isinstance(tp, typing.NewType):
                tp = tp.__supertype__
            elif isinstance(tp, _ALIAS_TYPES):
                tp = tp.__value__
            else:
                return tp

    def union(self, tp: Any, scope: _Scope, discriminator: str | None) -> _core.Kind:
        tp = self.unwrap(tp, scope)
        if get_origin(tp) not in _UNION_TYPES:
            msg = f"Discriminator needs a union of models, got {_name(tp)}"
            raise TypeError(msg)
        args = get_args(tp)
        nullable = type(None) in args
        rest = [arg for arg in args if arg is not type(None)]
        if discriminator is None and len(rest) == 1:
            return _core.Kind.optional(self.kind(rest[0], scope))
        if discriminator is not None and len(rest) < 2:  # noqa: PLR2004
            msg = f"Discriminator needs a union of models, got {_name(tp)}"
            raise TypeError(msg)
        members = [self.kind(arg, scope) for arg in rest]
        return _core.Kind.union(members, nullable=nullable, discriminator=discriminator)

    def alias(self, alias: Any, scope: _Scope) -> _core.Kind:
        """``type X = ...``: a recursive reference to ``X`` inside its value is a lazy kind."""
        entry = self.aliases.get(id(alias))
        if entry is not None:
            cell, kind = entry
            if kind is not None:
                return kind
            if cell is None:
                cell = _core.KindCell()
                self.aliases[id(alias)] = (cell, None)
            return _core.Kind.lazy(cell, alias.__name__)
        self.aliases[id(alias)] = (None, None)
        kind = self.kind(alias.__value__, scope)
        cell, _ = self.aliases[id(alias)]
        if cell is not None:
            cell.set(kind)
        self.aliases[id(alias)] = (cell, kind)
        return kind

    @staticmethod
    def substitute(tp: Any, origin: Any) -> Any:
        """``Pair[int]`` for ``type Pair[T] = tuple[T, T]``."""
        try:
            return origin.__value__[get_args(tp)]
        except TypeError as e:
            msg = f"cannot apply {_name(origin)} to {get_args(tp)}: {e}"
            raise TypeError(msg) from None

    # foreign classes

    def foreign(self, tp: type) -> _core.ModelCore:
        core = self.memo.get(tp)
        if core is None:
            core = _core.ModelCore(tp, build="dict" if is_typeddict(tp) else "call")
            self.memo[tp] = core
            core.set_fields(self.foreign_fields(tp))
        return core

    def foreign_fields(self, tp: type) -> list[_core.Field]:
        hints = _class_hints(tp)
        scopes: dict[type, _Scope] = {}

        def resolve(name: str) -> _core.Kind:
            raw, owner = hints[name]
            if owner not in scopes:
                scopes[owner] = _scope(owner, _own_annotations(owner), self.frame_locals)
            try:
                return self.kind(_field_hint(owner, name, raw, scopes[owner]), scopes[owner])
            except TypeError as e:
                msg = f"{tp.__qualname__}.{name}: {e}"
                raise TypeError(msg) from None

        fields = []
        if is_typeddict(tp):
            required_keys = tp.__required_keys__  # type: ignore[attr-defined]
            for name, (raw, _) in hints.items():
                fields.append(
                    _core.Field(
                        name, resolve(name), required=self.required(raw, name in required_keys)
                    )
                )
            return fields
        if _is_namedtuple(tp):
            defaults = tp._field_defaults  # type: ignore[attr-defined]
            items = [(name, defaults.get(name, MISSING), MISSING) for name in tp._fields]  # type: ignore[attr-defined]
        else:
            for name, (raw, _) in hints.items():
                if (
                    isinstance(raw, dataclasses.InitVar)
                    or _INITVAR_TEXT.match(_text_of(raw) or "")
                ) and getattr(tp, name, MISSING) is MISSING:
                    msg = f"{tp.__qualname__}.{name}: required InitVar is not supported"
                    raise TypeError(msg)
            items = [
                (spec.name, spec.default, spec.default_factory)
                for spec in dataclasses.fields(tp)
                if spec.init
            ]
        for name, default, factory in items:
            if name not in hints:  # an untyped collections.namedtuple field
                msg = f"{tp.__qualname__}.{name}: the field has no annotation"
                raise TypeError(msg)
            fields.append(_field(name, resolve(name), default=default, factory=factory))
        return fields

    @staticmethod
    def required(raw: Any, default: bool) -> bool:
        """A TypedDict key's required-ness: the hint's wrapper wins (``__required_keys__``
        misses ``Required`` / ``NotRequired`` inside ``Annotated`` under string annotations)."""
        text = _text_of(raw)
        if text is not None:
            if re.match(r"^\s*(?:\w+\.)*Required\b", text) or "Annotated[Required" in text:
                return True
            if re.match(r"^\s*(?:\w+\.)*NotRequired\b", text) or "Annotated[NotRequired" in text:
                return False
            return default
        while get_origin(raw) is Annotated:
            raw = get_args(raw)[0]
        if get_origin(raw) is Required:
            return True
        if get_origin(raw) is NotRequired:
            return False
        return default

    # set items

    def unhashable(self, tp: Any, scope: _Scope, seen: set[int]) -> bool:  # noqa: C901, PLR0911
        """Whether ``tp`` can produce a value that cannot go in a set."""
        text = _text_of(tp)
        if text is not None:
            return self.unhashable(_evaluate(text, scope), scope, seen)
        origin = get_origin(tp)
        args = get_args(tp)
        if origin is Annotated:
            if any(isinstance(marker, Converter) for marker in args[1:]):
                return False  # a converter decides its values
            return self.unhashable(args[0], scope, seen)
        if isinstance(tp, typing.NewType):
            return self.unhashable(tp.__supertype__, scope, seen)
        if isinstance(tp, _ALIAS_TYPES):
            if id(tp) in seen:
                return False
            seen.add(id(tp))
            return self.unhashable(tp.__value__, scope, seen)
        if origin in _UNION_TYPES:
            return any(self.unhashable(arg, scope, seen) for arg in args)
        if origin in {list, dict, set}:
            return True
        if origin in {tuple, frozenset}:
            return any(self.unhashable(arg, scope, seen) for arg in args if arg is not Ellipsis)
        if not isinstance(tp, type) or id(tp) in seen:
            return False  # a recursive class: decided by its other fields
        seen.add(id(tp))
        if is_typeddict(tp) or getattr(tp, "__hash__", None) is None:
            return True
        hashed = _hashed_fields(tp)
        if not hashed:
            return False
        hints = _class_hints(tp)
        for name in hashed:
            raw, owner = hints[name]
            owner_scope = _scope(owner, _own_annotations(owner), self.frame_locals)
            if self.unhashable(_field_hint(owner, name, raw, owner_scope), owner_scope, seen):
                return True
        return False


def _hashed_fields(tp: type) -> list[str]:
    """The fields a field-based ``__hash__`` of ``tp`` uses (empty: not field-based)."""
    info = vars(tp).get("__aiogram_info__")
    if info is not None:
        return list(info.compare) if info.frozen else []
    if _is_namedtuple(tp):
        return list(tp._fields)  # type: ignore[attr-defined]
    if dataclasses.is_dataclass(tp):
        params = tp.__dataclass_params__  # type: ignore[attr-defined]
        if params.unsafe_hash or (params.eq and params.frozen):
            return [
                spec.name
                for spec in dataclasses.fields(tp)
                if spec.hash or (spec.hash is None and spec.compare)
            ]
    return []


def _is_hashable(value: Any) -> bool:
    try:
        hash(value)
    except TypeError:
        return False
    return True


def _field(
    name: str,
    kind: _core.Kind,
    *,
    default: Any = MISSING,
    factory: Any = MISSING,
    **options: Any,
) -> _core.Field:
    """A ``Field``; a mutable default (``[]``, ``{}``, ``set()``) is copied per instance (D115)."""
    if default is not MISSING and not _is_hashable(default):
        default, factory = MISSING, partial(deepcopy, default)
    return _core.Field(
        name,
        kind,
        default=None if default is MISSING else default,
        has_default=default is not MISSING,
        factory=None if factory is MISSING else factory,
        **options,
    )


# ---------------------------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------------------------


def _camel(name: str) -> str:
    head = len(name) - len(name.lstrip("_"))
    first, *rest = name[head:].split("_")
    return name[:head] + first + "".join(part[:1].upper() + part[1:] for part in rest)


def _snake(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name).lower()


def _kebab(name: str) -> str:
    head = len(name) - len(name.lstrip("_"))
    return name[:head] + _snake(name[head:]).replace("_", "-")


_RENAMES: dict[str, Callable[[str], str]] = {"camel": _camel, "snake": _snake, "kebab": _kebab}


def _rename_function(rename: Rename | None) -> Callable[[str], str] | None:
    if rename is None or callable(rename):
        return rename
    if rename not in _RENAMES:
        msg = f"rename must be one of {sorted(_RENAMES)} or a callable, not {rename!r}"
        raise TypeError(msg)
    return _RENAMES[rename]


# ---------------------------------------------------------------------------------------------
# ModelBase
# ---------------------------------------------------------------------------------------------


@dataclasses.dataclass(slots=True)
class _Decl:
    """One field as declared in a class body (before its annotation is resolved)."""

    name: str
    raw: Any
    owner: type
    # MISSING as a dataclass default would mean "no default"
    default: Any = dataclasses.field(default_factory=lambda: MISSING)
    factory: Any = dataclasses.field(default_factory=lambda: MISSING)
    init: bool = True
    kw_only: bool = True
    repr: bool = True
    compare: bool = True
    key: str | None = None
    load: tuple[str, ...] = ()
    converter: Converter | None = None


@dataclasses.dataclass(slots=True)
class _ModelInfo:
    """Per-class state of a ``ModelBase`` subclass (``vars(cls)["__aiogram_info__"]``)."""

    own: tuple[_Decl, ...]
    rename: Rename | None
    converters: Mapping[type, Converter]
    frozen: bool
    # the defining function's frame (or class-body namespace), kept until the fields resolve
    locals_source: Any
    lock: threading.RLock
    names: tuple[str, ...] = ()
    init: tuple[str, ...] = ()
    repr: tuple[str, ...] = ()
    compare: tuple[str, ...] = ()

    def frame_locals(self) -> Mapping[str, Any] | None:
        source = self.locals_source
        if source is None:
            return None
        if isinstance(source, types.FrameType):
            return dict(source.f_locals)
        return dict(source)


def _info(cls: type) -> _ModelInfo:
    info: _ModelInfo = vars(cls)["__aiogram_info__"]
    return info


def _parent_info(cls: type) -> _ModelInfo | None:
    for base in cls.__mro__[1:]:
        info = vars(base).get("__aiogram_info__")
        if info is not None:
            return info  # type: ignore[no-any-return]
    return None


class _NotDefined(NameError):
    """A model refers to names that are not defined (yet)."""


def _locals_source() -> Any:
    """The frame that defines the class being set up, past ``__init_subclass__`` chains and the
    metaclass: a function frame (its locals are read at each resolve, so classes defined later
    in the same function resolve too), a class-body namespace, or ``None`` at module level."""
    frame = sys._getframe(1)  # noqa: SLF001
    own = {_setup.__code__, _ModelMeta.__new__.__code__}
    while frame is not None and (
        frame.f_code in own or frame.f_code.co_name == "__init_subclass__"
    ):
        frame = frame.f_back  # type: ignore[assignment]
    if frame is None or frame.f_locals is frame.f_globals:
        return None
    if frame.f_code.co_flags & 0x1:  # CO_OPTIMIZED: a function frame
        return frame
    return frame.f_locals


def _declarations(cls: type) -> tuple[_Decl, ...]:
    own = _own_annotations(cls)
    slots_defaults: dict[str, Any] | None = vars(cls).get("__aiogram_defaults__")
    decls = []
    for name, raw in own.items():
        if _is_classvar(raw):
            continue
        text = _text_of(raw)
        if raw is dataclasses.KW_ONLY or (text is not None and _KW_ONLY_TEXT.match(text)):
            msg = f"{cls.__qualname__}: KW_ONLY is not needed, every field is keyword-only"
            raise TypeError(msg)
        if isinstance(raw, dataclasses.InitVar) or (
            text is not None and _INITVAR_TEXT.match(text)
        ):
            msg = f"{cls.__qualname__}.{name}: InitVar is not supported"
            raise TypeError(msg)
        value = (slots_defaults if slots_defaults is not None else vars(cls)).get(name, MISSING)
        if isinstance(value, types.MemberDescriptorType):
            value = MISSING  # a user-declared slot, not a default
        decl = _Decl(name, raw, cls)
        if isinstance(value, _FieldInfo):
            decl.default, decl.factory = value.default, value.default_factory
            decl.init, decl.repr, decl.compare = value.init, value.repr, value.compare
            decl.kw_only = True if value.kw_only is None else value.kw_only
            decl.key, decl.load, decl.converter = value.key, value.load, value.converter
        elif isinstance(value, dataclasses.Field):
            decl.default, decl.factory = value.default, value.default_factory
            decl.init, decl.repr, decl.compare = value.init, value.repr, value.compare
            decl.kw_only = True if value.kw_only is MISSING else bool(value.kw_only)
        else:
            decl.default = value
        if isinstance(value, (_FieldInfo, dataclasses.Field)) and slots_defaults is None:
            # as dataclasses: the class attribute becomes the plain default, or goes away
            if decl.default is MISSING:
                delattr(cls, name)
            else:
                setattr(cls, name, decl.default)
        if not decl.init and decl.default is MISSING and decl.factory is MISSING:
            msg = f"{cls.__qualname__}.{name}: init=False needs a default or a default_factory"
            raise TypeError(msg)
        decls.append(decl)
    return tuple(decls)


def _all_declarations(cls: type) -> list[_Decl]:
    """Every field of ``cls``: inherited ones first, a redeclared field keeps its position."""
    fields: dict[str, _Decl] = {}
    for base in reversed(cls.__mro__):
        info = vars(base).get("__aiogram_info__")
        if info is not None:
            for decl in info.own:
                fields[decl.name] = decl
    return list(fields.values())


def _model_field(
    compiler: _Compiler,
    cls: type,
    decl: _Decl,
    scope: _Scope,
    rename: Callable[[str], str] | None,
) -> _core.Field:
    hint = _field_hint(decl.owner, decl.name, decl.raw, scope)
    key, load, converter = decl.key, decl.load, decl.converter
    explicit_key = key is not None
    if get_origin(hint) is Annotated:
        base, *metadata = get_args(hint)
        keys = [marker for marker in metadata if isinstance(marker, Key)]
        if keys:
            if len(keys) > 1 or explicit_key or load:
                msg = "the stored key is given more than once (Key / field(key=, load=))"
                raise TypeError(msg)
            key, load, explicit_key = keys[0].name, keys[0].load, True
            rest = [marker for marker in metadata if not isinstance(marker, Key)]
            hint = Annotated[(base, *rest)] if rest else base
    if converter is not None:
        if get_origin(hint) is Annotated and any(
            isinstance(marker, (Converter, Discriminator)) for marker in get_args(hint)[1:]
        ):
            msg = "the converter is given twice (Annotated and field(converter=))"
            raise TypeError(msg)
        kind = compiler.converter_kind(converter, hint, scope)
    else:
        kind = compiler.kind(hint, scope)
    if key is None:
        key = rename(decl.name) if rename is not None else decl.name
        if not isinstance(key, str):
            msg = f"rename returned {key!r}, not a str"
            raise TypeError(msg)
    return _field(
        decl.name,
        kind,
        default=decl.default,
        factory=decl.factory,
        key=key,
        load=load,
        init=decl.init,
        kw_only=decl.kw_only,
        keyed=explicit_key or rename is not None,
    )


def _compile(cls: type) -> list[_core.Field]:
    """The fields of a ``ModelBase`` class: ``TypeError`` for a bad field, ``_NotDefined`` when
    names are missing (the other fields are still checked)."""
    info = _info(cls)
    frame_locals = info.frame_locals()
    compiler = _Compiler(cls, info.converters, frame_locals)
    rename = _rename_function(info.rename)
    scopes: dict[type, _Scope] = {}
    fields = []
    missing: list[str] = []
    for decl in _all_declarations(cls):
        if decl.owner not in scopes:
            owner_info = _info(decl.owner)
            scopes[decl.owner] = _scope(
                decl.owner, [d.name for d in owner_info.own], owner_info.frame_locals()
            )
        try:
            fields.append(_model_field(compiler, cls, decl, scopes[decl.owner], rename))
        except NameError as e:
            missing.append(e.name or str(e))
        except TypeError as e:
            msg = f"{cls.__qualname__}.{decl.name}: {e}"
            raise TypeError(msg) from None
    if missing:
        names = sorted(set(missing))
        verb = "is" if len(names) == 1 else "are"
        msg = f"{cls.__qualname__} is not fully defined: {', '.join(names)} {verb} not defined"
        raise _NotDefined(msg)
    return fields


def _resolve(cls: type) -> None:
    """``ModelCore``'s resolve callback: compile a class whose names were missing at creation."""
    info = _info(cls)
    core: _core.ModelCore = vars(cls)["__aiogram_core__"]
    with info.lock:
        if not core.ready:
            core.set_fields(_compile(cls))
            info.locals_source = None


def _frozen_setattr(self: Any, name: str, value: Any) -> None:
    msg = f"cannot assign to field {name!r}"
    raise dataclasses.FrozenInstanceError(msg)


def _frozen_delattr(self: Any, name: str) -> None:
    msg = f"cannot delete field {name!r}"
    raise dataclasses.FrozenInstanceError(msg)


def _frozen_hash(self: Any) -> int:
    return hash(tuple(getattr(self, name) for name in type(self).__aiogram_info__.compare))


def _setup(
    cls: Any,  # attributes are set on it
    rename: Rename | None,
    converters: Mapping[type, Converter] | None,
    frozen: bool | None,
) -> None:
    parent = _parent_info(cls)
    if converters is not None and not all(isinstance(tp, type) for tp in converters):
        msg = f"{cls.__qualname__}: converters= keys must be types"
        raise TypeError(msg)
    if parent is not None and frozen is not None and frozen != parent.frozen:
        kinds = {True: "frozen", False: "non-frozen"}
        msg = (
            f"{cls.__qualname__}: cannot inherit a {kinds[frozen]} model from a "
            f"{kinds[parent.frozen]} one"
        )
        raise TypeError(msg)
    is_frozen = frozen if frozen is not None else (parent.frozen if parent else False)
    _rename_function(rename)  # reject a bad policy at class creation
    info = _ModelInfo(
        own=(),
        rename=rename if rename is not None else (parent.rename if parent else None),
        converters={**(parent.converters if parent else {}), **(converters or {})},
        frozen=is_frozen,
        locals_source=_locals_source(),
        lock=threading.RLock(),
    )
    cls.__aiogram_info__ = info
    info.own = _declarations(cls)
    decls = _all_declarations(cls)
    info.names = tuple(d.name for d in decls)
    info.init = tuple(d.name for d in decls if d.init)
    info.repr = tuple(d.name for d in decls if d.repr)
    info.compare = tuple(d.name for d in decls if d.compare)
    seen_default = None
    for decl in decls:
        if decl.init and not decl.kw_only:
            if decl.default is not MISSING or decl.factory is not MISSING:
                seen_default = decl.name
            elif seen_default is not None:
                msg = (
                    f"{cls.__qualname__}: positional field {decl.name!r} without a default "
                    f"follows {seen_default!r}"
                )
                raise TypeError(msg)
    post_init = callable(getattr(cls, "__post_init__", None))
    core = _core.ModelCore(cls, build="model", post_init=post_init, resolve=partial(_resolve, cls))
    cls.__aiogram_core__ = core
    body = vars(cls)
    if is_frozen:
        if "__setattr__" not in body:
            cls.__setattr__ = _frozen_setattr
        if "__delattr__" not in body:
            cls.__delattr__ = _frozen_delattr
        if "__hash__" not in body or (body["__hash__"] is None and "__eq__" not in body):
            cls.__hash__ = _frozen_hash
    try:
        fields = _compile(cls)
    except _NotDefined:
        return  # names defined later: compiled on first use (`_resolve`)
    core.set_fields(fields)
    info.locals_source = None


class _ModelMeta(type):
    """Only for ``slots=True``: ``__init_subclass__`` runs after the instance layout is fixed,
    so this moves the defaults out of the class namespace and declares the slots first."""

    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> _ModelMeta:
        if kwargs.get("slots"):
            if "__slots__" in namespace:
                msg = f"{name}: slots=True and __slots__ cannot be combined"
                raise TypeError(msg)
            names = [
                field_name
                for field_name, raw in _namespace_annotations(namespace).items()
                if not _is_classvar(raw)
            ]
            namespace["__aiogram_defaults__"] = {
                field_name: namespace.pop(field_name)
                for field_name in names
                if field_name in namespace
            }
            namespace["__slots__"] = tuple(names)
        return super().__new__(mcls, name, bases, namespace, **kwargs)


@dataclass_transform(kw_only_default=True, field_specifiers=(field, dataclasses.field))
class ModelBase(metaclass=_ModelMeta):
    """The base of converter-backed classes (``FSMData``, ``CallbackData``).

    Fields are annotated class attributes, as in a dataclass (PEP 681): ``_x`` names are fields,
    ``ClassVar`` is not, :func:`~aiogram.utils.converters.field` / ``dataclasses.field`` give
    ``default_factory``, ``init=False``, ``kw_only=False``, ``repr=False``, ``compare=False``.
    Every field is keyword-only unless ``kw_only=False``. The constructor checks every value
    (``ConversionError``); ``__post_init__`` runs after construction and after every load.

    Class keywords: ``rename=`` (``"camel"`` / ``"snake"`` / ``"kebab"`` / a callable: stored
    keys), ``converters={type: Converter}`` (this class's formats, inherited by subclasses),
    ``frozen=True``, ``slots=True``.
    """

    __slots__ = ("__fields_set__",)

    __aiogram_core__: ClassVar[_core.ModelCore]
    __aiogram_info__: ClassVar[_ModelInfo]

    def __init_subclass__(
        cls,
        *,
        rename: Rename | None = None,
        converters: Mapping[type, Converter] | None = None,
        frozen: bool | None = None,
        slots: bool = False,  # noqa: ARG003  (handled by the metaclass)
        **kwargs: Any,
    ) -> None:
        super().__init_subclass__(**kwargs)
        _setup(cls, rename, converters, frozen)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.__aiogram_core__.init(self, args, kwargs)

    @reprlib.recursive_repr()
    def __repr__(self) -> str:
        names = type(self).__aiogram_info__.repr
        args = ", ".join(f"{name}={getattr(self, name, MISSING)!r}" for name in names)
        return f"{type(self).__qualname__}({args})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return NotImplemented
        names = type(self).__aiogram_info__.compare
        return tuple(getattr(self, n) for n in names) == tuple(getattr(other, n) for n in names)

    __hash__ = None  # type: ignore[assignment]  # set per class for frozen models

    def __replace__(self, **changes: Any) -> typing.Self:
        """``copy.replace(obj, **changes)``: a new instance, checked by the constructor."""
        info = type(self).__aiogram_info__
        for name in changes:
            if name in info.names and name not in info.init:
                msg = f"field {name!r} is declared with init=False, it cannot be replaced"
                raise ValueError(msg)
        kwargs = {name: getattr(self, name) for name in info.init if name not in changes}
        kwargs.update(changes)
        return type(self)(**kwargs)

    def __getstate__(self) -> dict[str, Any]:
        state = {name: getattr(self, name) for name in type(self).__aiogram_info__.names}
        state["__fields_set__"] = fields_set(self)
        return state

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        for name, value in state.items():
            object.__setattr__(self, name, value)


def fields_set(obj: ModelBase) -> frozenset[str]:
    """The fields given explicitly (constructor arguments, keys present on load): D115
    ``exclude_unset``."""
    value: frozenset[str] = obj.__fields_set__  # type: ignore[attr-defined]
    return value


# ---------------------------------------------------------------------------------------------
# Facades
# ---------------------------------------------------------------------------------------------


def _model_core(tp: type) -> _core.ModelCore:
    core = vars(tp).get("__aiogram_core__") if isinstance(tp, type) else None
    if core is not None:
        return core  # type: ignore[no-any-return]
    if not (isinstance(tp, type) and _is_foreign(tp)):
        msg = f"{_name(tp)} is not a model, dataclass, NamedTuple or TypedDict"
        raise TypeError(msg)
    return _Compiler(tp, {}).foreign(tp)


def _cached(tp: type, attribute: str, build: Callable[[_core.ModelCore], Any]) -> Any:
    schema = vars(tp).get(attribute) if isinstance(tp, type) else None
    if schema is None:
        schema = build(_model_core(tp))
        with contextlib.suppress(TypeError, AttributeError):
            setattr(tp, attribute, schema)  # the schema lives on the class
    return schema


def json_schema(tp: type[_T]) -> _core.JsonSchema[_T]:
    """The JSON codec of a ``ModelBase`` class, dataclass, NamedTuple or TypedDict (compiled
    once, stored on the class)."""
    schema: _core.JsonSchema[_T] = _cached(tp, "__aiogram_json__", _core.JsonSchema)
    return schema


def flat_schema(tp: type[_T]) -> _core.FlatSchema[_T]:
    """The positional flat-string codec (callback data); ``TypeError`` for a field without a
    flat form, or with a ``Key`` / ``rename``."""
    schema: _core.FlatSchema[_T] = _cached(tp, "__aiogram_flat__", _core.FlatSchema)
    return schema


def json_codec(
    annotation: Any, *, converters: Mapping[type, Converter] | None = None
) -> _core.JsonCodec:
    """The JSON (and flat) codec of any annotation: ``json_codec(list[int]).load([1])``."""
    compiler = _Compiler(annotation, converters or {})
    return _core.JsonCodec(compiler.kind(annotation, _Scope({}, {})))
