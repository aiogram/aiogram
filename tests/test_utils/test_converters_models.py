"""Converter-core contract suite (F-08 plan-10): ``ModelBase``, keys, converter lookup, forward
references, the flat schema, imports, GC and threads.

This module uses ``from __future__ import annotations``, as ``FSMData`` / ``CallbackData`` users
will; the eager (PEP 649) cases run through :func:`module_from_source`.
"""

from __future__ import annotations

import copy
import dataclasses
import enum
import gc
import json
import pickle
import subprocess
import sys
import textwrap
import threading
import types
import typing
import weakref
from collections.abc import Iterator
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any, ClassVar, Literal, NamedTuple, NotRequired, Required, TypedDict
from uuid import UUID

import pytest

from aiogram.utils import _converters
from aiogram.utils._converters import ModelBase, fields_set, flat_schema, json_codec, json_schema
from aiogram.utils.converters import (
    MISSING,
    ConversionError,
    Converter,
    Discriminator,
    EnumByName,
    EpochDatetime,
    IsoDatetime,
    Key,
    field,
)

UTC = timezone.utc
UID = UUID("12345678-1234-5678-1234-567812345678")
EPOCH_2 = datetime(1970, 1, 1, 0, 0, 2, tzinfo=UTC)


def errors_of(call: Any, *args: Any, **kwargs: Any) -> list[tuple[Any, ...]]:
    with pytest.raises(ConversionError) as exc_info:
        call(*args, **kwargs)
    return [tuple(error) for error in exc_info.value.errors]


@pytest.fixture
def module_from_source() -> Iterator[Any]:
    """Run source text as a real module (its own globals, no ``__future__`` unless written)."""
    created: list[str] = []

    def make(source: str, name: str = "") -> types.ModuleType:
        name = name or f"_converters_case_{len(created)}"
        module = types.ModuleType(name)
        sys.modules[name] = module
        created.append(name)
        # dont_inherit: this module's `from __future__ import annotations` must not leak in
        code = compile(textwrap.dedent(source), f"<{name}>", "exec", dont_inherit=True)
        exec(code, module.__dict__)  # noqa: S102
        return module

    yield make
    for name in created:
        sys.modules.pop(name, None)


class Kind(enum.Enum):
    A = "a"
    B = "b"


class Address(ModelBase):
    city: str
    zip: int | None = None


class Form(ModelBase):
    item_id: int
    qty: int = 1
    address: Address | None = None
    tags: list[str] = []  # noqa: RUF012
    meta: dict[str, int] = field(default_factory=dict)
    created: datetime | None = None


class Node(ModelBase):
    value: int
    children: list[Node] = []  # noqa: RUF012


class Forward(ModelBase):  # refers to a class defined below: compiled on first use
    later: Later | None = None


class Later(ModelBase):
    back: Forward | None = None


class TestDeclaration:
    def test_fields_in_order(self):
        assert list(json_schema(Form).keys) == [
            "item_id",
            "qty",
            "address",
            "tags",
            "meta",
            "created",
        ]

    def test_private_names_are_fields_and_classvar_is_skipped(self):
        class Skips(ModelBase):
            LIMIT: ClassVar[int] = 3
            OTHER: ClassVar = 4
            _private: int = 0
            value: int = 0

        assert list(json_schema(Skips).keys) == ["_private", "value"]
        obj = Skips(_private=1)
        assert json_schema(Skips).dump(obj) == {"_private": 1, "value": 0}
        assert Skips.LIMIT == 3

    def test_classvar_without_future(self, module_from_source):
        module = module_from_source(
            """
            import typing
            from typing import ClassVar
            from aiogram.utils._converters import ModelBase

            class Plain(ModelBase):
                LIMIT: ClassVar[int] = 3
                OTHER: typing.ClassVar[str] = "x"
                value: int = 0
            """
        )
        assert list(json_schema(module.Plain).keys) == ["value"]

    @pytest.mark.parametrize(
        ("body", "message"),
        [
            ("_: dataclasses.KW_ONLY", "KW_ONLY is not needed"),
            ("_: KW_ONLY", "KW_ONLY is not needed"),
            ("seed: dataclasses.InitVar[int] = 0", r"\.seed: InitVar is not supported"),
            ("seed: InitVar[int] = 0", r"\.seed: InitVar is not supported"),
        ],
    )
    @pytest.mark.parametrize("future", [True, False], ids=["future", "eager"])
    def test_kw_only_and_initvar_rejected(self, module_from_source, body, message, future):
        source = (
            ("from __future__ import annotations\n" if future else "")
            + "import dataclasses\n"
            + "from dataclasses import KW_ONLY, InitVar\n"
            + "from aiogram.utils._converters import ModelBase\n"
            + f"class Bad(ModelBase):\n    a: int = 0\n    {body}\n"
        )
        with pytest.raises(TypeError, match=message):
            module_from_source(source)

    def test_field_options(self):
        class Options(ModelBase):
            a: int = field(kw_only=False)
            b: list[int] = field(default_factory=list, repr=False)
            c: int = field(default=0, compare=False)
            d: dict[str, int] = field(init=False, default_factory=dict)
            e: int = field(default=5, init=False)

        obj = Options(1)
        assert (obj.a, obj.b, obj.c, obj.d, obj.e) == (1, [], 0, {}, 5)
        assert repr(obj) == f"{Options.__qualname__}(a=1, c=0, d={{}}, e=5)"
        assert obj == Options(1, c=9)
        assert obj != Options(2)
        assert Options.c == 0  # the class attribute is the plain default
        assert Options.e == 5
        assert "b" not in vars(Options)  # a factory leaves no class attribute
        with pytest.raises(TypeError, match="unexpected keyword argument 'd'"):
            Options(1, d={})
        # init=False fields are still loaded and dumped
        loaded = json_schema(Options).load({"a": 1, "d": {"k": 1}, "e": 7})
        assert (loaded.d, loaded.e) == ({"k": 1}, 7)
        assert json_schema(Options).dump(obj) == {"a": 1, "b": [], "c": 0, "d": {}, "e": 5}

    def test_dataclasses_field(self):
        class Std(ModelBase):
            a: int = dataclasses.field(kw_only=False)
            b: list[int] = dataclasses.field(default_factory=list, repr=False)
            c: int = dataclasses.field(default=1, compare=False, hash=True, metadata={"x": 1})
            d: int = dataclasses.field(default=2, init=False)

        obj = Std(1)
        assert (obj.a, obj.b, obj.c, obj.d) == (1, [], 1, 2)
        assert repr(obj) == f"{Std.__qualname__}(a=1, c=1, d=2)"
        assert obj == Std(1, c=5)
        with pytest.raises(TypeError, match="unexpected keyword argument 'd'"):
            Std(1, d=3)

    def test_field_errors(self):
        with pytest.raises(ValueError, match="cannot specify both default and default_factory"):
            field(default=1, default_factory=list)
        with pytest.raises(TypeError, match="takes a sequence of keys, not a str"):
            field(load="old")
        with pytest.raises(TypeError, match="takes a sequence of keys, not a str"):
            Key("a", load="old")  # type: ignore[arg-type]
        assert Key("a", load=["b"]).load == ("b",)

    def test_init_false_needs_a_default(self):
        with pytest.raises(TypeError, match=r"Bad\.a: init=False needs a default"):

            class Bad(ModelBase):
                a: int = field(init=False)

    def test_positional_order(self):
        with pytest.raises(TypeError, match="positional field 'b' without a default follows 'a'"):

            class Bad(ModelBase):
                a: int = field(default=1, kw_only=False)
                b: int = field(kw_only=False)

        class Fine(ModelBase):  # a keyword-only field may follow a positional one with a default
            a: int = field(default=1, kw_only=False)
            b: int
            c: int = field(default_factory=int, kw_only=False)

        assert (Fine(b=2).a, Fine(5, 6, b=2).c) == (1, 6)

    def test_inherited_fields_first_and_redeclared_keeps_position(self):
        class Parent(ModelBase):
            a: int
            b: int = 1

        class Child(Parent):
            c: int = 2
            a: str = "x"  # type: ignore[assignment]

        assert list(json_schema(Child).keys) == ["a", "b", "c"]
        assert Child().a == "x"
        assert json_schema(Child).dump(Child(a="y")) == {"a": "y", "b": 1, "c": 2}
        with pytest.raises(ConversionError):
            Child(a=1)

    def test_a_base_method_never_becomes_a_default(self):
        class Base(ModelBase):
            def value(self) -> int:
                return 1

        class Child(Base):
            value: int  # type: ignore[assignment]

        with pytest.raises(TypeError, match="missing 1 required keyword-only argument: 'value'"):
            Child()
        assert Child(value=2).value == 2
        assert errors_of(json_schema(Child).load, {}) == [(("value",), "field required", MISSING)]

    def test_converters_keys_must_be_types(self):
        with pytest.raises(TypeError, match="converters= keys must be types"):

            class Bad(ModelBase, converters={"datetime": EpochDatetime()}):  # type: ignore[dict-item]
                a: int

    def test_unknown_class_keyword(self):
        with pytest.raises(TypeError):

            class Bad(ModelBase, nope=1):  # type: ignore[call-arg]
                a: int

    def test_bad_field_names_class_and_field(self):
        with pytest.raises(TypeError, match=r"Bad\.value: unsupported annotation complex"):

            class Bad(ModelBase):
                ok: int
                value: complex

        with pytest.raises(TypeError, match=r"Keys\.value: dict keys must be str, not int"):

            class Keys(ModelBase):
                value: dict[int, str]

    def test_unevaluable_annotation(self, module_from_source):
        with pytest.raises(TypeError, match=r"cannot evaluate annotation 'int\['"):
            module_from_source(
                """
                from aiogram.utils._converters import ModelBase

                class Bad(ModelBase):
                    a: "int["
                """
            )

    def test_class_inside_a_class_body(self):
        class Outer:
            class Inner(ModelBase):
                a: Kind
                b: list[Kind] = []  # noqa: RUF012

        assert json_schema(Outer.Inner).load({"a": "a"}).a is Kind.A


