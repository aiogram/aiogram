import pytest

from aiogram.utils.helper import Helper, HelperMode, Item, ListItem, OrderedHelper


class TestHelper:
    def test_items_all(self):
        class MyHelper(Helper):
            A = Item()
            B = Item()
            C = Item()
            D = Item()

        assert set(MyHelper.all()) == {"A", "B", "C", "D"}

    def test_listed_items_all(self):
        class MyHelper(Helper):
            A = ListItem()
            B = ListItem()
            C = ListItem()
            D = ListItem()

        assert set(MyHelper.all()) == {"A", "B", "C", "D"}

    def test_listed_items_combinations(self):
        class MyHelper(Helper):
            A = ListItem()
            B = ListItem()
            C = ListItem()
            D = ListItem()

        assert (MyHelper.A | MyHelper.B) == ["A", "B"]
        assert (MyHelper.C & MyHelper.D) == ["C", "D"]
        assert MyHelper.A.add(MyHelper.D) == ["A", "D"]
        assert MyHelper.B + MyHelper.D == ["B", "D"]

    def test_wrong_name(self):
        with pytest.raises(RuntimeError):

            class MyHelper(Helper):
                kaboom = Item()


class TestHelperMode:
    def test_helper_mode_all(self):
        assert set(HelperMode.all()) == {
            "SCREAMING_SNAKE_CASE",
            "lowerCamelCase",
            "CamelCase",
            "snake_case",
            "lowercase",
        }

    def test_screaming_snake_case(self):
        class MyHelper(Helper):
            mode = HelperMode.SCREAMING_SNAKE_CASE

            FOO = Item()
            BAR_BAZ = Item()

        assert MyHelper.FOO == "FOO"
        assert MyHelper.BAR_BAZ == "BAR_BAZ"

    def test_lower_camel_case(self):
        class MyHelper(Helper):
            mode = HelperMode.lowerCamelCase

            FOO = Item()
            BAR_BAZ = Item()

        assert MyHelper.FOO == "foo"
        assert MyHelper.BAR_BAZ == "barBaz"

    def test_camel_case(self):
        class MyHelper(Helper):
            mode = HelperMode.CamelCase

            FOO = Item()
            BAR_BAZ = Item()

        assert MyHelper.FOO == "Foo"
        assert MyHelper.BAR_BAZ == "BarBaz"

    def test_snake_case(self):
        class MyHelper(Helper):
            mode = HelperMode.snake_case

            FOO = Item()
            BAR_BAZ = Item()

        assert MyHelper.FOO == "foo"
        assert MyHelper.BAR_BAZ == "bar_baz"

    def test_lowercase(self):
        class MyHelper(Helper):
            mode = HelperMode.lowercase

            FOO = Item()
            BAR_BAZ = Item()

        assert MyHelper.FOO == "foo"
        assert MyHelper.BAR_BAZ == "barbaz"

    def test_extended_converters(self):
        assert HelperMode.apply("test_text", mode=HelperMode.SCREAMING_SNAKE_CASE) == "TEST_TEXT"
        assert HelperMode.apply("TestText", mode=HelperMode.SCREAMING_SNAKE_CASE) == "TEST_TEXT"
        assert HelperMode.apply("test_text", mode=HelperMode.snake_case) == "test_text"
        assert HelperMode.apply("foo", mode=lambda m: m.upper()) == "FOO"


class TestOrderedHelper:
    def test_items_are_ordered(self):
        class MyOrderedHelper(OrderedHelper):
            A = Item()
            D = Item()
            C = Item()
            B = Item()

        assert MyOrderedHelper.all() == ["A", "D", "C", "B"]

    def test_list_items_are_ordered(self):
        class MyOrderedHelper(OrderedHelper):
            A = ListItem()
            D = ListItem()
            C = ListItem()
            B = ListItem()

        assert MyOrderedHelper.all() == ["A", "D", "C", "B"]
