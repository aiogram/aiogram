from unittest.mock import patch

import pytest

from aiogram.utils.dataclass import dataclass_kwargs

ALL_VERSIONS = {
    "init": True,
    "repr": True,
    "eq": True,
    "order": True,
    "unsafe_hash": True,
    "frozen": True,
}
ADDED_IN_3_10 = {"match_args": True, "kw_only": True, "slots": True}
ADDED_IN_3_11 = {"weakref_slot": True}

PY_310 = {**ALL_VERSIONS, **ADDED_IN_3_10}
PY_311 = {**PY_310, **ADDED_IN_3_11}
LATEST_PY = PY_311


class TestDataclassKwargs:
    @pytest.mark.parametrize(
        "py_version,expected",
        [
            ((3, 10, 2), PY_310),
            ((3, 11, 0), PY_311),
            ((4, 13, 0), LATEST_PY),
        ],
    )
    def test_dataclass_kwargs(self, py_version, expected):
        with patch("sys.version_info", py_version):

            assert (
                dataclass_kwargs(
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
                )
                == expected
            )