class TestConstructor:
    def test_defaults_and_fields_set(self):
        form = Form(item_id=5)
        assert (form.qty, form.tags, form.meta, form.address) == (1, [], {}, None)
        assert fields_set(form) == {"item_id"}
        assert fields_set(Form(item_id=5, qty=1)) == {"item_id", "qty"}

    def test_validates(self):
        with pytest.raises(ConversionError) as exc_info:
            Form(item_id="x", tags=["a", 1], address=Address(city="c", zip=None), meta={"k": "v"})
        assert str(exc_info.value) == (
            "3 errors constructing Form\n"
            "  item_id: expected int, got 'x'\n"
            "  tags[1]: expected str, got 1\n"
            "  meta.k: expected int, got 'v'"
        )

    def test_defaults_are_not_checked(self):
        class Loose(ModelBase):
            a: int = "x"  # type: ignore[assignment]

        assert Loose().a == "x"

    def test_nested_instances_are_checked(self):
        address = Address(city="c")
        object.__setattr__(address, "zip", "bad")
        assert errors_of(Form, item_id=1, address=address) == [
            (("address", "zip"), "expected int", "bad")
        ]

    @pytest.mark.parametrize(
        ("args", "kwargs", "message"),
        [
            ((1,), {}, r"Form\.__init__\(\) takes 1 positional argument but 2 were given"),
            ((), {}, r"missing 1 required keyword-only argument: 'item_id'"),
            ((), {"item_id": 1, "nope": 2}, "got an unexpected keyword argument 'nope'"),
        ],
    )
    def test_argument_errors(self, args, kwargs, message):
        with pytest.raises(TypeError, match=message):
            Form(*args, **kwargs)

    def test_argument_errors_positional(self):
        class Two(ModelBase):
            a: int = field(kw_only=False)
            b: int = field(kw_only=False)
            c: int
            d: int

        with pytest.raises(TypeError, match=r"takes 3 positional arguments but 4 were given"):
            Two(1, 2, 3)
        with pytest.raises(TypeError, match="got multiple values for argument 'a'"):
            Two(1, 2, a=1, c=1, d=1)
        with pytest.raises(
            TypeError, match="missing 2 required keyword-only arguments: 'c' and 'd'"
        ):
            Two(1, 2)
        with pytest.raises(TypeError, match="missing 1 required positional argument: 'b'"):
            Two(1, c=1, d=1)

    def test_mutable_defaults_are_copied(self):
        first, second = Form(item_id=1), Form(item_id=2)
        first.tags.append("x")
        first.meta["k"] = 1
        assert (second.tags, second.meta) == ([], {})
        loaded = json_schema(Form).load({"item_id": 3})
        assert loaded.tags == []
        assert loaded.tags is not json_schema(Form).load({"item_id": 3}).tags

    def test_immutable_default_is_shared(self):
        shared = Decimal("1.5")

        class Price(ModelBase):
            value: Decimal = shared

        assert Price().value is shared
        assert json_schema(Price).load({}).value is shared

    def test_post_init(self):
        calls = []

        class Checked(ModelBase):
            a: int

            def __post_init__(self) -> None:
                calls.append(self.a)
                if self.a < 0:
                    msg = "a must be >= 0"
                    raise ValueError(msg)
                if self.a == 13:
                    raise KeyError(self.a)

        Checked(a=1)
        json_schema(Checked).load({"a": 2})
        json_schema(Checked).load_json(b'{"a": 3}')
        assert calls == [1, 2, 3]
        with pytest.raises(ValueError, match="a must be >= 0") as exc_info:
            Checked(a=-1)  # the constructor lets it propagate unchanged
        assert type(exc_info.value) is ValueError
        with pytest.raises(KeyError):
            Checked(a=13)
        for call, arg in [
            (json_schema(Checked).load, {"a": -1}),
            (json_schema(Checked).load_json, b'{"a": -1}'),
        ]:
            with pytest.raises(ConversionError) as error_info:
                call(arg)
            assert [tuple(e) for e in error_info.value.errors] == [
                ((), "a must be >= 0", {"a": -1})
            ]
            assert isinstance(error_info.value.__cause__, ValueError)
        with pytest.raises(KeyError):
            json_schema(Checked).load({"a": 13})

    def test_post_init_error_of_a_nested_model_is_at_its_path(self):
        class Inner(ModelBase):
            a: int

            def __post_init__(self) -> None:
                msg = "never valid"
                raise ValueError(msg)

        class Outer(ModelBase):
            items: list[Inner]

        assert errors_of(json_schema(Outer).load, {"items": [{"a": 1}]}) == [
            (("items", 0), "never valid", {"a": 1})
        ]

    def test_post_init_on_flat_load(self):
        class Item(ModelBase):
            id: int

            def __post_init__(self) -> None:
                if self.id < 0:
                    msg = "negative"
                    raise ValueError(msg)

        assert flat_schema(Item).load(["1"]).id == 1
        assert errors_of(flat_schema(Item).load, ["-1"])[0][1] == "negative"


