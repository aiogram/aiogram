from aiogram.utils.mixins import DataMixin


class MyClass(DataMixin):
    pass


class TestDataMixin:
    def test_store_value(self):
        obj = MyClass()
        obj["foo"] = 42

        assert "foo" in obj
        assert obj["foo"] == 42
        assert len(obj.data) == 1

    def test_remove_value(self):
        obj = MyClass()
        obj["foo"] = 42
        del obj["foo"]

        assert "key" not in obj
        assert len(obj.data) == 0

    def test_getter(self):
        obj = MyClass()
        obj["foo"] = 42

        assert obj.get("foo") == 42
        assert obj.get("bar") is None
        assert obj.get("baz", "test") == "test"


class TestContextInstanceMixin:
    def test_instance(self):
        pass
