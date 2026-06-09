import pytest

from aiogram.dispatcher.flags import Flag, FlagDecorator, FlagGenerator


@pytest.fixture(name="flag")
def flag_fixture() -> Flag:
    return Flag("test", True)


@pytest.fixture(name="flag_decorator")
def flag_decorator_fixture(flag: Flag) -> FlagDecorator:
    return FlagDecorator(flag)


@pytest.fixture(name="flag_generator")
def flag_flag_generator() -> FlagGenerator:
    return FlagGenerator()


class TestFlagDecorator:
    def test_with_value(self, flag_decorator: FlagDecorator):
        new_decorator = flag_decorator._with_value(True)

        assert new_decorator is not flag_decorator
        assert new_decorator.flag is not flag_decorator.flag
        assert new_decorator.flag

    def test_call_invalid(self, flag_decorator: FlagDecorator):
        with pytest.raises(ValueError):
            flag_decorator(True, test=True)

    def test_call_with_function(self, flag_decorator: FlagDecorator):
        def func():
            pass

        decorated = flag_decorator(func)
        assert decorated is func
        assert hasattr(decorated, "aiogram_flag")

    def test_call_with_arg(self, flag_decorator: FlagDecorator):
        new_decorator = flag_decorator("hello")
        assert new_decorator is not flag_decorator
        assert new_decorator.flag.value == "hello"

    def test_call_with_kwargs(self, flag_decorator: FlagDecorator):
        new_decorator = flag_decorator(test=True)
        assert new_decorator is not flag_decorator
        assert isinstance(new_decorator.flag.value, dict)
        assert "test" in new_decorator.flag.value


class TestFlagGenerator:
    def test_getattr(self):
        generator = FlagGenerator()
        assert isinstance(generator.foo, FlagDecorator)
        assert isinstance(generator.bar, FlagDecorator)

        assert generator.foo is not generator.foo
        assert generator.foo is not generator.bar

    def test_failed_getattr(self):
        generator = FlagGenerator()

        with pytest.raises(AttributeError):
            generator._something
