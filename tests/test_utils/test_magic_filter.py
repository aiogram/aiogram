import os
import warnings
from dataclasses import dataclass
from re import Match

import pytest

from aiogram import F
from aiogram.utils.magic_filter import MagicFilter


@dataclass
class MyObject:
    text: str
    caption: str = ""


class TestMagicFilter:
    # --- existing .as_() tests ---

    def test_operation_as(self):
        magic: MagicFilter = F.text.regexp(r"^(\d+)$").as_("match")

        assert not magic.resolve(MyObject(text="test"))

        result = magic.resolve(MyObject(text="123"))
        assert isinstance(result, dict)
        assert isinstance(result["match"], Match)

    def test_operation_as_not_none(self):
        # Issue: https://github.com/aiogram/aiogram/issues/1281
        magic = F.cast(int).as_("value")

        result = magic.resolve("0")
        assert result == {"value": 0}

    def test_operation_as_not_none_iterable(self):
        # Issue: https://github.com/aiogram/aiogram/issues/1281
        magic = F.as_("value")

        result = magic.resolve([])
        assert result is None

    # --- __ror__ / __rand__ warning tests ---

    @pytest.mark.parametrize(
        "left_operand",
        [
            pytest.param("confirm", id="str"),
            pytest.param(42, id="int"),
            pytest.param(True, id="bool"),
            pytest.param(3.14, id="float"),
            pytest.param(None, id="None"),
            pytest.param([], id="list"),
        ],
    )
    def test_ror_non_filter_warns(self, left_operand):
        """__ror__ with a non-MagicFilter left operand should emit UserWarning."""
        with pytest.warns(UserWarning, match="Possible operator precedence mistake") as rec:
            result = left_operand | F.text
        assert isinstance(result, MagicFilter)
        # repr of the offending value must appear in the warning text
        assert repr(left_operand) in str(rec[0].message)

    @pytest.mark.parametrize(
        "left_operand",
        [
            pytest.param("value", id="str"),
            pytest.param(42, id="int"),
            pytest.param(True, id="bool"),
            pytest.param(3.14, id="float"),
        ],
    )
    def test_rand_non_filter_warns(self, left_operand):
        """__rand__ with a non-MagicFilter left operand should emit UserWarning."""
        with pytest.warns(UserWarning, match="Possible operator precedence mistake") as rec:
            result = left_operand & F.text
        assert isinstance(result, MagicFilter)
        assert repr(left_operand) in str(rec[0].message)

    def test_ror_warning_stacklevel_points_to_caller(self):
        """The warning must reference the caller's line, not magic_filter.py internals."""
        with pytest.warns(UserWarning) as rec:
            _ = "oops" | F.text  # this is the line that should be reported
        # Warning filename must be THIS test file, not aiogram/utils/magic_filter.py
        assert os.path.basename(rec[0].filename) == "test_magic_filter.py"

    def test_rand_warning_stacklevel_points_to_caller(self):
        """The warning must reference the caller's line, not magic_filter.py internals."""
        with pytest.warns(UserWarning) as rec:
            _ = "oops" & F.text  # this is the line that should be reported
        assert os.path.basename(rec[0].filename) == "test_magic_filter.py"

    def test_real_world_bug_pattern_warns(self):
        """
        The canonical bug from the issue:
            F.text == "confirm" | F.text == "cancel"
        Python parses this as:
            F.text == ("confirm" | F.text) == "cancel"   # semantically broken
        The warning must fire at expression evaluation time.
        Resolving the buggy filter raises TypeError because magic_filter internally
        tries to evaluate str | str — demonstrating why the warning matters.
        """
        with pytest.warns(UserWarning, match="Possible operator precedence mistake"):
            # fmt: off
            buggy_filter = F.text == "confirm" | F.text == "cancel"
            # fmt: on
        # The result is still a MagicFilter object (runtime behaviour preserved)
        assert isinstance(buggy_filter, MagicFilter)
        # Resolving raises TypeError: the expression is semantically broken
        with pytest.raises(TypeError):
            buggy_filter.resolve(MyObject(text="confirm"))

    def test_correct_or_pattern_matches(self):
        """Sanity check: the correctly parenthesised form resolves as expected."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            good_filter = (F.text == "confirm") | (F.text == "cancel")
        assert good_filter.resolve(MyObject(text="confirm"))
        assert good_filter.resolve(MyObject(text="cancel"))
        assert not good_filter.resolve(MyObject(text="other"))

    # --- false-positive guard tests (must never warn) ---

    def test_ror_filter_no_warning(self):
        """__ror__ between two MagicFilter instances must NOT emit any warning."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            result = (F.text == "a") | (F.text == "b")
        assert isinstance(result, MagicFilter)

    def test_rand_filter_no_warning(self):
        """__rand__ between two MagicFilter instances must NOT emit any warning."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            result = (F.text == "a") & (F.caption == "b")
        assert isinstance(result, MagicFilter)

    def test_or_truthy_no_warning(self):
        """F.text | F.caption (truthy OR) must NOT emit any warning."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            result = F.text | F.caption
        assert isinstance(result, MagicFilter)

    def test_prebuilt_filter_or_no_warning(self):
        """Pre-built filter variables joined with | must NOT emit any warning."""
        f1 = F.text == "a"
        f2 = F.text == "b"
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            result = f1 | f2
        assert isinstance(result, MagicFilter)

    def test_prebuilt_filter_and_no_warning(self):
        """Pre-built filter variables joined with & must NOT emit any warning."""
        f1 = F.text == "a"
        f2 = F.caption == "b"
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            result = f1 & f2
        assert isinstance(result, MagicFilter)

    def test_chained_or_three_no_warning(self):
        """Chained (f1 | f2 | f3) must NOT emit any warning."""
        f1 = F.text == "a"
        f2 = F.text == "b"
        f3 = F.text == "c"
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            result = f1 | f2 | f3
        assert isinstance(result, MagicFilter)

    def test_mixed_and_or_no_warning(self):
        """(F.x == v) & (F.y == v) | (F.z == v) must NOT emit any warning."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            result = (F.text == "a") & (F.caption == "b") | (F.text == "c")
        assert isinstance(result, MagicFilter)

    def test_filter_and_subfilter_no_warning(self):
        """F.x & (F.y == v) must NOT emit any warning."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            result = F.text & (F.caption == "b")
        assert isinstance(result, MagicFilter)

    def test_negation_no_warning(self):
        """~F.x must NOT emit any warning."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            result = ~F.text
        assert isinstance(result, MagicFilter)

    def test_in_no_warning(self):
        """F.x.in_({...}) must NOT emit any warning."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            result = F.text.in_({"a", "b", "c"})
        assert isinstance(result, MagicFilter)
