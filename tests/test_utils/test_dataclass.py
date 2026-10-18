from aiogram.utils.dataclass import dataclass_kwargs


class TestDataclassKwargs:
    def test_dataclass_kwargs(self):
        assert dataclass_kwargs(
            init=True,
            repr=True,
            eq=True,
            order=True,
            unsafe_hash=True,
            frozen=True,
            match_args=True,
            kw_only=True,
            slots=True,
            weakref_slot=True,
        ) == {
            "init": True,
            "repr": True,
            "eq": True,
            "order": True,
            "unsafe_hash": True,
            "frozen": True,
            "match_args": True,
            "kw_only": True,
            "slots": True,
            "weakref_slot": True,
        }

    def test_dataclass_kwargs_skips_unset(self):
        assert dataclass_kwargs() == {}
        assert dataclass_kwargs(frozen=False, slots=True) == {"frozen": False, "slots": True}
