import datetime

import pytest

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus, ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.methods import GetChatAdministrators, GetChatMember, SendMessage
from aiogram.test import DELIVERY_METHODS, Blueprint, BotTestEnvironment
from aiogram.test.overrides import fresh_result
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


@pytest.fixture
def party():
    """A group and three players, the shape every targeting test below needs."""
    blueprint = Blueprint()
    players = [blueprint.add_user(name) for name in ("Alice", "Bob", "Carol")]
    for player in players:
        blueprint.add_private_chat(player)
    blueprint.add_supergroup("Table", members=dict.fromkeys(players, ChatMemberStatus.MEMBER))
    return blueprint


@pytest.fixture
def table(party):
    environment = BotTestEnvironment(blueprint=party)
    try:
        yield environment
    finally:
        environment.dispose_sync()


class TestTargetedOverrides:
    """
    An override addressed to a chat, which is what makes a multi-recipient bot testable.

    The motivating report: a game engine messages the group and every player from one
    trigger, so ``env.on(SendMessage).raises(times=1)`` hit whichever call the engine
    happened to make first. Testing "this player blocked the bot" meant reordering the
    production code so the blocked player is served first, and testing *two* blocked
    players was not expressible at all.
    """

    async def test_two_different_chats_are_blocked_at_once(self, table, party):
        alice, bob, carol = (table.chat(user.id) for user in party.users)
        group = table.chat(party.chats[-1].id)
        table.on(SendMessage, chat_id=alice.id).raises(TelegramForbiddenError, "blocked A")
        table.on(SendMessage, chat_id=bob.id).raises(TelegramForbiddenError, "blocked B")

        with pytest.raises(TelegramForbiddenError, match="blocked A"):
            await table.bot.send_message(chat_id=alice.id, text="hi")
        # The group is messaged in between, and consumes neither rule.
        assert (await table.bot.send_message(chat_id=group.id, text="round 1")).text == "round 1"
        with pytest.raises(TelegramForbiddenError, match="blocked B"):
            await table.bot.send_message(chat_id=bob.id, text="hi")
        assert (await table.bot.send_message(chat_id=carol.id, text="hi")).text == "hi"

    async def test_a_mismatching_rule_is_not_consumed(self, table, party):
        """
        The property the whole redesign rests on: a rule the call does not match is
        skipped without its ``times`` budget moving, so an earlier message to somebody
        else cannot use it up.
        """
        alice, bob, _ = (table.chat(user.id) for user in party.users)
        table.on(SendMessage, chat_id=alice.id).raises(TelegramForbiddenError, times=1)

        await table.bot.send_message(chat_id=bob.id, text="not you")
        await table.bot.send_message(chat_id=bob.id, text="still not you")

        with pytest.raises(TelegramForbiddenError):
            await table.bot.send_message(chat_id=alice.id, text="you")

    async def test_several_field_filters_are_anded(self, env, private, team):
        env.on(SendMessage, chat_id=private.id, text="secret").returns("caught")

        assert await env.bot.send_message(chat_id=private.id, text="secret") == "caught"
        assert (await env.bot.send_message(chat_id=team.id, text="secret")).text == "secret"
        assert (await env.bot.send_message(chat_id=private.id, text="other")).text == "other"

    async def test_filters_are_matched_against_the_resolved_method(self, blueprint, dp, private):
        """
        Defaults are filled in before an override is consulted, so a filter names the call
        the API would have seen rather than the one the handler literally wrote.
        """
        blueprint.default = DefaultBotProperties(parse_mode=ParseMode.HTML)
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            environment.on(SendMessage, parse_mode=ParseMode.HTML).returns("caught")

            assert await environment.bot.send_message(chat_id=private.id, text="hi") == "caught"
        finally:
            environment.dispose_sync()

    async def test_where_narrows_by_an_arbitrary_predicate(self, env, private):
        env.on(SendMessage).where(lambda call: "night" in (call.text or "")).returns("caught")

        assert await env.bot.send_message(chat_id=private.id, text="night falls") == "caught"
        assert (await env.bot.send_message(chat_id=private.id, text="dawn")).text == "dawn"

    async def test_where_and_field_filters_compose(self, env, private, team):
        env.on(SendMessage, chat_id=private.id).where(lambda call: call.text == "x").returns("hit")

        assert await env.bot.send_message(chat_id=private.id, text="x") == "hit"
        assert (await env.bot.send_message(chat_id=team.id, text="x")).text == "x"

    async def test_a_predicate_applies_only_to_what_is_declared_after_it(self, env, private):
        """
        Each outcome keeps the matcher in force when it was declared, so narrowing a
        builder between two declarations does not retroactively narrow the first.
        """
        builder = env.on(SendMessage).returns("wide", times=1)
        builder.where(lambda call: call.text == "narrow").returns("narrow", times=1)

        assert await env.bot.send_message(chat_id=private.id, text="anything") == "wide"
        assert await env.bot.send_message(chat_id=private.id, text="narrow") == "narrow"

    async def test_rules_are_tried_in_registration_order(self, env, private):
        env.on(SendMessage).returns("general")
        env.on(SendMessage, chat_id=private.id).returns("specific")

        assert await env.bot.send_message(chat_id=private.id, text="hi") == "general"

    def test_a_filter_on_an_unknown_field_is_refused(self, env):
        with pytest.raises(TypeError, match="has no field\\(s\\) chat_di"):
            env.on(SendMessage, chat_di=1)

    def test_the_refusal_names_the_fields_that_do_exist(self, env):
        with pytest.raises(TypeError, match="known fields: .*chat_id"):
            env.on(SendMessage, chat_di=1)

    def test_a_matcher_describes_itself(self, env, private):
        plain = env.on(SendMessage).matcher()
        narrowed = env.on(SendMessage, chat_id=private.id).where(_is_night).matcher()

        assert plain.describe() == "SendMessage"
        assert narrowed.describe() == f"SendMessage(chat_id={private.id!r}, where(_is_night))"


