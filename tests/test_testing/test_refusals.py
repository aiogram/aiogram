import ast
import re
import string
from pathlib import Path

import pytest

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramConflictError,
    TelegramForbiddenError,
    TelegramNotFound,
    TelegramRetryAfter,
    TelegramUnauthorizedError,
)
from aiogram.methods import SendMessage
from aiogram.test import ApiRejection, refusals
from aiogram.test.errors import raise_api_error
from aiogram.test.overrides import default_message
from aiogram.test.refusals import GUARANTEED, REFUSALS, Refusal

from .conftest import EXCEPTION_FOR_CODE

ROOT = Path(__file__).parents[2]

#: The texts a bot may match on. Growing this list is a promise made to
#: every bot, so it changes here, in the docs, and nowhere by accident.
GUARANTEED_NAMES = {
    "BOT_BLOCKED",
    "BOT_KICKED",
    "BOT_NOT_A_MEMBER",
    "ENTITIES",
    "FLOOD",
    "MESSAGE_TO_DELETE_NOT_FOUND",
    "MESSAGE_TO_EDIT_NOT_FOUND",
    "QUERY_TOO_OLD",
    "REPLY_NOT_FOUND",
    "THREAD_NOT_FOUND",
}


def fields_of(refusal: Refusal) -> dict[str, object]:
    names = [name for _, name, _, _ in string.Formatter().parse(refusal.text) if name]
    return dict.fromkeys(names, "x")


class TestTheContract:
    @pytest.mark.parametrize("name", sorted(REFUSALS))
    async def test_every_refusal_becomes_the_exception_of_its_code(self, env, name):
        refusal = REFUSALS[name]
        retry_after = 7 if refusal.error_code == 429 else None
        rejection = refusal(retry_after=retry_after, **fields_of(refusal))

        with pytest.raises(EXCEPTION_FOR_CODE[refusal.error_code]) as raised:
            env.fail(
                SendMessage(chat_id=1, text="hi"),
                rejection.prefixed,
                rejection.error_code,
                rejection.retry_after,
            )

        assert rejection.refusal is refusal
        if retry_after is None:
            assert raised.value.message == rejection.prefixed
        else:
            assert raised.value.retry_after == retry_after

    @pytest.mark.parametrize(
        ("error_code", "prefix"),
        [(400, "Bad Request"), (403, "Forbidden"), (429, "Too Many Requests")],
    )
    def test_the_prefix_names_the_code(self, error_code, prefix):
        retry_after = 3 if error_code == 429 else None
        rejection = ApiRejection("nope", error_code=error_code, retry_after=retry_after)

        assert rejection.prefixed == f"{prefix}: nope"

    @pytest.mark.parametrize("error_code", [200, 401, 404, 409, 500])
    def test_a_code_with_no_matching_type_is_refused(self, error_code):
        with pytest.raises(ValueError, match="400, a 403 or a 429"):
            ApiRejection("nope", error_code=error_code)

    def test_a_flood_carries_how_long_to_wait(self):
        with pytest.raises(ValueError, match="carries retry_after"):
            ApiRejection("nope", error_code=429)

    def test_only_a_flood_carries_how_long_to_wait(self):
        with pytest.raises(ValueError, match="carries retry_after"):
            ApiRejection("nope", retry_after=3)

    @pytest.mark.parametrize(
        ("error_code", "retry_after"),
        [(429, None), (400, 3), (403, 3)],
    )
    async def test_the_session_error_keeps_the_same_rule(self, env, error_code, retry_after):
        with pytest.raises(ValueError, match="carries retry_after"):
            raise_api_error(
                env.session,
                env.bot,
                SendMessage(chat_id=1, text="hi"),
                "nope",
                error_code,
                retry_after,
            )

    @pytest.mark.parametrize(
        ("error_code", "expected"),
        [
            (401, TelegramUnauthorizedError),
            (404, TelegramNotFound),
            (409, TelegramConflictError),
        ],
    )
    async def test_other_statuses_stay_available_to_the_session(self, env, error_code, expected):
        with pytest.raises(expected):
            raise_api_error(
                env.session,
                env.bot,
                SendMessage(chat_id=1, text="hi"),
                "nope",
                error_code,
            )


class TestTheRegistry:
    def test_the_guaranteed_texts_are_the_listed_ones(self):
        assert {name for name, refusal in REFUSALS.items() if refusal.guaranteed} == (
            GUARANTEED_NAMES
        )
        assert set(GUARANTEED) == {REFUSALS[name] for name in GUARANTEED_NAMES}

    def test_a_guaranteed_text_cites_its_source(self):
        for refusal in GUARANTEED:
            assert refusal.sourced, refusal.text
        with pytest.raises(ValueError, match="cites no source"):
            Refusal("made up", guaranteed=True)

    def test_a_text_that_cites_nothing_is_best_effort(self):
        approximate = [r for r in REFUSALS.values() if not r.sourced]

        assert approximate
        assert not any(refusal.guaranteed for refusal in approximate)

    def test_the_names_are_module_attributes(self):
        for name, refusal in REFUSALS.items():
            assert getattr(refusals, name) is refusal

    def test_a_text_without_fields_is_not_formatted(self):
        refusal = Refusal("it's {braced}")

        assert refusal().description == "it's {braced}"

    def test_only_this_package_builds_a_rejection_from_a_literal(self):
        allowed = {"errors.py", "refusals.py"}
        offenders = []
        for path in sorted((ROOT / "aiogram" / "test").glob("*.py")):
            if path.name in allowed:
                continue
            for node in ast.walk(ast.parse(path.read_text())):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "ApiRejection"
                ):
                    offenders.append(f"{path.name}:{node.lineno}")

        assert not offenders, "declare these in aiogram/test/refusals.py"

    def test_the_documentation_lists_exactly_the_guaranteed_texts(self):
        docs = (ROOT / "docs" / "dispatcher" / "testing.rst").read_text()
        heading = "Refusals and error codes\n========================\n"
        section = docs.split(heading)[1].split("\nOverriding results")[0]
        listed = set(re.findall(r"^\* ``([^`]+)``$", section, re.M))

        shown = {re.sub(r"\{[^}]*\}", "…", refusal.text) for refusal in GUARANTEED}

        assert listed == shown


class TestRaisesWithoutAMessage:
    @pytest.mark.parametrize(
        ("error", "text"),
        [
            (TelegramBadRequest, "Bad Request: test error"),
            (TelegramForbiddenError, "Forbidden: test error"),
            (TelegramNotFound, "Not Found: test error"),
            (TelegramUnauthorizedError, "Unauthorized: test error"),
            (TelegramConflictError, "Conflict: test error"),
        ],
    )
    async def test_the_text_wears_the_prefix_of_the_type(self, env, error, text):
        env.on(SendMessage).raises(error)

        with pytest.raises(error, match=f"^Telegram server says - {text}$"):
            await env.bot.send_message(chat_id=1, text="hi")

    def test_an_unmapped_type_falls_back_to_a_bad_request(self):
        error = TelegramRetryAfter(
            method=SendMessage(chat_id=1, text="hi"),
            message="Too Many Requests: retry after 5",
            retry_after=5,
        )

        assert default_message(error) == "Bad Request: test error"

    async def test_a_message_given_is_kept(self, env):
        env.on(SendMessage).raises(TelegramForbiddenError, "Forbidden: kept")

        with pytest.raises(TelegramForbiddenError, match="Forbidden: kept"):
            await env.bot.send_message(chat_id=1, text="hi")