class TestDunders:
    def test_eq_and_repr(self):
        assert Address(city="a") == Address(city="a")
        assert Address(city="a") != Address(city="b")
        assert Address(city="a") != "a"
        assert Address.__eq__(Address(city="a"), Form(item_id=1)) is NotImplemented
        assert repr(Address(city="a")) == "Address(city='a', zip=None)"
        with pytest.raises(TypeError, match="unhashable"):
            hash(Address(city="a"))

    def test_recursive_repr(self):
        node = Node(value=1)
        node.children.append(node)
        assert repr(node) == "Node(value=1, children=[...])"

    def test_repr_of_a_partly_set_instance(self):
        empty = Address.__new__(Address)
        assert repr(empty) == f"Address(city={MISSING!r}, zip=None)"  # zip: the class default

    def test_frozen(self):
        class Point(ModelBase, frozen=True):
            x: int
            y: int = 0
            tags: list[str] = field(default_factory=list, compare=False)

        point = Point(x=1)
        with pytest.raises(dataclasses.FrozenInstanceError, match="cannot assign to field 'x'"):
            point.x = 2  # type: ignore[misc]
        with pytest.raises(dataclasses.FrozenInstanceError, match="cannot delete field 'x'"):
            del point.x
        assert hash(point) == hash(Point(x=1, tags=["a"]))
        assert {point, Point(x=1)} == {point}
        loaded = json_schema(Point).load({"x": 1})  # loading bypasses the frozen __setattr__
        assert loaded == point
        assert fields_set(loaded) == {"x"}

    def test_frozen_inheritance(self):
        class Frozen(ModelBase, frozen=True):
            a: int

        class Child(Frozen):  # inherits frozen
            b: int = 0

        with pytest.raises(dataclasses.FrozenInstanceError):
            Child(a=1).b = 2  # type: ignore[misc]
        with pytest.raises(TypeError, match="cannot inherit a non-frozen model from a frozen one"):

            class Thawed(Frozen, frozen=False):
                pass

        with pytest.raises(TypeError, match="cannot inherit a frozen model from a non-frozen one"):

            class Iced(Address, frozen=True):
                pass

        class Same(Frozen, frozen=True):
            pass

        assert hash(Same(a=1)) == hash(Frozen(a=1))

    def test_frozen_keeps_user_dunders(self):
        class Own(ModelBase, frozen=True):
            a: int

            def __setattr__(self, name: str, value: Any) -> None:
                object.__setattr__(self, name, value * 2)

            def __delattr__(self, name: str) -> None:
                object.__setattr__(self, name, 0)

            def __hash__(self) -> int:
                return 7

        obj = Own(a=1)
        obj.a = 2
        del obj.a
        assert (obj.a, hash(obj)) == (0, 7)

        class OwnEq(ModelBase, frozen=True):  # noqa: PLW1641
            a: int

            def __eq__(self, other: object) -> bool:
                return True

        # as dataclasses: the None that an own __eq__ implies is not an explicit __hash__
        assert OwnEq.__hash__ is _converters._frozen_hash

        class ExplicitNone(ModelBase, frozen=True):
            a: int
            __hash__ = None  # type: ignore[assignment]

        # an explicit `__hash__ = None` is kept, as dataclasses
        assert ExplicitNone.__hash__ is None

    def test_replace(self):
        class Options(ModelBase, frozen=True):
            a: int
            b: int = 0
            hidden: int = field(default=1, init=False)

        obj = Options(a=1)
        changed = obj.__replace__(b=2)
        assert (changed.a, changed.b) == (1, 2)
        assert fields_set(changed) == {"a", "b"}
        with pytest.raises(ValueError, match="'hidden' is declared with init=False"):
            obj.__replace__(hidden=2)
        with pytest.raises(TypeError, match="unexpected keyword argument 'nope'"):
            obj.__replace__(nope=2)
        with pytest.raises(ConversionError):
            obj.__replace__(a="x")
        if sys.version_info >= (3, 13):
            assert copy.replace(obj, a=5).a == 5

    @pytest.mark.parametrize(
        "options", [{}, {"frozen": True}, {"slots": True}, {"frozen": True, "slots": True}]
    )
    def test_pickle_and_copy(self, options):
        namespace: dict[str, Any] = {}
        exec(  # noqa: S102  (pickle needs a module-level class: registered below)
            "from aiogram.utils._converters import ModelBase\n"
            "class Picklable(ModelBase, **options):\n"
            "    a: int\n"
            "    tags: list[str] = []\n",
            {"ModelBase": ModelBase, "options": options, "__name__": __name__},
            namespace,
        )
        cls = namespace["Picklable"]
        cls.__qualname__ = cls.__name__ = f"Picklable{len(options)}{'frozen' in options}"
        setattr(sys.modules[__name__], cls.__name__, cls)
        try:
            obj = cls(a=1, tags=["x"])
            for clone in (pickle.loads(pickle.dumps(obj)), copy.copy(obj), copy.deepcopy(obj)):
                assert clone == obj
                assert fields_set(clone) == {"a", "tags"}
            assert copy.deepcopy(obj).tags is not obj.tags
            assert copy.copy(obj).tags is obj.tags
        finally:
            delattr(sys.modules[__name__], cls.__name__)


class TestSlots:
    def test_slots_with_defaults(self):
        class Slotted(ModelBase, slots=True):
            LIMIT: ClassVar[int] = 3
            a: int = 1
            tags: list[str] = []  # noqa: RUF012
            b: str = field(default="x", key="bee")

        obj = Slotted()
        assert not hasattr(obj, "__dict__")
        assert Slotted.__slots__ == ("a", "tags", "b")
        assert (obj.a, obj.tags, obj.b, Slotted.LIMIT) == (1, [], "x", 3)
        assert obj.tags is not Slotted().tags
        with pytest.raises(AttributeError):
            obj.other = 1  # type: ignore[attr-defined]
        assert json_schema(Slotted).dump(obj) == {"a": 1, "tags": [], "bee": "x"}
        assert json_schema(Slotted).load({"a": 2}).a == 2

    def test_slots_without_annotations(self):
        class Empty(ModelBase, slots=True):
            pass

        assert Empty.__slots__ == ()
        assert json_schema(Empty).dump(Empty()) == {}

    def test_slots_eager(self, module_from_source):
        module = module_from_source(
            """
            from typing import ClassVar
            from aiogram.utils._converters import ModelBase

            class Slotted(ModelBase, slots=True, frozen=True):
                LIMIT: ClassVar[int] = 3
                a: int = 1

            class Empty(ModelBase, slots=True):
                pass
            """
        )
        assert module.Slotted.__slots__ == ("a",)
        assert not hasattr(module.Slotted(), "__dict__")
        assert module.Empty.__slots__ == ()

    def test_user_slots(self):
        class Own(ModelBase):
            __slots__ = ("a", "b")
            a: int
            b: int

        obj = Own(a=1, b=2)
        assert not hasattr(obj, "__dict__")
        assert json_schema(Own).load({"a": 1, "b": 2}) == obj
        with pytest.raises(TypeError, match="missing 2 required"):
            Own()

    def test_slots_and_dunder_slots_rejected(self):
        with pytest.raises(TypeError, match="slots=True and __slots__ cannot be combined"):

            class Both(ModelBase, slots=True):
                __slots__ = ("a",)
                a: int

    def test_frozen_slots(self):
        class Point(ModelBase, frozen=True, slots=True):
            x: int
            y: int = 0

        point = json_schema(Point).load({"x": 1})
        with pytest.raises(dataclasses.FrozenInstanceError):
            point.x = 2  # type: ignore[misc]
        assert hash(point) == hash(Point(x=1))
        assert copy.deepcopy(point) == point

    def test_dataclass_slots_as_field_types(self):
        @dataclasses.dataclass(slots=True)
        class Slotted:
            a: int

        @dataclasses.dataclass(frozen=True, slots=True)
        class FrozenSlotted:
            a: int
            b: tuple[int, ...] = ()

        class Holder(ModelBase):
            s: Slotted
            f: set[FrozenSlotted]

        holder = json_schema(Holder).load({"s": {"a": 1}, "f": [{"a": 2, "b": [3]}]})
        assert holder.s == Slotted(1)
        assert holder.f == {FrozenSlotted(2, (3,))}
        assert json_schema(Holder).dump(holder) == {"s": {"a": 1}, "f": [{"a": 2, "b": [3]}]}


