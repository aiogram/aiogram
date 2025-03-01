import pytest

from aiogram.utils.class_attrs_resolver import (
    get_reversed_mro_unique_attrs_resolver,
    get_sorted_mro_attrs_resolver,
    inspect_members_resolver,
)


class SimpleClass1:
    def method1(self):
        pass

    def method2(self):
        pass


class SimpleClass2:
    def method2(self):
        pass

    def method1(self):
        pass


class InheritedClass1(SimpleClass1):
    def method3(self):
        pass

    def method4(self):
        pass


class InheritedClass2(SimpleClass1):
    def method2(self):
        pass

    def method3(self):
        pass


class TestClassAttrsResolver:
    @pytest.mark.parametrize(
        "cls, resolver, expected",
        [
            # inspect_members_resolver
            (SimpleClass1, inspect_members_resolver, ["method1", "method2"]),
            (SimpleClass2, inspect_members_resolver, ["method1", "method2"]),
            (
                InheritedClass1,
                inspect_members_resolver,
                ["method1", "method2", "method3", "method4"],
            ),
            (InheritedClass2, inspect_members_resolver, ["method1", "method2", "method3"]),
            # get_reversed_mro_unique_attrs_resolver
            (SimpleClass1, get_reversed_mro_unique_attrs_resolver, ["method1", "method2"]),
            (SimpleClass2, get_reversed_mro_unique_attrs_resolver, ["method2", "method1"]),
            (
                InheritedClass1,
                get_reversed_mro_unique_attrs_resolver,
                ["method1", "method2", "method3", "method4"],
            ),
            (
                InheritedClass2,
                get_reversed_mro_unique_attrs_resolver,
                ["method1", "method2", "method3"],
            ),
            # get_sorted_mro_attrs_resolver
            (SimpleClass1, get_sorted_mro_attrs_resolver, ["method1", "method2"]),
            (SimpleClass2, get_sorted_mro_attrs_resolver, ["method2", "method1"]),
            (
                InheritedClass1,
                get_sorted_mro_attrs_resolver,
                ["method3", "method4", "method1", "method2"],
            ),
            (InheritedClass2, get_sorted_mro_attrs_resolver, ["method3", "method1", "method2"]),
        ],
    )
    def test_resolve_class_attrs(self, cls, resolver, expected):
        names = [name for name, _ in resolver(cls) if not name.startswith("__")]
        assert names == expected
