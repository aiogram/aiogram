import pytest

from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramMigrateToChat,
    TelegramRetryAfter,
)
from aiogram.methods import SendMessage


class TestAClassTheCallCannotBuild:
    def test_retry_after_gets_an_example(self, env):
        with pytest.raises(TypeError) as caught:
            env.on(SendMessage).raises(TelegramRetryAfter)

        text = str(caught.value)
        assert "TelegramRetryAfter cannot be raised from the class" in text
        assert "also needs retry_after" in text
        assert (
            "env.on(SendMessage).raises(TelegramRetryAfter(method=SendMessage(...), "
            'message="Too Many Requests: retry after 5", retry_after=5))'
        ) in text

    def test_migrate_to_chat_gets_an_example(self, env):
        with pytest.raises(TypeError, match="migrate_to_chat_id=-1001234567890"):
            env.on(SendMessage, chat_id=1).raises(TelegramMigrateToChat)

    def test_another_class_is_told_what_it_needs(self, env):
        class Quota(TelegramBadRequest):
            def __init__(self, method, message, units, *, region, spare=0):
                super().__init__(method=method, message=message)

        with pytest.raises(
            TypeError,
            match=r"Quota\(method=SendMessage\(\.\.\.\), message=\.\.\., units=\.\.\., region=\.\.\.\)",
        ):
            env.on(SendMessage).raises(Quota)

    async def test_nothing_is_declared_by_the_refusal(self, env):
        with pytest.raises(TypeError):
            env.on(SendMessage).raises(TelegramRetryAfter)

        sent = await env.bot.send_message(chat_id=1000, text="x")

        assert sent.text == "x"


class TestWhatIsStillAccepted:
    @pytest.mark.parametrize("error", [TelegramBadRequest, TelegramForbiddenError])
    async def test_a_class_taking_the_method_and_message(self, env, error):
        env.on(SendMessage).raises(error, "Boom: x", times=1)

        with pytest.raises(error, match="Boom: x"):
            await env.bot.send_message(chat_id=1000, text="x")

    async def test_an_instance_built_whole(self, env):
        flood = TelegramRetryAfter(
            method=SendMessage(chat_id=1000, text=""),
            message="Too Many Requests: retry after 5",
            retry_after=5,
        )
        env.on(SendMessage).raises(flood, times=1)

        with pytest.raises(TelegramRetryAfter) as caught:
            await env.bot.send_message(chat_id=1000, text="x")

        assert caught.value.retry_after == 5


class TestWhatIsNotAnException:
    @pytest.mark.parametrize("error", ["Bad Request: chat not found", ValueError, 5, None])
    def test_it_is_refused_with_the_usual_spelling(self, env, error):
        with pytest.raises(TypeError, match="takes a TelegramAPIError subclass or an instance"):
            env.on(SendMessage).raises(error)

    def test_the_message_goes_second(self, env):
        with pytest.raises(TypeError, match=r'raises\(TelegramBadRequest, "Bad Request: chat'):
            env.on(SendMessage).raises("Bad Request: chat not found")

    def test_an_instance_of_another_exception_is_refused(self, env):
        with pytest.raises(TypeError, match="takes a TelegramAPIError subclass"):
            env.on(SendMessage).raises(ValueError("x"))
