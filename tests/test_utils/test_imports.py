import pytest

import aiogram
from aiogram.utils.imports import import_module


class TestImports:
    def test_bad_type(self):
        with pytest.raises(ValueError, match=r"Target should be string not"):
            import_module(42)

    @pytest.mark.parametrize("value", ["module", "module:", ":attribute"])
    def test_bad_format(self, value):
        with pytest.raises(ValueError, match='must be in format "<module>:<attribute>"'):
            import_module(value)

    @pytest.mark.parametrize("value", ["module", "aiogram.KABOOM", "aiogram.KABOOM.TEST"])
    def test_bad_value(self, value):
        with pytest.raises(ValueError, match="Could not import module"):
            import_module(f"{value}:attribute")

    def test_has_no_attribute(self):
        with pytest.raises(ValueError, match="has no attribute"):
            import_module("aiogram:KABOOM")

    def test_imported(self):
        value = import_module("aiogram:__version__")
        isinstance(value, str)
        assert value == aiogram.__version__
