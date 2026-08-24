import datetime

import pytest

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.methods import GetChatAdministrators, GetChatMember, SendMessage
from aiogram.test import BotTestEnvironment
from aiogram.types import Chat, ChatMemberMember, Message, User

#: Declared once and reused by every test below, the way a real suite declares a fixture
#: response — which is exactly the object an override must never hand out by reference.
SHARED_ANSWER = Message(
    message_id=4242,
    date=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    chat=Chat(id=1000, type="private"),
    text="canned",
)


class TestOverrides:
    async def test_returns_wins_over_modeling(self, env, private):
        canned = Message(
            message_id=999,
            date=env.world.next_date(),
            chat=private.as_chat(),
            text="canned",
        )
        env.on(SendMessage).returns(canned)

        result = await env.bot.send_message(chat_id=private.id, text="ignored")

        assert result.message_id == 999
        assert private.messages == []

    async def test_returns_wins_over_synthesis(self, env):
        member = ChatMemberMember(user=User(id=5, is_bot=False, first_name="Fixed"))
        env.on(GetChatMember).returns(member)

        result = await env.bot.get_chat_member(chat_id=12345, user_id=5)

        assert result.user.first_name == "Fixed"

    async def test_raises_an_error_class(self, env, private):
        env.on(SendMessage).raises(TelegramForbiddenError, "Forbidden: bot was blocked")

        with pytest.raises(TelegramForbiddenError, match="bot was blocked"):
            await env.bot.send_message(chat_id=private.id, text="hi")

        assert private.messages == []

    async def test_raises_an_error_instance(self, env, private):
        error = TelegramRetryAfter(
            method=SendMessage(chat_id=private.id, text="hi"),
            message="Too Many Requests",
            retry_after=5,
        )
        env.on(SendMessage).raises(error)

        with pytest.raises(TelegramRetryAfter) as exc_info:
            await env.bot.send_message(chat_id=private.id, text="hi")

        assert exc_info.value.retry_after == 5

    async def test_default_error(self, env, private):
        env.on(SendMessage).raises()

        with pytest.raises(TelegramBadRequest, match="test error"):
            await env.bot.send_message(chat_id=private.id, text="hi")

    async def test_consecutive_outcomes(self, env, private):
        env.on(SendMessage).raises(TelegramBadRequest, "first fails", times=1)

        with pytest.raises(TelegramBadRequest, match="first fails"):
            await env.bot.send_message(chat_id=private.id, text="one")

        message = await env.bot.send_message(chat_id=private.id, text="two")

        assert message.text == "two"

    async def test_times_are_consumed_in_order(self, env, private):
        env.on(SendMessage).returns("first", times=1).returns("second", times=1)

        assert await env.bot.send_message(chat_id=private.id, text="x") == "first"
        assert await env.bot.send_message(chat_id=private.id, text="x") == "second"
        assert isinstance(await env.bot.send_message(chat_id=private.id, text="x"), Message)

    async def test_overrides_do_not_leak_between_environments(self, blueprint, dp, private):
        first = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        first.on(SendMessage).raises(TelegramForbiddenError)
        await first.dispose()

        second = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        chat_id = blueprint.chats[0].id
        message = await second.bot.send_message(chat_id=chat_id, text="hi")
        await second.dispose()

        assert message.text == "hi"

    async def test_overrides_for_other_methods_are_ignored(self, env, private):
        env.on(GetChatMember).returns("unused")

        message = await env.bot.send_message(chat_id=private.id, text="hi")

        assert message.text == "hi"

    async def test_an_already_exhausted_outcome_is_dropped(self, env, private):
        env.on(SendMessage).returns("never", times=0).returns("used", times=1)

        assert await env.bot.send_message(chat_id=private.id, text="hi") == "used"

    def test_registry_can_be_cleared(self, env):
        env.on(SendMessage).returns("x")

        env.overrides.clear()

        assert env.overrides.take(SendMessage(chat_id=1, text="x")) is None


class TestADeclaredResultStaysTheTestsOwn:
    """
    An override hands out a copy, the way a real answer is freshly parsed every time.

    The declared object belongs to the test; the answer belongs to the caller, which
    mounts it to a bot and may go on to edit it. Handing out the declared object itself
    would mutate the test's own — often module-level — object and leave it holding a
    reference to a bot whose environment is long gone.
    """

    async def test_the_declared_object_is_neither_returned_nor_mounted(self, env, private):
        env.on(SendMessage).returns(SHARED_ANSWER)

        result = await env.bot.send_message(chat_id=private.id, text="ignored")

        assert result is not SHARED_ANSWER
        assert result.model_dump() == SHARED_ANSWER.model_dump()
        assert result.bot is env.bot
        assert SHARED_ANSWER.bot is None
        assert SHARED_ANSWER.chat.bot is None

    async def test_every_call_gets_its_own_copy(self, env, private):
        env.on(SendMessage).returns(SHARED_ANSWER)

        first = await env.bot.send_message(chat_id=private.id, text="one")
        second = await env.bot.send_message(chat_id=private.id, text="two")

        assert first is not second
        assert first.chat is not second.chat

    async def test_the_items_of_a_declared_list_are_copied_too(self, env, team):
        member = ChatMemberMember(user=User(id=5, is_bot=False, first_name="Fixed"))
        env.on(GetChatAdministrators).returns([member])

        result = await env.bot.get_chat_administrators(chat_id=team.id)

        assert result[0] is not member
        assert result[0].bot is env.bot
        assert member.bot is None
        assert member.user.bot is None

    async def test_a_declared_tuple_is_copied_item_by_item(self, env, team):
        """Any sequence a test declares, not only the list the real API would send."""
        member = ChatMemberMember(user=User(id=6, is_bot=False, first_name="Tupled"))
        env.on(GetChatAdministrators).returns((member,))

        result = await env.bot.get_chat_administrators(chat_id=team.id)

        assert isinstance(result, tuple)
        assert result[0] is not member
        assert result[0].bot is env.bot
        assert member.bot is None

    async def test_no_bot_leaks_from_one_environment_into_the_next(self, blueprint, dp):
        first = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        first.on(SendMessage).returns(SHARED_ANSWER)
        chat_id = blueprint.chats[0].id
        from_first = await first.bot.send_message(chat_id=chat_id, text="hi")
        await first.dispose()

        second = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        second.on(SendMessage).returns(SHARED_ANSWER)
        from_second = await second.bot.send_message(chat_id=chat_id, text="hi")
        await second.dispose()

        assert SHARED_ANSWER.bot is None
        assert from_first.bot is first.bot
        assert from_second.bot is second.bot
