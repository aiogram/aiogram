import pytest

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramConflictError,
    TelegramForbiddenError,
    TelegramNotFound,
    TelegramServerError,
    TelegramUnauthorizedError,
)
from aiogram.methods import SendMessage
from aiogram.test.errors import raise_api_error


class TestRaiseApiError:
    @pytest.mark.parametrize(
        ("error_code", "expected"),
        [
            (400, TelegramBadRequest),
            (401, TelegramUnauthorizedError),
            (403, TelegramForbiddenError),
            (404, TelegramNotFound),
            (409, TelegramConflictError),
            (500, TelegramServerError),
        ],
    )
    async def test_error_types_match_the_status_code(self, env, error_code, expected):
        method = SendMessage(chat_id=1, text="hi")

        with pytest.raises(expected, match="nope"):
            raise_api_error(
                session=env.session,
                bot=env.bot,
                method=method,
                description="nope",
                error_code=error_code,
            )

    async def test_the_failing_method_is_attached(self, env):
        method = SendMessage(chat_id=1, text="hi")

        with pytest.raises(TelegramBadRequest) as exc_info:
            env.fail(method, "Bad Request: nope")

        assert exc_info.value.method is method


class TestErrorPipeline:
    async def test_error_handler_receives_the_exception(self, env, dp, alice, private):
        seen = []

        @dp.message()
        async def handler(message):
            await message.bot.edit_message_text(
                chat_id=private.id,
                message_id=404,
                text="nope",
            )
            return "not reached"

        @dp.error()
        async def on_error(event):
            seen.append(type(event.exception).__name__)
            return "handled by error handler"

        assert await alice.send("hi") == "handled by error handler"
        assert seen == ["TelegramBadRequest"]

    async def test_handlers_can_catch_the_error_themselves(self, env, dp, alice, private):
        @dp.message()
        async def handler(message):
            try:
                await message.bot.delete_message(chat_id=private.id, message_id=404)
            except TelegramBadRequest as error:
                return str(error)
            return "not reached"  # pragma: no cover

        assert "message to delete not found" in await alice.send("hi")

    async def test_state_is_unchanged_after_a_failed_call(self, env, dp, alice, private):
        env.on(SendMessage).raises(TelegramForbiddenError, "Forbidden: blocked")

        @dp.message()
        async def handler(message):
            try:
                await message.answer("hi")
            except TelegramForbiddenError:
                return "blocked"
            return "not reached"  # pragma: no cover

        before = len(private.messages)

        assert await alice.send("hi") == "blocked"
        assert len(private.messages) == before + 1  # only the user's own message
