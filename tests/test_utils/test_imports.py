import pytest

import aiogram
from aiogram.utils.imports import import_module, import_all_modules


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


class TestAllModulesImports:
    def test_relative_import_without_package(self):
        with pytest.raises(TypeError, match="the 'package' argument is required to perform a relative import for"):
            import_all_modules(".kaboom")

    def test_non_existing_root(self):
        with pytest.raises(ModuleNotFoundError):
            import_all_modules("kaboom")

    def test_non_existing_package(self):
        with pytest.raises(ModuleNotFoundError):
            import_all_modules("test", "kaboom")

    def test_imported(self, capfd):
        import_all_modules("tests.modules_for_tests")
        captured = capfd.readouterr()
        assert captured.out == "__init__ imported\nsmall_module imported\n" \
                               "small_package imported\nnested_small_module imported\n"