class TestLoadDump:
    DATA: ClassVar[dict[str, Any]] = {
        "item_id": 5,
        "qty": 2,
        "address": {"city": "Kyiv", "zip": 1001},
        "tags": ["a", "b"],
        "meta": {"k": 1},
        "created": "2024-05-06T07:08:09+00:00",
    }

    def test_round_trip(self):
        schema = json_schema(Form)
        form = schema.load(self.DATA)
        assert isinstance(form.address, Address)
        assert form.created == datetime(2024, 5, 6, 7, 8, 9, tzinfo=UTC)
        assert schema.dump(form) == self.DATA
        assert schema.dump_json(form) == json.dumps(self.DATA, separators=(",", ":")).encode()
        assert schema.load_json(schema.dump_json(form)) == form
        assert fields_set(form) == set(self.DATA)
        assert fields_set(form.address) == {"city", "zip"}

    def test_schema_is_cached_on_the_class(self):
        assert json_schema(Form) is json_schema(Form)
        assert vars(Form)["__aiogram_json__"] is json_schema(Form)
        assert json_schema(Form).core is Form.__aiogram_core__

        class Child(Form):
            pass

        assert json_schema(Child) is not json_schema(Form)

    def test_unknown_keys_ignored(self):
        form = json_schema(Form).load({"item_id": 1, "extra": 0})
        assert not hasattr(form, "extra")

    @pytest.mark.parametrize(
        ("data", "errors"),
        [
            ({"item_id": "5"}, [(("item_id",), "expected int", "5")]),
            (
                {"item_id": 5, "address": {"city": "x", "zip": "abc"}},
                [(("address", "zip"), "expected int", "abc")],
            ),
            ({"item_id": 5, "address": {}}, [(("address", "city"), "field required", MISSING)]),
            ({"item_id": 5, "tags": ["a", "b", 3]}, [(("tags", 2), "expected str", 3)]),
            ({"item_id": 5, "meta": {"k": "v"}}, [(("meta", "k"), "expected int", "v")]),
            ({}, [(("item_id",), "field required", MISSING)]),
            ([1], [((), "expected Form", [1])]),
            (
                {"qty": "x", "tags": "y"},
                [
                    (("item_id",), "field required", MISSING),
                    (("qty",), "expected int", "x"),
                    (("tags",), "expected list", "y"),
                ],
            ),
        ],
    )
    def test_load_errors(self, data, errors):
        assert errors_of(json_schema(Form).load, data) == errors
        assert errors_of(json_schema(Form).load_json, json.dumps(data)) == errors

    def test_recursive_error_path(self):
        data = {"value": 1, "children": [{"value": 2}, {"value": "x"}]}
        with pytest.raises(ConversionError) as exc_info:
            json_schema(Node).load(data)
        assert str(exc_info.value) == (
            "1 error loading Node\n  children[1].value: expected int, got 'x'"
        )

    def test_dump_errors(self):
        form = Form(item_id=1, address=Address(city="c"))
        object.__setattr__(form.address, "city", 1)
        object.__setattr__(form, "tags", ["a", 2])
        expected = [(("address", "city"), "expected str", 1), (("tags", 1), "expected str", 2)]
        assert errors_of(json_schema(Form).dump, form) == expected
        assert errors_of(json_schema(Form).dump_json, form) == expected
        assert errors_of(json_schema(Form).dump, Address(city="x")) == [
            ((), "expected Form", Address(city="x"))
        ]

    def test_dump_accepts_a_subclass_instance(self):
        class Child(Address):
            extra: int = 0

        assert json_schema(Address).dump(Child(city="a")) == {"city": "a", "zip": None}

    def test_exclude_unset(self):
        schema = json_schema(Form)
        assert schema.dump(Form(item_id=5, qty=1), exclude_unset=True) == {"item_id": 5, "qty": 1}
        loaded = schema.load({"item_id": 5, "address": {"city": "c"}})
        # top level only: the nested model is dumped whole
        expected = {"item_id": 5, "address": {"city": "c", "zip": None}}
        assert schema.dump(loaded, exclude_unset=True) == expected
        assert (
            schema.dump_json(loaded, exclude_unset=True)
            == json.dumps(expected, separators=(",", ":")).encode()
        )
        assert len(schema.dump(loaded)) == 6

    def test_exclude_unset_without_fields_set(self):
        bare = Address.__new__(Address)
        object.__setattr__(bare, "city", "c")
        object.__setattr__(bare, "zip", None)
        assert json_schema(Address).dump(bare, exclude_unset=True) == {"city": "c", "zip": None}

    def test_dump_fields(self):
        class Patch(ModelBase, rename="camel"):
            item_id: int
            note: Annotated[str, Key("n")] = ""
            when: datetime | None = None

        schema = json_schema(Patch)
        assert schema.dump_fields({"item_id": 1, "note": "x"}) == {"itemId": 1, "n": "x"}
        assert schema.dump_fields(types.MappingProxyType({"when": None})) == {"when": None}
        with pytest.raises(TypeError, match=r"Patch has no field 'itemId'"):
            schema.dump_fields({"itemId": 1})
        assert errors_of(schema.dump_fields, {"item_id": "a", "note": 1}) == [
            (("itemId",), "expected int", "a"),
            (("n",), "expected str", 1),
        ]

    def test_load_json_one_pass(self):
        schema = json_schema(Form)
        data = {**self.DATA, "unknown": [{"deep": [1, 2.5, None, "x"]}]}
        for encoded in (
            json.dumps(data),
            json.dumps(data).encode(),
            bytearray(json.dumps(data).encode()),
        ):
            loaded = schema.load_json(encoded)
            assert schema.dump(loaded) == self.DATA
            assert fields_set(loaded) == set(self.DATA)

    def test_load_json_big_int_and_bom(self):
        schema = json_schema(Form)
        assert (
            schema.load_json(b'{"item_id": 123456789012345678901234567890}').item_id
            == 10**29 + 23456789012345678901234567890
        )
        assert schema.load_json(b'\xef\xbb\xbf{"item_id": 1}').item_id == 1

    def test_not_a_model(self):
        with pytest.raises(
            TypeError, match="int is not a model, dataclass, NamedTuple or TypedDict"
        ):
            json_schema(int)
        with pytest.raises(TypeError, match="is not a model"):
            flat_schema(list[int])  # type: ignore[arg-type]

    def test_foreign_top_level(self):
        @dataclasses.dataclass
        class Point:
            x: int
            y: int = 0

        class Pair(NamedTuple):
            a: int

        class Movie(TypedDict):
            title: str

        assert json_schema(Point).load({"x": 3}) == Point(3)
        assert json_schema(Point) is json_schema(Point)
        assert json_schema(Pair).load_json(b'{"a": 1}') == Pair(1)
        assert json_schema(Movie).dump({"title": "t"}) == {"title": "t"}
        assert json_schema(Point).dump(Point(3), exclude_unset=True) == {"x": 3, "y": 0}

    def test_typeddict_under_future(self):
        class Total(TypedDict):
            always: int
            maybe: NotRequired[int]
            wrapped: Annotated[NotRequired[int], "meta"]

        class Partial(TypedDict, total=False):
            sometimes: int
            must: Required[int]
            wrapped: Annotated[Required[int], "meta"]

        assert json_codec(Total).load({"always": 1}) == {"always": 1}
        assert json_codec(Partial).load({"must": 1, "wrapped": 2}) == {"must": 1, "wrapped": 2}
        assert errors_of(json_codec(Partial).load, {"sometimes": 1}) == [
            (("must",), "field required", MISSING),
            (("wrapped",), "field required", MISSING),
        ]

    def test_dataclass_under_future(self):
        @dataclasses.dataclass
        class Seeded:
            value: int
            seed: dataclasses.InitVar[int] = 0

        @dataclasses.dataclass
        class NeedsSeed:
            value: int
            seed: dataclasses.InitVar[int]

        assert json_codec(Seeded).load({"value": 1}) == Seeded(1)
        with pytest.raises(TypeError, match="required InitVar"):
            json_codec(NeedsSeed)

    def test_set_of_frozen_dataclasses_under_future(self):
        @dataclasses.dataclass(frozen=True)
        class Tagged:
            tags: list[str]

        @dataclasses.dataclass(frozen=True)
        class Ok:
            name: str
            point: tuple[int, int] = (0, 0)

        with pytest.raises(TypeError, match="unhashable set item"):
            json_codec(set[Tagged])
        assert json_codec(set[Ok]).load([{"name": "a"}]) == {Ok("a")}

    def test_set_of_frozen_models(self):
        class Point(ModelBase, frozen=True):
            x: int
            tags: list[str] = field(default_factory=list, compare=False)

        class Tagged(ModelBase, frozen=True):
            tags: list[str]

        class HashedByHand(ModelBase):
            tags: list[str]

            def __hash__(self) -> int:
                return 1

        assert json_codec(set[Point]).load([{"x": 1}, {"x": 1, "tags": ["a"]}]) == {Point(x=1)}
        with pytest.raises(TypeError, match="unhashable set item"):
            json_codec(set[Tagged])
        assert len(json_codec(set[HashedByHand]).load([{"tags": []}])) == 1


