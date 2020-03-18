import pytest

from aiogram.utils.mixins import ContextInstanceMixin

class ContextObject(ContextInstanceMixin['ContextObject']):
    pass


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
