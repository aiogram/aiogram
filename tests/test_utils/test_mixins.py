import pytest

from aiogram.utils.mixins import ContextInstanceMixin, DataMixin, KeepRefsMixin


class ContextObject(ContextInstanceMixin["ContextObject"]):
    pass


class DataObject(DataMixin):
    pass


class RefsObject(KeepRefsMixin):
    pass


class TestDataMixin:
    def test_store_value(self):
        obj = DataObject()
        obj["foo"] = 42

        assert "foo" in obj
        assert obj["foo"] == 42
        assert len(obj.data) == 1

    def test_remove_value(self):
        obj = DataObject()
        obj["foo"] = 42
        del obj["foo"]

        assert "key" not in obj
        assert len(obj.data) == 0

    def test_getter(self):
        obj = DataObject()
        obj["foo"] = 42

        assert obj.get("foo") == 42
        assert obj.get("bar") is None
        assert obj.get("baz", "test") == "test"


class TestContextInstanceMixin:
    def test_empty(self):
        obj = ContextObject()

        assert obj.get_current(no_error=True) is None
        with pytest.raises(LookupError):
            assert obj.get_current(no_error=False)

    def test_set_wrong_type(self):
        obj = ContextObject()

        with pytest.raises(
            TypeError, match=r"Value should be instance of 'ContextObject' not '.+'"
        ):
            obj.set_current(42)


class TestKeepRefsMixin:
    def test_refs_are_saved(self):
        obj = RefsObject()

        assert obj in RefsObject.get_instances()

    def test_refs_are_deleted(self):
        obj = RefsObject()
        size_with_obj = len(RefsObject.get_instances())
        del obj
        size_without_obj = len(RefsObject.get_instances())

        assert size_with_obj - 1 == size_without_obj