class TestKeys:
    @pytest.mark.parametrize(
        ("rename", "names", "keys"),
        [
            ("camel", ["item_id", "_note", "__x_y", "a"], ["itemId", "_note", "__xY", "a"]),
            ("snake", ["itemId", "HTTPCode", "a"], ["item_id", "httpcode", "a"]),
            ("kebab", ["item_id", "_a_b", "pageNo"], ["item-id", "_a-b", "page-no"]),
            (str.upper, ["item_id"], ["ITEM_ID"]),
        ],
    )
    def test_rename(self, rename, names, keys):
        cls = types.new_class(
            "Renamed",
            (ModelBase,),
            {"rename": rename},
            lambda ns: ns.update(
                {"__annotations__": dict.fromkeys(names, "int"), "__module__": __name__}
            ),
        )
        assert [key for key, _ in json_schema(cls).keys.values()] == keys

    def test_two_fields_reading_one_key(self):
        with pytest.raises(TypeError, match="fields 'item_id' and 'itemId' both read the key"):

            class Clash(ModelBase, rename="kebab"):
                item_id: int
                itemId: int  # noqa: N815

        with pytest.raises(TypeError, match="both read the key"):

            class LoadClash(ModelBase):
                a: int = field(load=["b"])
                b: int

    def test_bad_rename(self):
        with pytest.raises(TypeError, match="rename must be one of"):

            class Bad(ModelBase, rename="pascal"):  # type: ignore[arg-type]
                a: int

        with pytest.raises(TypeError, match="rename returned 1, not a str"):

            class Worse(ModelBase, rename=lambda name: 1):  # type: ignore[arg-type,return-value]
                a: int

    def test_key_and_load_priority(self):
        class Keys(ModelBase, rename="camel"):
            item_id: int
            qty: Annotated[int, Key("q", load=("quantity", "qty_old"))] = 0
            note: str = field(default="", key="n", load=["old_note"])

        schema = json_schema(Keys)
        assert schema.keys == {
            "item_id": ("itemId", ()),
            "qty": ("q", ("quantity", "qty_old")),
            "note": ("n", ("old_note",)),
        }
        for data, qty in [
            ({"itemId": 1, "quantity": 2}, 2),
            ({"itemId": 1, "qty_old": 3}, 3),
            ({"itemId": 1, "qty_old": 3, "quantity": 2}, 2),
            ({"itemId": 1, "quantity": 2, "q": 9}, 9),
            ({"itemId": 1, "q": 9, "quantity": 2}, 9),
            ({"itemId": 1, "qty": 9}, 0),  # the attribute name is not a key here
        ]:
            assert schema.load(data).qty == qty
            assert schema.load_json(json.dumps(data)).qty == qty
        loaded = schema.load({"itemId": 1, "old_note": "x", "quantity": 2})
        assert (loaded.note, fields_set(loaded)) == ("x", {"item_id", "note", "qty"})
        assert schema.dump(loaded) == {"itemId": 1, "q": 2, "n": "x"}
        assert errors_of(schema.load, {"quantity": "x"}) == [
            (("itemId",), "field required", MISSING),
            (("q",), "expected int", "x"),  # the loc is the stored key
        ]

    def test_key_given_twice(self):
        with pytest.raises(TypeError, match="the stored key is given more than once"):

            class Twice(ModelBase):
                a: Annotated[int, Key("x")] = field(default=0, key="y")

        with pytest.raises(TypeError, match="the stored key is given more than once"):

            class TwoKeys(ModelBase):
                a: Annotated[int, Key("x"), Key("y")]

    def test_key_keeps_other_metadata(self):
        class Keyed(ModelBase):
            when: Annotated[datetime, Key("w"), EpochDatetime()]

        assert json_schema(Keyed).dump(Keyed(when=EPOCH_2)) == {"w": 2}

    def test_key_inside_a_container_rejected(self):
        with pytest.raises(TypeError, match="Key applies to a field"):

            class Bad(ModelBase):
                a: list[Annotated[int, Key("x")]]

    def test_rename_is_inherited_but_not_by_nested_models(self):
        class Inner(ModelBase):
            some_value: int

        class Outer(ModelBase, rename="camel"):
            inner_model: Inner

        class Child(Outer):
            extra_field: int = 0

        class Other(Outer, rename="kebab"):
            more_field: int = 0

        assert json_schema(Child).dump(Child(inner_model=Inner(some_value=1))) == {
            "innerModel": {"some_value": 1},
            "extraField": 0,
        }
        assert list(json_schema(Other).keys.values()) == [
            ("inner-model", ()),
            ("more-field", ()),
        ]

    def test_discriminator_reads_the_stored_key(self):
        class Cat(ModelBase):
            kind: Annotated[Literal["cat"], Key("type")]

        class Dog(ModelBase, rename="camel"):
            kind: Annotated[Literal["dog"], Key("type")]
            is_good: bool = True

        class Owner(ModelBase):
            pet: Annotated[Cat | Dog, Discriminator("kind")]

        owner = json_schema(Owner).load({"pet": {"type": "dog", "isGood": False}})
        assert type(owner.pet) is Dog
        assert json_schema(Owner).dump(owner) == {"pet": {"type": "dog", "isGood": False}}
        assert errors_of(json_schema(Owner).load, {"pet": {"kind": "cat"}}) == [
            (("pet", "type"), "field required", MISSING)
        ]


class Celsius(Converter):
    def to_json(self, value: Any) -> Any:
        return f"{value}C"

    def from_json(self, value: Any) -> Any:
        return float(value.removesuffix("C"))


class Hooked:
    """A type with its own converter hook (F-12 puts one on ``TelegramObject``)."""

    def __init__(self, value: str) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Hooked) and other.value == self.value

    __hash__ = None  # type: ignore[assignment]

    @classmethod
    def __aiogram_converter__(cls) -> Converter:
        return HookConverter(cls)


class HookedChild(Hooked):
    pass


class HookConverter(Converter):
    def __init__(self, tp: type) -> None:
        self.tp = tp

    def to_json(self, value: Any) -> Any:
        return {"hooked": value.value}

    def from_json(self, value: Any) -> Any:
        return self.tp(value["hooked"])


class Other(Converter):
    def to_json(self, value: Any) -> Any:
        return "other"

    def from_json(self, value: Any) -> Any:
        return Hooked("other")


class TestConverterPrecedence:
    def test_field_beats_class_map(self):
        class Times(ModelBase, converters={datetime: EpochDatetime()}):
            a: Annotated[datetime, IsoDatetime(timespec="seconds")]
            b: datetime
            c: datetime = field(default=EPOCH_2, converter=IsoDatetime(timespec="hours"))

        dumped = json_schema(Times).dump(Times(a=EPOCH_2, b=EPOCH_2))
        assert dumped == {"a": "1970-01-01T00:00:02+00:00", "b": 2, "c": "1970-01-01T00+00:00"}

    def test_converter_given_twice(self):
        with pytest.raises(TypeError, match="the converter is given twice"):

            class Twice(ModelBase):
                a: Annotated[datetime, EpochDatetime()] = field(converter=IsoDatetime())

        with pytest.raises(TypeError, match="the converter is given twice"):

            class TwiceDiscriminator(ModelBase):
                a: Annotated[int, Discriminator("x")] = field(converter=Celsius())

    def test_field_converter_keeps_the_key(self):
        class Keyed(ModelBase):
            a: Annotated[float, Key("x")] = field(default=1.0, converter=Celsius())

        assert json_schema(Keyed).dump(Keyed()) == {"x": "1.0C"}

    def test_class_map_by_mro(self):
        class Named(ModelBase, converters={enum.Enum: EnumByName()}):
            kind: Kind
            kinds: list[Kind] = []  # noqa: RUF012

        assert json_schema(Named).dump(Named(kind=Kind.A, kinds=[Kind.B])) == {
            "kind": "A",
            "kinds": ["B"],
        }

    def test_date_entry_does_not_catch_datetime(self):
        class Dated(ModelBase, converters={date: Celsius()}):
            day: date
            when: datetime

        dumped_when = json_schema(Dated).dump(Dated(day=date(2024, 1, 1), when=EPOCH_2))
        assert dumped_when["when"] == "1970-01-01T00:00:02+00:00"

    def test_exact_entry_beats_a_base_entry(self):
        class Upper(Converter):
            def to_json(self, value: Any) -> Any:
                return value.value.upper()

            def from_json(self, value: Any) -> Any:
                return Kind(value.lower())

        class Both(ModelBase, converters={enum.Enum: EnumByName(), Kind: Upper()}):
            kind: Kind

        assert json_schema(Both).dump(Both(kind=Kind.A)) == {"kind": "A"}
        assert json_schema(Both).load({"kind": "B"}).kind is Kind.B

    def test_type_hook(self):
        class Holder(ModelBase):
            a: Hooked
            b: HookedChild  # inherited through the MRO
            c: Annotated[Hooked, Other()]

        holder = json_schema(Holder).load({"a": {"hooked": "x"}, "b": {"hooked": "y"}, "c": 1})
        assert holder.a == Hooked("x")
        assert type(holder.b) is HookedChild
        assert holder.c == Hooked("other")
        assert json_schema(Holder).dump(holder) == {
            "a": {"hooked": "x"},
            "b": {"hooked": "y"},
            "c": "other",
        }

    def test_class_map_beats_the_hook(self):
        class Holder(ModelBase, converters={Hooked: Other()}):
            a: Hooked
            b: HookedChild

        assert json_schema(Holder).dump(Holder(a=Hooked("x"), b=HookedChild("y"))) == {
            "a": "other",
            "b": "other",
        }

    def test_class_map_reaches_containers_and_foreign_classes(self):
        @dataclasses.dataclass
        class Event:
            at: datetime

        class Stamp(NamedTuple):
            at: datetime

        class Log(TypedDict):
            at: datetime

        class Inner(ModelBase):  # another model keeps its own formats
            at: datetime

        class Holder(ModelBase, converters={datetime: EpochDatetime()}):
            many: list[datetime]
            by_key: dict[str, datetime | None]
            event: Event
            stamp: Stamp
            log: Log
            inner: Inner

        holder = Holder(
            many=[EPOCH_2],
            by_key={"a": EPOCH_2},
            event=Event(EPOCH_2),
            stamp=Stamp(EPOCH_2),
            log={"at": EPOCH_2},
            inner=Inner(at=EPOCH_2),
        )
        assert json_schema(Holder).dump(holder) == {
            "many": [2],
            "by_key": {"a": 2},
            "event": {"at": 2},
            "stamp": {"at": 2},
            "log": {"at": 2},
            "inner": {"at": "1970-01-01T00:00:02+00:00"},
        }
        # the dataclass on its own has no class map
        assert json_schema(Event).dump(Event(EPOCH_2)) == {"at": "1970-01-01T00:00:02+00:00"}

    def test_subclasses_inherit_and_override_the_map(self):
        class Parent(ModelBase, converters={datetime: EpochDatetime(), Kind: EnumByName()}):
            at: datetime
            kind: Kind = Kind.A

        class Child(Parent, converters={datetime: EpochDatetime(unit="ms")}):
            pass

        assert json_schema(Child).dump(Child(at=EPOCH_2)) == {"at": 2000, "kind": "A"}
        assert json_schema(Parent).dump(Parent(at=EPOCH_2)) == {"at": 2, "kind": "A"}

    def test_json_codec_converters(self):
        codec = json_codec(list[datetime], converters={datetime: EpochDatetime()})
        assert codec.dump([EPOCH_2]) == [2]


