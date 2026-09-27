import re
from pathlib import Path

import pytest

from aiogram.methods import SetPassportDataErrors, TelegramMethod
from aiogram.test.modeling import RECORD_ONLY, REGISTRY

MODELING = Path("aiogram/test/modeling.py")


def all_method_types():
    """Every generated Bot API method, from the package's own exports."""
    from aiogram import methods

    return {
        value
        for value in vars(methods).values()
        if isinstance(value, type)
        and issubclass(value, TelegramMethod)
        and value is not TelegramMethod
    }


class TestTheBoundaryIsADecision:
    def test_record_only_and_modeled_do_not_overlap(self):
        """
        The guard for design decision D1.

        This asserts the two sets are disjoint. It is deliberately **not** a completeness
        check over every unmodeled method: a Bot API bump adds methods, and a guard that
        failed on every bump for a list that is documentation would get suppressed rather
        than maintained. Modeling one of these methods is meant to be an edit to both the
        registry and `RECORD_ONLY`, in the same change — that is the failure this catches.
        """
        assert not RECORD_ONLY & set(REGISTRY)

    def test_record_only_names_real_methods(self):
        assert all_method_types() >= RECORD_ONLY

    def test_the_list_is_not_empty(self):
        """A vacuous list would make the overlap assertion pass while guarding nothing."""
        assert len(RECORD_ONLY) > 40

    def test_every_entry_carries_a_reason(self):
        """
        Each entry sits under a comment saying why. The reason is the reusable part —
        a flat list of names answers no questions about the next method.
        """
        source = MODELING.read_text(encoding="utf-8")
        block = re.search(r"RECORD_ONLY: frozenset.*?\n    \},\n\)", source, re.S)
        assert block is not None, "RECORD_ONLY is no longer a literal set this test can read"

        groups = 0
        seen_since_comment = True
        for line in block.group(0).splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                if not seen_since_comment:
                    continue
                groups += 1
                seen_since_comment = False
            elif stripped.endswith(","):
                seen_since_comment = True

        assert groups >= 10, "entries should stay grouped by reason, not flattened"


class TestRecordOnlyMethodsStillWork:
    async def test_a_record_only_method_succeeds_and_is_recorded(self, env, alice):
        """Being on the list changes nothing at runtime — tier three still answers."""
        assert await env.bot.verify_user(user_id=alice.user.id) is True

    async def test_a_record_only_method_returning_an_object_is_synthesized(self, env):
        result = await env.bot.get_webhook_info()

        assert result is not None

    @pytest.mark.parametrize(
        "method_type",
        sorted(RECORD_ONLY, key=lambda item: item.__name__),
        ids=lambda item: item.__name__,
    )
    def test_no_handler_is_registered(self, method_type):
        assert method_type not in REGISTRY

    async def test_an_override_still_wins(self, env, alice):
        """The escape hatch is unaffected: a test that cares declares the outcome."""
        env.on(SetPassportDataErrors).returns(False)

        assert await env.bot.set_passport_data_errors(user_id=alice.user.id, errors=[]) is False
