import ast
import re
import string
from pathlib import Path

import pytest

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramConflictError,
    TelegramForbiddenError,
    TelegramMigrateToChat,
    TelegramNotFound,
    TelegramRetryAfter,
    TelegramUnauthorizedError,
)
from aiogram.methods import SendMessage
from aiogram.test import ApiRejection, rejections
from aiogram.test.errors import raise_api_error
from aiogram.test.overrides import default_message
from aiogram.test.rejections import (
    ALL,
    GUARANTEED,
    Rejection,
    rejection_fields,
    rejection_of,
)

from .conftest import EXCEPTION_FOR_CODE

ROOT = Path(__file__).parents[2]

#: The texts a bot may match on. Growing this list is a promise made to
#: every bot, so it changes here, in the docs, and nowhere by accident.
GUARANTEED_NAMES = {
    "BOT_BLOCKED",
    "BOT_KICKED",
    "BOT_NOT_A_MEMBER",
    "CANT_PARSE_ENTITIES",
    "FLOOD",
    "MESSAGE_TO_DELETE_NOT_FOUND",
    "MESSAGE_TO_EDIT_NOT_FOUND",
    "QUERY_TOO_OLD",
    "MESSAGE_TO_BE_REPLIED_NOT_FOUND",
    "MESSAGE_THREAD_NOT_FOUND",
    "TOPIC_CLOSED",
    "TOPIC_DELETED",
}


def fields_of(rejection: Rejection) -> dict[str, object]:
    names = [name for _, name, _, _ in string.Formatter().parse(rejection.description) if name]
    return dict.fromkeys(names, "x")


def raised_from(env, rejection: Rejection, **fields):
    """The ApiRejection of ``rejection`` and what a call fails with."""
    retry_after = 7 if rejection.error_code == 429 else None
    api = rejection(retry_after=retry_after, **(fields or fields_of(rejection)))
    with pytest.raises(EXCEPTION_FOR_CODE[rejection.error_code]) as raised:
        env.fail(
            SendMessage(chat_id=1, text="hi"),
            api.prefixed,
            api.error_code,
            api.retry_after,
        )
    return api, raised.value


class TestTheContract:
    @pytest.mark.parametrize("name", sorted(ALL))
    async def test_every_rejection_becomes_the_exception_of_its_code(self, env, name):
        rejection = ALL[name]

        api, error = raised_from(env, rejection)

        assert api.rejection is rejection
        if api.retry_after is None:
            assert error.message == api.prefixed
        else:
            assert error.retry_after == api.retry_after

    @pytest.mark.parametrize(
        ("error_code", "prefix"),
        [
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (403, "Forbidden"),
            (404, "Not Found"),
            (409, "Conflict"),
            (413, "Request Entity Too Large"),
            (429, "Too Many Requests"),
            (500, "Internal Server Error"),
            (418, "I'm a Teapot"),
            (599, "Error"),
        ],
    )
    def test_the_prefix_names_the_code(self, error_code, prefix):
        retry_after = 3 if error_code == 429 else None
        api = ApiRejection("nope", error_code=error_code, retry_after=retry_after)

        assert api.prefixed == f"{prefix}: nope"

    def test_a_flood_carries_how_long_to_wait(self):
        with pytest.raises(ValueError, match="carries retry_after"):
            ApiRejection("nope", error_code=429)

    @pytest.mark.parametrize("error_code", [400, 403, 404, 500])
    def test_only_a_flood_carries_how_long_to_wait(self, error_code):
        with pytest.raises(ValueError, match="carries retry_after"):
            ApiRejection("nope", error_code=error_code, retry_after=3)

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


class TestNamingTheRejection:
    @pytest.mark.parametrize("name", sorted(ALL))
    async def test_a_caught_exception_names_its_rejection(self, env, name):
        rejection = ALL[name]

        api, error = raised_from(env, rejection)

        assert rejection_of(api) is rejection
        assert rejection_of(error) is rejection
        assert rejection_fields(error) == rejection_fields(api) == fields_of(rejection)

    async def test_a_flood_is_named_through_aiograms_rewording(self, env):
        _api, error = raised_from(env, rejections.FLOOD)

        assert "Original description" in error.message
        assert rejection_of(error) is rejections.FLOOD
        assert rejection_fields(error) == {"seconds": "x"}

    def test_a_migration_is_named_through_its_rewording(self):
        error = TelegramMigrateToChat(
            method=SendMessage(chat_id=1, text="hi"),
            message="Bad Request: bot was kicked from the group chat",
            migrate_to_chat_id=-100,
        )

        assert rejection_of(error) is rejections.BOT_KICKED
        assert rejection_fields(error) == {"noun": "group"}

    def test_an_api_rejection_answers_with_the_one_it_came_from(self):
        api = rejections.MESSAGE_CANT_BE_DELETED()

        assert rejection_of(api) is rejections.MESSAGE_CANT_BE_DELETED

    def test_a_rejection_that_fits_no_declaration_names_none(self):
        assert rejection_of(ApiRejection("made up")) is None
        assert rejection_fields(ApiRejection("made up")) == {}

    def test_a_declaration_does_not_vouch_for_other_wording(self):
        api = ApiRejection("made up", rejection=rejections.MESSAGE_CANT_BE_DELETED)

        assert rejection_of(api) is None

    def test_no_two_descriptions_read_alike(self):
        for name, rejection in ALL.items():
            found = [
                other
                for other in ALL
                if rejections._PATTERNS[ALL[other]].fullmatch(
                    rejection.format(**fields_of(rejection))
                )
            ]
            assert found == [name], f"{name} reads like {found}"


class TestTheRegistry:
    def test_the_guaranteed_descriptions_are_the_listed_ones(self):
        assert {name for name, rejection in ALL.items() if rejection.guaranteed} == (
            GUARANTEED_NAMES
        )
        assert set(GUARANTEED) == {ALL[name] for name in GUARANTEED_NAMES}

    def test_a_guaranteed_description_cites_its_source(self):
        for rejection in GUARANTEED:
            assert rejection.sourced, rejection.description
        with pytest.raises(ValueError, match="cites no source"):
            Rejection("made up", guaranteed=True)

    def test_a_description_that_cites_nothing_is_best_effort(self):
        approximate = [r for r in ALL.values() if not r.sourced]

        assert approximate
        assert not any(rejection.guaranteed for rejection in approximate)

    def test_the_names_are_module_attributes(self):
        for name, rejection in ALL.items():
            assert getattr(rejections, name) is rejection

    def test_a_description_without_fields_is_not_formatted(self):
        rejection = Rejection("it's {braced}")

        assert rejection().description == "it's {braced}"

    def test_only_this_package_builds_a_rejection_from_a_literal(self):
        allowed = {"errors.py", "rejections.py"}
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

        assert not offenders, "declare these in aiogram/test/rejections.py"

    def test_the_documentation_lists_exactly_the_guaranteed_descriptions(self):
        docs = (ROOT / "docs" / "dispatcher" / "testing.rst").read_text()
        heading = "Refusals and error codes\n========================\n"
        section = docs.split(heading)[1].split("\nOverriding results")[0]
        listed = set(re.findall(r"^\* ``([^`]+)``$", section, re.M))

        shown = {re.sub(r"\{[^}]*\}", "…", rejection.description) for rejection in GUARANTEED}

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