class TestForwardRefs:
    def test_self_reference(self):
        node = json_schema(Node).load({"value": 1, "children": [{"value": 2}]})
        assert node.children[0].value == 2
        assert node.children[0].children == []

    def test_mutual_module_level(self):
        forward = json_schema(Forward).load({"later": {"back": {}}})
        assert isinstance(forward.later.back, Forward)
        assert json_schema(Forward).dump(forward) == {"later": {"back": {"later": None}}}

    def test_local_classes_defined_later(self):
        class First(ModelBase):
            second: Second | None = None
            many: list[Third] = []  # noqa: RUF012

        class Second(ModelBase):
            first: First | None = None

        class Third(ModelBase):
            value: int = 0

        first = json_schema(First).load({"second": {"first": {}}, "many": [{"value": 1}]})
        assert isinstance(first.second.first, First)
        assert first.many[0].value == 1

    def test_local_class_used_before_the_other_is_defined(self):
        class Early(ModelBase):
            late: Late | None = None

        with pytest.raises(NameError, match=r"Early is not fully defined: Late is not defined"):
            Early()

        class Late(ModelBase):
            pass

        assert isinstance(Early(late=Late()).late, Late)

    def test_subclass_of_a_resolved_local_base(self):
        class Inner(ModelBase):
            value: int = 0

        class Base(ModelBase):
            inner: Inner | None = None
            many: list[Kind] = []  # noqa: RUF012

        assert json_schema(Base).load({"inner": {}}).inner == Inner()

        class Child(Base, converters={Kind: EnumByName()}):  # compiles `inner` again, later
            extra: int = 0

        child = json_schema(Child).load({"inner": {"value": 1}, "many": ["B"]})
        assert (child.inner, child.many) == (Inner(value=1), [Kind.B])

    def test_not_fully_defined(self, module_from_source):
        module = module_from_source(
            """
            from __future__ import annotations
            from aiogram.utils._converters import ModelBase

            class Pending(ModelBase):
                a: Missing1 | None = None
                b: list[Missing2] = []
                c: int = 0
            """
        )
        message = "Pending is not fully defined: Missing1, Missing2 are not defined"
        for use in (
            module.Pending,
            lambda: json_schema(module.Pending).load({}),
            lambda: json_schema(module.Pending).load_json(b"{}"),
            lambda: flat_schema(module.Pending).load(["", "", "0"]),
        ):
            with pytest.raises(NameError) as exc_info:
                use()
            assert str(exc_info.value) == message
            assert not isinstance(exc_info.value, (TypeError, ValueError))
        module.Missing1 = int
        module.Missing2 = str
        assert module.Pending(a=1, b=["x"]).b == ["x"]

    def test_one_bad_field_next_to_a_pending_one(self, module_from_source):
        with pytest.raises(TypeError, match=r"Mixed\.bad: unsupported annotation complex"):
            module_from_source(
                """
                from __future__ import annotations
                from aiogram.utils._converters import ModelBase

                class Mixed(ModelBase):
                    pending: Later
                    bad: complex
                """
            )

    def test_cross_module_subclass(self):
        from tests.test_utils._converters_base import Base  # noqa: PLC0415
        from tests.test_utils._converters_sub import Extra, Sub  # noqa: PLC0415

        sub = json_schema(Sub).load({"kind": "a", "extra": {"kind": "a", "note": "n"}})
        assert sub.kind is Base.Kind.A
        assert sub.day == date(2024, 1, 2)
        assert isinstance(sub.extra, Extra)
        assert json_schema(Sub).dump(sub) == {
            "kind": "a",
            "day": "2024-01-02",
            "extra": {"kind": "a", "day": "2024-01-02", "note": "n"},
        }

    def test_field_named_like_its_type_under_future(self):
        class Dated(ModelBase):
            date: date = date(2024, 1, 2)

        assert Dated().date == date(2024, 1, 2)
        assert json_schema(Dated).load({"date": "2024-05-06"}).date == date(2024, 5, 6)

    @pytest.mark.skipif(sys.version_info < (3, 14), reason="deferred annotations (PEP 649)")
    def test_field_named_like_its_type_eager(self, module_from_source):
        module = module_from_source(
            """
            from datetime import date
            from aiogram.utils._converters import ModelBase

            class Dated(ModelBase):
                date: date = date(2024, 1, 2)
            """
        )
        assert json_schema(module.Dated).load({"date": "2024-05-06"}).date == date(2024, 5, 6)

    @pytest.mark.skipif(sys.version_info >= (3, 14), reason="eager annotations only")
    def test_field_named_like_its_type_eager_before_pep649(self, module_from_source):
        with pytest.raises(TypeError, match="the annotation evaluates to the field's own default"):
            module_from_source(
                """
                from datetime import date
                from aiogram.utils._converters import ModelBase

                class Dated(ModelBase):
                    date: date = date(2024, 1, 2)
                """
            )

    @pytest.mark.skipif(sys.version_info < (3, 14), reason="deferred annotations (PEP 649)")
    def test_unquoted_self_reference(self, module_from_source):
        module = module_from_source(
            """
            from aiogram.utils._converters import ModelBase

            class Leaf(ModelBase):
                child: Leaf | None = None
                other: Later | None = None

            class Later(ModelBase):
                pass
            """
        )
        leaf = json_schema(module.Leaf).load({"child": {"child": None}, "other": {}})
        assert isinstance(leaf.child, module.Leaf)
        assert isinstance(leaf.other, module.Later)


class TestFlat:
    def test_round_trip(self):
        class Item(ModelBase):
            id: int
            owner: UUID
            kind: Kind
            page: int | None = None
            on: bool = False
            price: Decimal = Decimal(0)

        schema = flat_schema(Item)
        assert schema is flat_schema(Item)
        item = schema.load(["5", UID.hex, "b", "", "yes", "1.10"])
        assert (item.id, item.owner, item.kind, item.page, item.on, item.price) == (
            5,
            UID,
            Kind.B,
            None,
            True,
            Decimal("1.10"),
        )
        assert fields_set(item) == {"id", "owner", "kind", "page", "on", "price"}
        assert schema.dump(item) == ["5", UID.hex, "b", "", "1", "1.10"]
        assert schema.load(("5", str(UID), "a", "3", "0", "0")).page == 3

    def test_errors_fail_fast(self):
        class Item(ModelBase):
            id: int
            on: bool

        schema = flat_schema(Item)
        with pytest.raises(ConversionError) as exc_info:
            schema.load(["x", "maybe"])
        assert [tuple(e) for e in exc_info.value.errors] == [(("id",), "expected int", "x")]
        assert exc_info.value.title == f"loading {Item.__qualname__}"
        assert errors_of(schema.load, ["1"]) == [((), "expected 2 parts", ["1"])]
        assert errors_of(schema.load, ("1", "2", "3")) == [
            ((), "expected 2 parts", ["1", "2", "3"])
        ]
        assert errors_of(schema.dump, 5) == [((), f"expected {Item.__qualname__}", 5)]
        bad = Item(id=1, on=True)
        object.__setattr__(bad, "id", "x")
        assert errors_of(schema.dump, bad) == [(("id",), "expected int", "x")]

    def test_flat_user_converter(self):
        class Shout(Converter):
            def to_json(self, value: Any) -> Any:
                return value.upper()

            def from_json(self, value: Any) -> Any:
                return value.lower()

            def to_str(self, value: Any) -> str:
                return value.upper()

            def from_str(self, value: str) -> Any:
                if not value:
                    msg = "empty"
                    raise ValueError(msg)
                return value.lower()

        class Loud(ModelBase):
            word: Annotated[str, Shout()]
            count: int = 0

        assert flat_schema(Loud).load(["HEY", "2"]).word == "hey"
        assert flat_schema(Loud).dump(Loud(word="ho")) == ["HO", "0"]
        assert errors_of(flat_schema(Loud).load, ["", "0"]) == [(("word",), "empty", "")]
        assert json_schema(Loud).load_json(b'{"word": "HO"}').word == "ho"

    def test_dataclass_flat(self):
        @dataclasses.dataclass
        class Point:
            x: int
            y: int = 0

        assert flat_schema(Point).load(["1", "2"]) == Point(1, 2)
        assert flat_schema(Point).dump(Point(1)) == ["1", "0"]

    @pytest.mark.parametrize(
        ("annotation", "message"),
        [
            ("datetime", "datetime has no flat-string form"),
            ("list[int]", "list has no flat-string form"),
            ("int | str", "int | str has no flat-string form"),
            ("Address", "Address has no flat-string form"),
            (
                "Annotated[int, Key('i')]",
                "callback data is packed by position; Key and rename have no effect",
            ),
        ],
    )
    def test_rejected_fields(self, annotation, message):
        cls = types.new_class(
            "Item",
            (ModelBase,),
            {},
            lambda ns: ns.update({"__annotations__": {"v": annotation}, "__module__": __name__}),
        )
        with pytest.raises(TypeError, match=rf"Item\.v: {message}"):
            flat_schema(cls)

    def test_rename_rejected(self):
        class Renamed(ModelBase, rename="camel"):
            item_id: int

        with pytest.raises(TypeError, match="callback data is packed by position"):
            flat_schema(Renamed)
        assert json_schema(Renamed).load({"itemId": 1}).item_id == 1

    def test_typeddict_is_not_flat(self):
        class Movie(TypedDict):
            title: str

        with pytest.raises(TypeError):
            flat_schema(Movie)


