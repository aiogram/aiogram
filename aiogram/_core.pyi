# Hand-written stub for the native extension (crates/aiogram-core), checked against the
# built module by `make stubtest` (PD-36, as pydantic-core does).
#
# The converter classes below are the whole Python -> Rust interface of the converter core
# (aiogram/utils/_converters.py builds them; F-08 plan-10): Rust never reads Python attributes
# of the resolver's objects by name.
from collections.abc import Callable, Mapping, Sequence
from types import GenericAlias
from typing import Any, Generic, Literal, Self, TypedDict, TypeVar, final, type_check_only

__all__ = [
    "__version__",
    "Field",
    "FlatSchema",
    "JsonCodec",
    "JsonSchema",
    "Kind",
    "KindCell",
    "ModelCore",
    "build_info",
    "converters_init",
]

_T = TypeVar("_T")

__version__: str

@type_check_only
class BuildInfo(TypedDict):
    version: str
    pyo3_version: str
    profile: str
    lto: str
    target: str

def build_info() -> BuildInfo: ...
def converters_init(
    error: type[ValueError], detail: type[tuple[Any, ...]], missing: object
) -> None:
    """Hand the converter core ``ConversionError``, ``ErrorDetail`` and ``MISSING``.

    ``aiogram.utils._converters`` calls it once at import; the schemas raise ``RuntimeError``
    before it.
    """

@final
class Kind:
    """One compiled annotation (immutable). Built only through the static constructors."""

    @property
    def label(self) -> str:
        """The type name used in messages: ``int``, ``list``, ``Address``, ``int | None``."""

    @property
    def flat(self) -> bool:
        """Whether the kind has a flat-string form (callback data)."""

    @staticmethod
    def str_() -> Kind: ...
    @staticmethod
    def int_() -> Kind: ...
    @staticmethod
    def float_() -> Kind: ...
    @staticmethod
    def bool_() -> Kind: ...
    @staticmethod
    def uuid(*, hex: bool = False) -> Kind:
        """JSON: canonical text, or 32 hex digits with ``hex``; flat: always hex."""

    @staticmethod
    def datetime(
        *,
        timespec: Literal[
            "auto", "hours", "minutes", "seconds", "milliseconds", "microseconds"
        ] = "auto",
        sep: str = "T",
        epoch: Literal["s", "ms"] | None = None,
    ) -> Kind:
        """ISO 8601 text (``isoformat(sep, timespec)``), or a number with ``epoch``."""

    @staticmethod
    def date() -> Kind: ...
    @staticmethod
    def time(
        *,
        timespec: Literal[
            "auto", "hours", "minutes", "seconds", "milliseconds", "microseconds"
        ] = "auto",
    ) -> Kind: ...
    @staticmethod
    def timedelta() -> Kind:
        """A number of seconds (``total_seconds()``), in both codecs."""

    @staticmethod
    def decimal(*, number: bool = False) -> Kind:
        """Text, or a JSON number with ``number`` (exact on the bytes paths, a float on dicts)."""

    @staticmethod
    def bytes_() -> Kind:
        """Padded base64 in JSON, unpadded base64url in the flat form."""

    @staticmethod
    def text(
        tp: type, parse: Callable[[str], Any], format: Callable[[Any], str], *, flat: bool
    ) -> Kind:
        """A value stored as text through Python callables (``Fraction``)."""

    @staticmethod
    def enum(tp: type, *, by_name: bool = False, missing: bool = False) -> Kind:
        """An ``Enum`` by value (a ``(type, value)`` match) or by name.

        ``missing``: call ``_missing_`` on a miss.
        """

    @staticmethod
    def literal(values: Sequence[object]) -> Kind: ...
    @staticmethod
    def optional(inner: Kind) -> Kind: ...
    @staticmethod
    def sequence(item: Kind, container: type) -> Kind:
        """``list`` / ``tuple`` (``tuple[T, ...]``) / ``set`` / ``frozenset``: a JSON array."""

    @staticmethod
    def tuple_(items: Sequence[Kind]) -> Kind:
        """A fixed-length ``tuple[A, B]``: a JSON array of exactly that many items."""

    @staticmethod
    def dict_(value: Kind) -> Kind:
        """``dict[str, T]``."""

    @staticmethod
    def model(core: ModelCore) -> Kind:
        """A model, dataclass, NamedTuple or TypedDict; its fields may be set later."""

    @staticmethod
    def union(
        members: Sequence[Kind], *, nullable: bool, discriminator: str | None = None
    ) -> Kind:
        """Smart union (exact type first, then left to right), or tagged by a ``Literal`` field."""

    @staticmethod
    def python(converter: object, *, flat: bool) -> Kind:
        """A user converter: Rust calls its ``to_json`` / ``from_json`` (and ``to_str`` /
        ``from_str`` when ``flat``)."""

    @staticmethod
    def lazy(cell: KindCell, label: str) -> Kind:
        """A reference to a kind set later (a recursive ``type X = ...`` alias)."""