def _is_night(call):
    return "night" in (call.text or "")


class TestOverrideHandles:
    async def test_cancel_withdraws_only_its_own_rules(self, env, private, team):
        cancelled = env.on(SendMessage, chat_id=private.id).raises(TelegramForbiddenError)
        env.on(SendMessage, chat_id=team.id).raises(TelegramForbiddenError, "kept")

        cancelled.cancel()

        assert (await env.bot.send_message(chat_id=private.id, text="hi")).text == "hi"
        with pytest.raises(TelegramForbiddenError, match="kept"):
            await env.bot.send_message(chat_id=team.id, text="hi")

    async def test_cancel_is_idempotent(self, env, private):
        handle = env.on(SendMessage).raises(TelegramForbiddenError)

        handle.cancel()
        handle.cancel()

        assert (await env.bot.send_message(chat_id=private.id, text="hi")).text == "hi"

    async def test_cancelling_an_already_spent_rule_is_not_an_error(self, env, private):
        handle = env.on(SendMessage).returns("once", times=1)
        assert await env.bot.send_message(chat_id=private.id, text="hi") == "once"

        handle.cancel()

        assert handle.rules  # it still remembers what it declared
        assert env.overrides.rules == []

    async def test_a_handle_is_a_context_manager(self, env, private):
        with (
            env.on(SendMessage).raises(TelegramForbiddenError),
            pytest.raises(
                TelegramForbiddenError,
            ),
        ):
            await env.bot.send_message(chat_id=private.id, text="hi")

        assert (await env.bot.send_message(chat_id=private.id, text="hi")).text == "hi"