def test_core_stub_surface():
    """The only place the raw ``_core`` objects matter: the resolver builds them."""
    from aiogram import _core  # noqa: PLC0415

    kind = _core.Kind.int_()
    assert (kind.label, kind.flat) == ("int", True)
    assert repr(kind) == "<Kind int>"
    field_ = _core.Field("a", kind, key="b", load=["c"])
    assert (field_.name, field_.key, field_.load, field_.kind) == ("a", "b", ("c",), kind)
    core = Address.__aiogram_core__
    assert (core.tp, core.ready) == (Address, True)
    with pytest.raises(RuntimeError, match="has its fields set already"):
        core.set_fields([])
    cell = _core.KindCell()
    cell.set(kind)
    with pytest.raises(RuntimeError):
        cell.set(kind)
    assert json_codec(int).kind.label == "int"


def test_no_heavy_imports():
    """The converter modules and the extension import only the standard library."""
    root = Path(_converters.__file__).parents[2]
    code = textwrap.dedent(f"""
        import sys, types
        for name, path in [("aiogram", {str(root / "aiogram")!r}),
                           ("aiogram.utils", {str(root / "aiogram" / "utils")!r})]:
            package = types.ModuleType(name)
            package.__path__ = [path]
            sys.modules[name] = package  # skip aiogram/__init__ (it imports the Bot API)
        import aiogram.utils._converters
    """)
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-X", "importtime", "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    imported = {line.rsplit("|", 1)[-1].strip() for line in result.stderr.splitlines()}
    assert "aiogram._core" in imported  # the check sees the module's imports
    assert "dataclasses" in imported
    for name in imported:
        assert name.split(".")[0] not in {"pydantic", "pydantic_core", "attrs", "attr", "msgspec"}


def test_recursive_local_model_is_collected():
    def make() -> weakref.ref[type]:
        # a function of its own: on 3.11 / 3.12 a frame caches its locals until it returns
        class Leaf(ModelBase):
            value: int = 0

        class Tree(ModelBase):
            children: list[Tree] = []  # noqa: RUF012
            parent: Tree | None = None
            leaf: Leaf | None = None

        class Child(Tree):  # compiles the inherited fields again, from the kept locals
            pass

        assert json_schema(Child).load({"children": [{"leaf": {}}]}).children[0].children == []
        return weakref.ref(Tree)

    refs = [make() for _ in range(5)]
    gc.collect()
    assert all(ref() is None for ref in refs)


def test_threads_compile_and_resolve_concurrently(module_from_source):
    errors: list[BaseException] = []
    barrier = threading.Barrier(8)
    module = module_from_source(
        """
        from __future__ import annotations
        from aiogram.utils._converters import ModelBase

        class Lazy(ModelBase):
            later: list[Later] = []

        class Later(ModelBase):
            value: int = 0
        """
    )
    lazy = module.Lazy

    def worker(index: int) -> None:
        try:
            barrier.wait()
            assert json_schema(lazy).load({"later": [{"value": index}]}).later[0].value == index
            cls = types.new_class(
                f"Local{index}",
                (ModelBase,),
                {"rename": "camel"},
                lambda ns: ns.update(
                    {"__annotations__": {"some_value": "list[int]"}, "__module__": __name__}
                ),
            )
            for _ in range(50):
                obj = json_schema(cls).load_json(b'{"someValue": [1, 2]}')
                assert json_schema(cls).dump_json(obj) == b'{"someValue":[1,2]}'
        except BaseException as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert errors == []