@final
class KindCell:
    def __new__(cls) -> Self: ...
    def set(self, kind: Kind) -> None:
        """Set once; ``RuntimeError`` on a second call."""

@final
class Field:
    """One field: attribute ``name``, stored ``key``, fallback ``load`` keys, kind, default."""

    def __new__(
        cls,
        name: str,
        kind: Kind,
        *,
        key: str | None = None,
        load: Sequence[str] = ...,
        default: object = None,
        has_default: bool = False,
        factory: Callable[[], Any] | None = None,
        init: bool = True,
        kw_only: bool = True,
        required: bool = True,
        keyed: bool = False,
    ) -> Self: ...
    @property
    def name(self) -> str: ...
    @property
    def key(self) -> str: ...
    @property
    def load(self) -> tuple[str, ...]: ...
    @property
    def kind(self) -> Kind: ...

@final
class ModelCore:
    """The field table and builder of one class.

    ``build``: ``"model"`` (a ``ModelBase`` class: ``object.__new__`` + generic setattr, the
    ``__fields_set__`` record, ``__post_init__``), ``"call"`` (a dataclass / NamedTuple:
    ``cls(**values)``) or ``"dict"`` (a TypedDict: a plain dict of the keys present).
    ``resolve`` is called when the fields are needed before :meth:`set_fields`.
    """

    def __new__(
        cls,
        tp: type,
        *,
        build: Literal["model", "call", "dict"],
        post_init: bool = False,
        resolve: Callable[[], None] | None = None,
    ) -> Self: ...
    @property
    def tp(self) -> type: ...
    @property
    def ready(self) -> bool: ...
    def set_fields(self, fields: Sequence[Field]) -> None:
        """Set once; ``RuntimeError`` on a second call."""

    def init(self, instance: object, args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> None:
        """``__init__`` of a ``"model"`` class: check the values strictly, fill defaults, set the
        attributes and ``__fields_set__``, run ``__post_init__``. ``TypeError`` for missing or
        unexpected arguments, ``ConversionError`` for values."""

@final
class JsonSchema(Generic[_T]):
    def __new__(cls, core: ModelCore) -> Self: ...
    @classmethod
    def __class_getitem__(cls, key: Any) -> GenericAlias: ...
    @property
    def core(self) -> ModelCore: ...
    @property
    def keys(self) -> dict[str, tuple[str, tuple[str, ...]]]:
        """Attribute name -> (stored key, fallback load keys)."""

    def load(self, data: Mapping[str, Any]) -> _T: ...
    def load_json(self, data: bytes | bytearray | str) -> _T: ...
    def dump(self, obj: _T, *, exclude_unset: bool = False) -> dict[str, Any]: ...
    def dump_json(self, obj: _T, *, exclude_unset: bool = False) -> bytes: ...
    def dump_fields(self, values: Mapping[str, Any]) -> dict[str, Any]:
        """Check and dump some fields (a typed patch): attribute names in, stored keys out."""

@final
class FlatSchema(Generic[_T]):
    """Positional flat-string codec (callback data). ``TypeError`` for a field without a flat
    form or with an explicit key, when the fields are known."""

    def __new__(cls, core: ModelCore) -> Self: ...
    @classmethod
    def __class_getitem__(cls, key: Any) -> GenericAlias: ...
    @property
    def core(self) -> ModelCore: ...
    def load(self, parts: Sequence[str]) -> _T: ...
    def dump(self, obj: _T) -> list[str]: ...

@final
class JsonCodec:
    """The JSON codec of any kind (a field annotation): ``json_codec(list[int])``."""

    def __new__(cls, kind: Kind) -> Self: ...
    @property
    def kind(self) -> Kind: ...
    def load(self, value: Any) -> Any: ...
    def load_json(self, data: bytes | bytearray | str) -> Any: ...
    def dump(self, value: Any) -> Any: ...
    def dump_json(self, value: Any) -> bytes: ...
    def load_flat(self, text: str) -> Any:
        """The flat-string form; ``TypeError`` when the kind has none."""

    def dump_flat(self, value: Any) -> str: ...