class TestBlockedSugar:
    """``env.blocked(chat_id=...)`` — the reported scenario, spelled the way it reads."""

    async def test_scoped_block_stops_delivery_and_lifts_on_exit(self, table, party):
        alice = table.chat(party.users[0].id)
        group = table.chat(party.chats[-1].id)

        with table.blocked(chat_id=alice.id):
            with pytest.raises(TelegramForbiddenError, match="bot was blocked by the user"):
                await table.bot.send_message(chat_id=alice.id, text="your role")
            assert (await table.bot.send_message(chat_id=group.id, text="go")).text == "go"

        assert (await table.bot.send_message(chat_id=alice.id, text="again")).text == "again"

    async def test_two_players_can_be_blocked_at_once(self, table, party):
        """The case that was impossible before: the engine's ordering no longer matters."""
        alice, bob, carol = (table.chat(user.id) for user in party.users)

        with table.blocked(chat_id=alice.id), table.blocked(chat_id=bob.id):
            for blocked in (alice, bob):
                with pytest.raises(TelegramForbiddenError):
                    await table.bot.send_message(chat_id=blocked.id, text="your role")
            assert (await table.bot.send_message(chat_id=carol.id, text="role")).text == "role"

    async def test_every_delivery_method_is_blocked_not_only_send_message(self, table, party):
        alice = table.chat(party.users[0].id)
        group = table.chat(party.chats[-1].id)
        posted = await table.bot.send_message(chat_id=group.id, text="announcement")

        with table.blocked(chat_id=alice.id):
            with pytest.raises(TelegramForbiddenError):
                await table.bot.send_photo(chat_id=alice.id, photo="file-id")
            with pytest.raises(TelegramForbiddenError):
                await table.bot.send_chat_action(chat_id=alice.id, action="typing")
            with pytest.raises(TelegramForbiddenError):
                await table.bot.forward_message(
                    chat_id=alice.id,
                    from_chat_id=group.id,
                    message_id=posted.message_id,
                )
            with pytest.raises(TelegramForbiddenError):
                await table.bot.copy_message(
                    chat_id=alice.id,
                    from_chat_id=group.id,
                    message_id=posted.message_id,
                )

    async def test_forwarding_out_of_the_blocked_chat_still_works(self, table, party):
        """A block is about the destination: ``from_chat_id`` is not what it names."""
        alice = table.chat(party.users[0].id)
        group = table.chat(party.chats[-1].id)
        posted = await table.bot.send_message(chat_id=alice.id, text="from Alice")

        with table.blocked(chat_id=alice.id):
            forwarded = await table.bot.forward_message(
                chat_id=group.id,
                from_chat_id=alice.id,
                message_id=posted.message_id,
            )

        assert forwarded.text == "from Alice"

    async def test_the_call_is_still_recorded(self, table, party):
        """
        Recording happens before overrides apply, on purpose — see `handle_call`. It is
        what lets a test assert the bot *tried* to reach the addressee it should have.
        """
        alice = table.chat(party.users[0].id)

        with table.blocked(chat_id=alice.id), pytest.raises(TelegramForbiddenError):
            await table.bot.send_message(chat_id=alice.id, text="your role")

        assert table.calls.last(SendMessage).text == "your role"

    async def test_an_unscoped_block_is_cancelled_by_hand(self, table, party):
        alice = table.chat(party.users[0].id)
        block = table.blocked(chat_id=alice.id)

        with pytest.raises(TelegramForbiddenError):
            await table.bot.send_message(chat_id=alice.id, text="hi")
        block.cancel()

        assert (await table.bot.send_message(chat_id=alice.id, text="hi")).text == "hi"

    async def test_a_block_accepts_a_declaration_rather_than_an_id(self, table, party):
        with table.blocked(chat_id=party.users[0]), pytest.raises(TelegramForbiddenError):
            await table.bot.send_message(chat_id=party.users[0].id, text="hi")

    async def test_the_wording_can_be_replaced(self, table, party):
        alice = table.chat(party.users[0].id)

        with (
            table.blocked(chat_id=alice.id, message="Forbidden: user is deactivated"),
            pytest.raises(TelegramForbiddenError, match="user is deactivated"),
        ):
            await table.bot.send_message(chat_id=alice.id, text="hi")

    def test_the_delivery_set_is_derived_rather_than_hand_kept(self):
        """
        Guards the prefix rule in `overrides`: it must cover the methods a block stops and
        exclude the one ``Send``-prefixed method that addresses no chat.
        """
        names = {method.__name__ for method in DELIVERY_METHODS}

        assert {"SendMessage", "SendPhoto", "SendChatAction"} <= names
        assert {"CopyMessage", "CopyMessages", "ForwardMessage", "ForwardMessages"} <= names
        assert "SendChatJoinRequestWebApp" not in names
        assert "EditMessageText" not in names


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

    async def test_a_deeply_nested_result_is_copied_without_recursion(self, env, private):
        """
        A canned result nests as deep as the test that built it, and copying must follow.

        The mount walk was made iterative precisely for reply chains this long; a copy that
        recursed died on the same shape, with a `RecursionError` from inside the toolkit
        rather than anything the bot under test did.
        """
        chain = Message(
            message_id=1,
            date=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
            chat=Chat(id=1000, type="private"),
            text="0",
        )
        for index in range(1500):
            chain = Message(
                message_id=index + 2,
                date=chain.date,
                chat=Chat(id=1000, type="private"),
                reply_to_message=chain,
            )
        env.on(SendMessage).returns(chain)

        result = await env.bot.send_message(chat_id=private.id, text="ignored")

        assert result is not chain
        assert result.reply_to_message.bot is env.bot
        assert chain.reply_to_message.bot is None

    async def test_the_copy_arrives_already_bound(self, env, private):
        """
        The destination is known where the copy is made, so it is made bound.

        The alternative — copy unbound, then let the session's `mount` walk the whole graph
        to bind it — is a second full walk of something that was just built object by
        object, on a shape that can be thousands of nodes deep.
        """
        env.on(SendMessage).returns(SHARED_ANSWER)

        result = await env.bot.send_message(chat_id=private.id, text="ignored")

        assert result.bot is env.bot
        assert result.chat.bot is env.bot

    async def test_fresh_result_still_hands_out_an_unbound_copy(self, env):
        """The named entry point other modules import; the policy lives in `mounting`."""
        copied = fresh_result(SHARED_ANSWER)

        assert copied is not SHARED_ANSWER
        assert copied.bot is None
        assert copied.model_dump() == SHARED_ANSWER.model_dump()

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