class TestReviewRegressions:
    """Codex review of plan-10 (2026-11-21)."""

    def test_decimal_number_in_a_union_keeps_its_digits(self):
        from aiogram.utils.converters import DecimalAsNumber  # noqa: PLC0415

        exact = Decimal("0.12345678901234567890123456789")
        codec = json_codec(Annotated[Decimal, DecimalAsNumber()] | str)
        assert codec.load_json(codec.dump_json(exact)) == exact
        assert codec.load_json(b'"x"') == "x"

        class Priced(ModelBase):
            kind: Literal["priced"]
            price: Annotated[Decimal, DecimalAsNumber()]

        class Free(ModelBase):
            kind: Literal["free"]

        tagged = json_codec(Annotated[Priced | Free, Discriminator("kind")])
        loaded = tagged.load_json(b'{"kind": "priced", "price": 0.12345678901234567890123456789}')
        assert loaded.price == exact

    def test_local_union_and_annotated_aliases_reach_subclasses(self):
        def make() -> type:
            Number = int | str  # noqa: N806
            Tagged = Annotated[int, "meta"]  # noqa: N806

            class Base(ModelBase):
                number: Number
                tagged: Tagged

            json_schema(Base).load({"number": 1, "tagged": 2})  # resolved, locals released

            class Child(Base):
                extra: Number = 0

            return Child

        assert json_schema(make()).load({"number": "x", "tagged": 2}).number == "x"

    def test_typeddict_required_from_the_evaluated_annotation(self):
        class Movie(TypedDict):
            title: str
            year: typing.Annotated[typing.NotRequired[int], "meta"]

        class Partial(TypedDict, total=False):
            title: typing.Annotated[typing.Required[str], "meta"]
            year: int

        assert json_codec(Movie).load({"title": "x"}) == {"title": "x"}
        assert errors_of(json_codec(Partial).load, {"year": 1}) == [
            (("title",), "field required", MISSING)
        ]

    @pytest.mark.parametrize("bytes_path", [False, True])
    def test_discriminator_reads_fallback_keys(self, bytes_path):
        class CatK(ModelBase):
            kind: Annotated[Literal["cat"], Key("type", load=("kind",))]

        class DogK(ModelBase):
            kind: Annotated[Literal["dog"], Key("type", load=("kind",))]

        codec = json_codec(Annotated[CatK | DogK, Discriminator("kind")])

        def load(value: dict[str, Any]) -> Any:
            return codec.load_json(json.dumps(value).encode()) if bytes_path else codec.load(value)

        assert isinstance(load({"kind": "cat"}), CatK)
        assert isinstance(load({"kind": "cat", "type": "dog"}), DogK)  # the stored key wins
        assert errors_of(load, {"kind": "cow"}) == [
            (("kind",), "expected one of ['cat', 'dog']", "cow")
        ]

    def test_discriminator_fallback_keys_must_agree(self):
        class CatK(ModelBase):
            kind: Annotated[Literal["cat"], Key("type", load=("kind",))]

        class DogK(ModelBase):
            kind: Annotated[Literal["dog"], Key("type")]

        with pytest.raises(TypeError, match="under different keys"):
            json_codec(Annotated[CatK | DogK, Discriminator("kind")])

    def test_alias_referring_to_itself_outside_a_container(self, module_from_source):
        if sys.version_info < (3, 12):
            pytest.skip("PEP 695")
        module = module_from_source(
            """
            type Loop = Loop | int
            type Tree = dict[str, Tree] | int
            """
        )
        with pytest.raises(TypeError, match="refers to itself outside a list, tuple, dict"):
            json_codec(module.Loop)
        assert json_codec(module.Tree).load({"a": {"b": 1}}) == {"a": {"b": 1}}

    def test_load_json_error_cap_reports_no_false_missing_fields(self):
        class Capped(ModelBase):
            a: int
            b: list[int]

        document = json.dumps({"b": ["x"] * 150, "a": 1}).encode()
        errors = errors_of(json_schema(Capped).load_json, document)
        assert len(errors) == 100
        assert all(error[0][0] == "b" for error in errors)

    def test_local_literal_alias_reaches_subclasses(self):
        def make() -> type:
            Color = Literal["r", "g"]  # noqa: N806

            class Painted(ModelBase):
                color: Color

            json_schema(Painted).load({"color": "r"})
            return Painted

        class Repainted(make()):  # type: ignore[misc]
            extra: int = 0

        assert json_schema(Repainted).load({"color": "g"}).color == "g"

    def test_set_item_uses_its_own_function_locals(self):
        def make() -> type:
            class Inner(ModelBase, frozen=True):
                a: int

            class Item(ModelBase, frozen=True):
                x: Inner

            return Item

        item = make()

        class Basket(ModelBase):
            items: set[item]  # type: ignore[valid-type]

        loaded = json_schema(Basket).load({"items": [{"x": {"a": 1}}]})
        assert len(loaded.items) == 1

    def test_typeddict_subclass_from_another_module(self, module_from_source):
        if sys.version_info < (3, 12):
            pytest.skip("TypedDict has no __orig_bases__ before 3.12")
        module_from_source(
            """
            from __future__ import annotations
            from typing import TypedDict

            class Point(TypedDict):
                x: int
                tag: Tag

            Tag = str
            """,
            name="_converters_case_td_base",
        )
        child = module_from_source(
            """
            from __future__ import annotations
            from _converters_case_td_base import Point

            class Point3(Point):
                z: int
            """
        )
        assert json_codec(child.Point3).load({"x": 1, "tag": "t", "z": 2}) == {
            "x": 1,
            "tag": "t",
            "z": 2,
        }

    def test_converter_on_an_optional_field(self):
        class Up(Converter):
            def to_json(self, value: str) -> str:
                return value.upper()

            def from_json(self, value: Any) -> str:
                return str(value).lower()

        class Stamped(ModelBase):
            at: datetime | None = field(default=None, converter=IsoDatetime(timespec="seconds"))
            name: str | None = field(default=None, converter=Up())
            other: Annotated[str | None, Up()] = None

        schema = json_schema(Stamped)
        empty = Stamped()
        assert schema.dump(empty) == {"at": None, "name": None, "other": None}
        full = Stamped(at=EPOCH_2, name="a", other="b")
        assert schema.dump(full) == {"at": "1970-01-01T00:00:02+00:00", "name": "A", "other": "B"}
        assert schema.load({"name": "X", "at": None}).name == "x"

    def test_empty_conversion_error_from_a_converter(self):
        class Empty(Converter):
            def to_json(self, value: Any) -> Any:
                return value

            def from_json(self, value: Any) -> Any:
                raise ConversionError("bad", [])

        class Holder(ModelBase):
            value: Annotated[int, Empty()]

        errors = errors_of(json_schema(Holder).load, {"value": 1})
        assert [error[:1] for error in errors] == [(("value",),)]

    def test_union_member_reads_the_whole_object_before_failing(self):
        class Keyed(ModelBase):
            a: Annotated[int, Key("a", load=("old",))]

        class Holder(ModelBase):
            v: Keyed | int

        schema = json_schema(Holder)
        assert schema.load_json(b'{"v": {"old": "x", "a": 1}}').v == Keyed(a=1)
        assert schema.load_json(b'{"v": {"a": "x", "a": 1}}').v == Keyed(a=1)
        assert json_codec(dict[str, int] | int).load_json(b'{"a": "x", "a": 1}') == {"a": 1}

    def test_released_locals_keep_constants_and_markers(self):
        def make() -> type:
            MODE = "a"  # noqa: N806
            KEY = Key("k")  # noqa: N806

            class Based(ModelBase):
                m: Literal[MODE] = "a"
                n: Annotated[int, KEY] = 0

            json_schema(Based).dump(Based())
            return Based

        class Sub(make()):  # type: ignore[misc]
            extra: int = 0

        assert json_schema(Sub).dump(Sub()) == {"m": "a", "k": 0, "extra": 0}

    def test_replace_keeps_the_set_fields(self):
        class Z(ModelBase):
            x: int = 1
            y: int = 2
            z: int = 3

        assert fields_set(copy.replace(Z(x=1), y=5)) == {"x", "y"}
        assert json_schema(Z).dump(copy.replace(Z(x=1), y=5), exclude_unset=True) == {
            "x": 1,
            "y": 5,
        }

    def test_name_error_from_user_code_is_not_a_pending_name(self):
        class Hooked:
            @classmethod
            def __aiogram_converter__(cls) -> Converter:
                raise NameError("typo")

        with pytest.raises(NameError, match="typo"):

            class Uses(ModelBase):
                h: Hooked

    def test_load_json_str_with_a_lone_surrogate(self):
        codec = json_codec(str)
        assert codec.load_json('"a\ud800"') == "a\ud800"
        with pytest.raises(ConversionError, match="lone surrogate"):
            codec.load_json('"a\ud800')

    def test_pep695_generic_parameter_order_identity_and_recursion(self, module_from_source):
        if sys.version_info < (3, 12):
            pytest.skip("PEP 695")
        module = module_from_source(
            """
            type Swap[T, U] = tuple[U, T]
            type Identity[T] = T
            type Tree[T] = T | list[Tree[T]]
            """
        )
        assert json_codec(module.Swap[int, str]).load(["x", 1]) == ("x", 1)
        assert json_codec(module.Identity[int]).load(5) == 5
        # unhashable Annotated metadata in a type argument: memoised by identity
        assert json_codec(module.Identity[Annotated[int, {"meta": []}]]).load(5) == 5
        assert json_codec(module.Tree[int]).load([1, [2, [3]]]) == [1, [2, [3]]]

    def test_field_converter_next_to_unrelated_metadata(self):
        class Meta(ModelBase):
            at: Annotated[datetime, "meta"] = field(
                default=EPOCH_2, converter=IsoDatetime(timespec="seconds")
            )

        assert json_schema(Meta).dump(Meta()) == {"at": "1970-01-01T00:00:02+00:00"}

    def test_union_member_with_a_failed_nested_list(self):
        class WithInts(ModelBase):
            x: list[int]

        class WithStrs(ModelBase):
            x: list[str]

        codec = json_codec(WithInts | WithStrs)
        assert codec.load_json(b'{"x": ["a", "b"]}') == WithStrs(x=["a", "b"])
        assert codec.load({"x": ["a", "b"]}) == WithStrs(x=["a", "b"])
        with pytest.raises(ConversionError) as exc_info:
            codec.load_json(b'{"x": [1.5]}')
        loc, message, _ = exc_info.value.errors[0]
        assert loc == ()
        assert message.startswith("expected ") and "WithInts |" in message
        assert len(exc_info.value.__notes__) == 2

    def test_converter_on_a_generic_alias(self, module_from_source):
        if sys.version_info < (3, 12):
            pytest.skip("PEP 695")
        module = module_from_source(
            """
            type Identity[T] = T
            type Maybe[T] = T | None
            """
        )

        class Up(Converter):
            def to_json(self, value: str) -> str:
                return value.upper()

            def from_json(self, value: Any) -> str:
                return str(value)

        stamped = json_codec(Annotated[module.Identity[datetime], EpochDatetime()])
        assert stamped.dump(EPOCH_2) == 2
        maybe = json_codec(Annotated[module.Maybe[str], Up()])
        assert maybe.dump(None) is None
        assert maybe.dump("a") == "A"

    def test_inherited_field_redeclared_as_classvar(self):
        class Parent(ModelBase):
            x: int
            y: int = 0

        class Child(Parent):
            x: ClassVar[int] = 42

        assert Child(y=1).y == 1
        assert json_schema(Child).dump(Child()) == {"y": 0}
        assert Child.x == 42

    def test_epoch_dump_beyond_float_exact_microseconds(self):
        stamp = datetime(2300, 1, 1, 0, 0, 0, 1, tzinfo=UTC)
        codec = json_codec(Annotated[datetime, EpochDatetime()])
        assert codec.dump(stamp) == stamp.timestamp()
        assert json.loads(codec.dump_json(stamp)) == stamp.timestamp()

    @pytest.mark.skipif(sys.version_info < (3, 14), reason="deferred annotations (PEP 649)")
    def test_field_named_like_its_type_with_a_field_specifier(self, module_from_source):
        module = module_from_source(
            """
            import dataclasses
            from datetime import date
            from aiogram.utils._converters import ModelBase
            from aiogram.utils.converters import field

            class Dated(ModelBase):
                date: date = field(default=date(2020, 1, 1))

            class Factory(ModelBase):
                date: date = dataclasses.field(default_factory=lambda: date(2020, 1, 2))
            """
        )
        assert json_schema(module.Dated).dump(module.Dated()) == {"date": "2020-01-01"}
        assert json_schema(module.Factory).dump(module.Factory()) == {"date": "2020-01-02"}

    def test_optional_bytes_has_no_flat_form(self):
        assert not json_codec(bytes | None).kind.flat
        assert json_codec(bytes).kind.flat

    def test_replace_keeps_a_frozenset(self):
        class Small(ModelBase):
            a: int = 0

        assert type(fields_set(copy.replace(Small(), a=2))) is frozenset

    def test_union_notes_cut_long_values(self):
        with pytest.raises(ConversionError) as exc_info:
            json_codec(int | bool).load("x" * 10_000)
        assert all(len(note) < 200 for note in exc_info.value.__notes__)
