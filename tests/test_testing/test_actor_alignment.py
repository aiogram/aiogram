"""
Actor triggers produce only updates Telegram would deliver.

One regression test per finding of the audit behind the
``align-actor-triggers-with-bot-api`` change, each refusal raised as a
setup error before anything is dispatched.
"""

import asyncio
import datetime

import pytest

from aiogram.dispatcher.event.bases import CancelHandler, SkipHandler
from aiogram.enums import ChatMemberStatus
from aiogram.methods import AnswerGuestQuery
from aiogram.test import Blueprint, BotTestEnvironment, WorldLookupError
from aiogram.test.modeling import SUBSCRIPTION_PERIOD
from aiogram.types import (
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Location,
    Message,
    MessageOriginUser,
    Update,
    User,
)


def keyboard(*data):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=item, callback_data=item) for item in data]],
    )


async def send_poll(env, chat, **kwargs):
    return await env.bot.send_poll(
        chat_id=chat.id,
        question="Tabs or spaces?",
        options=["Tabs", "Spaces", "Both"],
        is_anonymous=False,
        **kwargs,
    )


class TestClickOnAGivenMessage:
    async def test_a_stale_copy_resolves_to_the_stored_message(self, env, dp, alice, private):
        seen = []

        @dp.callback_query()
        async def clicked(query):
            seen.append(query.message)

        sent = await env.bot.send_message(
            chat_id=private.id, text="step 1", reply_markup=keyboard("next", "back")
        )
        await env.bot.edit_message_text(
            chat_id=private.id,
            message_id=sent.message_id,
            text="step 2",
            reply_markup=keyboard("back"),
        )

        await alice.click("back", message=sent)

        (message,) = seen
        assert message is private.find_message(sent.message_id)
        assert message.text == "step 2"

    async def test_a_button_the_stored_message_lost_is_refused(self, env, dp, alice, private):
        seen = []
        dp.callback_query.register(seen.append)
        sent = await env.bot.send_message(
            chat_id=private.id, text="step 1", reply_markup=keyboard("next")
        )
        await env.bot.edit_message_reply_markup(
            chat_id=private.id, message_id=sent.message_id, reply_markup=keyboard("done")
        )

        with pytest.raises(WorldLookupError, match="edited since"):
            await alice.click("next", message=sent)

        assert seen == []

    async def test_a_button_that_is_not_there_is_refused(self, env, dp, alice, private):
        seen = []
        dp.callback_query.register(seen.append)
        sent = await env.bot.send_message(
            chat_id=private.id, text="menu", reply_markup=keyboard("next")
        )

        with pytest.raises(WorldLookupError, match="carries no button") as failure:
            await alice.click("bogus", message=sent)

        assert "edited since" not in str(failure.value)
        assert seen == []

    async def test_the_users_own_message_is_refused(self, env, alice, private):
        await alice.send("hi")

        with pytest.raises(WorldLookupError, match="carries no button"):
            await alice.click("x", message=private.messages[-1])

    async def test_another_chats_message_is_refused(self, env, alice, team):
        sent = await env.bot.send_message(
            chat_id=team.id, text="menu", reply_markup=keyboard("go")
        )

        with pytest.raises(WorldLookupError, match=r"bind it with `\.in_"):
            await alice.click("go", message=sent)

    async def test_a_deleted_message_is_refused(self, env, alice, private):
        sent = await env.bot.send_message(
            chat_id=private.id, text="menu", reply_markup=keyboard("go")
        )
        await env.bot.delete_message(chat_id=private.id, message_id=sent.message_id)

        with pytest.raises(WorldLookupError, match="does not exist"):
            await alice.click("go", message=sent)


class TestSkippedHandlers:
    async def test_a_skipping_handler_falls_through(self, env, dp, alice):
        @dp.message()
        async def skipping(message):
            raise SkipHandler

        @dp.message()
        async def handling(message):
            return "handled"

        assert await alice.send("hi") == "handled"

        route = env.last_route
        assert route.handler.endswith("handling")
        assert route.exception is None

    async def test_a_skip_with_nothing_after_names_no_handler(self, env, dp, alice):
        @dp.message()
        async def skipping(message):
            raise SkipHandler

        await alice.send("hi")

        route = env.last_route
        assert route.handled is False
        assert route.handler is None
        assert route.router is None
        assert route.exception is None

    async def test_a_cancelling_handler_is_the_one_that_failed(self, env, dp, alice):
        """aiogram catches only `SkipHandler`; a cancel fails the update."""

        @dp.message()
        async def cancelling(message):
            raise CancelHandler

        with pytest.raises(CancelHandler):
            await alice.send("hi")

        route = env.last_route
        assert route.handler.endswith("cancelling")
        assert isinstance(route.exception, CancelHandler)


class TestUserEdits:
    async def test_an_edit_is_dated(self, env, dp, alice, private):
        dp.edited_message.register(lambda message: message.edit_date)
        await alice.send("before")
        await env.advance_time(60)

        edited_at = await alice.edit(private.messages[-1], "after")

        now = int(env.world.now.timestamp())
        assert edited_at == now
        assert private.messages[-1].edit_date == now

    async def test_fields_alone_keep_the_text(self, env, dp, alice, private):
        dp.edited_message.register(lambda message: message.text)
        await alice.send("keep me")

        text = await alice.edit(private.messages[-1], fields={"reply_markup": keyboard("x")})

        assert text == "keep me"
        (row,) = private.messages[-1].reply_markup.inline_keyboard
        assert [button.callback_data for button in row] == ["x"]

    async def test_a_user_cannot_edit_the_bots_message(self, env, dp, alice, private):
        seen = []
        dp.edited_message.register(seen.append)
        sent = await env.bot.send_message(chat_id=private.id, text="mine")

        with pytest.raises(WorldLookupError, match=r"sent by user \d+, not by user"):
            await alice.edit(sent, "hijacked")

        assert private.find_message(sent.message_id).text == "mine"
        assert seen == []

    async def test_a_message_sent_on_behalf_of_a_chat_is_refused(self, env, alice, team):
        stored = team.add_message(
            Message(
                message_id=team.allocate_message_id(),
                date=env.world.now,
                chat=team.as_chat(),
                sender_chat=Chat(id=-100777, type="channel", title="Linked"),
                text="forwarded",
            )
        )

        with pytest.raises(WorldLookupError, match="sent by chat -100777"):
            await alice.in_(team).edit(stored, "changed")

    async def test_a_forward_is_refused(self, env, alice, private):
        origin = MessageOriginUser(
            date=env.now,
            sender_user=User(id=-7, is_bot=False, first_name="Carol"),
        )
        await alice.send("passed on", fields={"forward_origin": origin})

        with pytest.raises(WorldLookupError, match="a forward cannot be edited"):
            await alice.edit(private.messages[-1], "changed")

    async def test_a_message_with_no_sender_is_refused(self, env, alice, team):
        stored = team.add_message(
            Message(
                message_id=team.allocate_message_id(),
                date=env.world.now,
                chat=team.as_chat(),
                text="nobody's",
            )
        )

        with pytest.raises(WorldLookupError, match="sent by no one"):
            await alice.in_(team).edit(stored, "changed")

    async def test_another_chats_message_is_refused(self, env, alice, team):
        await alice.in_(team).send("in the team")

        with pytest.raises(WorldLookupError, match=r"bind it with `\.in_"):
            await alice.edit(team.messages[-1], "changed")

    async def test_an_unknown_message_is_refused(self, env, alice, private):
        await alice.send("hi")
        message = private.messages[-1].model_copy(update={"message_id": 404})

        with pytest.raises(WorldLookupError, match="does not exist"):
            await alice.edit(message, "changed")

    async def test_a_fed_edited_message_replaces_the_stored_one(self, env, dp, alice, private):
        seen = []
        dp.edited_message.register(seen.append)
        await alice.send("before")
        stored = private.messages[-1]
        edited = Message(
            message_id=stored.message_id,
            date=stored.date,
            edit_date=int(env.world.now.timestamp()),
            chat=private.as_chat(),
            from_user=alice.user.as_user(),
            text="after",
        )

        await env.feed(Update(update_id=env.world.next_update_id(), edited_message=edited))

        (message,) = seen
        assert private.find_message(stored.message_id) is message
        assert message.text == "after"
        assert len(private.messages) == 1

    async def test_a_channel_actor_can_edit_the_bots_post(self, dp):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        news = blueprint.add_channel(
            "News",
            members={alice: ChatMemberStatus.CREATOR},
            bot_status=ChatMemberStatus.ADMINISTRATOR,
        )
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            seen = []
            dp.edited_channel_post.register(seen.append)
            post = await environment.bot.send_message(chat_id=news.id, text="by the bot")

            await environment.user(alice).in_(news).edit(post, "by an admin")

            (edited,) = seen
            assert edited.text == "by an admin"
        finally:
            environment.dispose_sync()


class TestDrain:
    async def test_a_caught_failure_is_not_reported(self, env, alice):
        await alice.send("hi")

        async def explode():
            msg = "handled by the bot"
            raise KeyError(msg)

        task = asyncio.create_task(explode())
        with pytest.raises(KeyError):
            await task

        assert await env.drain() == 0

    async def test_a_gathered_failure_is_not_reported(self, env, alice):
        await alice.send("hi")

        async def explode():
            msg = "gathered"
            raise KeyError(msg)

        results = await asyncio.gather(explode(), return_exceptions=True)

        assert isinstance(results[0], KeyError)
        assert await env.drain() == 0

    async def test_an_uncaught_failure_is_still_reported(self, env, alice):
        await alice.send("hi")

        async def explode():
            msg = "nobody looked"
            raise KeyError(msg)

        task = asyncio.create_task(explode())
        await asyncio.sleep(0)
        assert task.done()

        with pytest.raises(Exception, match="nobody looked"):
            await env.drain()


class TestBusinessConnectionOwner:
    @pytest.fixture
    def business(self, dp):
        blueprint = Blueprint()
        owner = blueprint.add_user("Owner")
        customer = blueprint.add_user("Customer")
        blueprint.add_private_chat(owner)
        customer_chat = blueprint.add_private_chat(customer)
        connection = blueprint.add_business_connection(owner)
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            actor = env.user(customer).in_(customer_chat, business=connection)
            yield env, owner, actor
        finally:
            env.dispose_sync()

    async def test_a_customer_bound_actor_names_the_owner(self, business, dp):
        env, owner, actor = business
        seen = []
        dp.business_connection.register(lambda event: seen.append(event.user.id))

        await actor.disable_business_connection()
        await actor.enable_business_connection()

        assert seen == [owner.id, owner.id]


class TestSubscriptionsAndPayments:
    async def test_a_cancelled_subscription_can_be_tested(self, env, dp, alice):
        dp.subscription.register(lambda event: event.state)

        assert await alice.update_subscription("sub-1", state="canceled") == "canceled"
        assert await alice.update_subscription("sub-1", state="failed") == "failed"

    async def test_the_default_state_is_active(self, env, dp, alice):
        dp.subscription.register(lambda event: event.state)

        assert await alice.update_subscription("sub-1") == "active"

    async def test_an_undocumented_state_is_refused(self, env, dp, alice):
        seen = []
        dp.subscription.register(seen.append)

        with pytest.raises(WorldLookupError, match="'state'"):
            await alice.update_subscription("sub-1", state="state")

        assert seen == []

    async def test_a_subscription_payment_carries_its_expiry(self, env, dp, alice):
        dp.message.register(lambda message: message.successful_payment)

        payment = await alice.pay("sub-1", is_subscription=True)

        expires = env.world.now + datetime.timedelta(seconds=SUBSCRIPTION_PERIOD)
        assert payment.is_recurring is True
        assert payment.is_first_recurring is True
        assert payment.subscription_expiration_date == int(expires.timestamp())

    async def test_a_renewal_is_not_the_first_payment(self, env, dp, alice):
        dp.message.register(lambda message: message.successful_payment)
        await alice.pay("sub-1", is_subscription=True)
        await alice.pay("other", is_subscription=True)

        renewal = await alice.pay("sub-1", is_subscription=True)

        assert renewal.is_recurring is True
        assert renewal.is_first_recurring is None
        assert renewal.subscription_expiration_date is not None

    async def test_a_one_off_payment_carries_no_subscription_fields(self, env, dp, alice):
        dp.message.register(lambda message: message.successful_payment)

        payment = await alice.pay("once")

        assert payment.is_recurring is None
        assert payment.is_first_recurring is None
        assert payment.subscription_expiration_date is None


class TestInlineQueryChatType:
    @pytest.fixture
    def chat_types(self, dp):
        seen = []
        dp.inline_query.register(lambda query: seen.append(query.chat_type))
        return seen

    async def test_an_unbound_actor_is_the_sender(self, env, alice, chat_types):
        await alice.inline_query("search")

        assert chat_types == ["sender"]

    async def test_the_actors_own_private_chat_is_the_sender(self, env, alice, chat_types):
        await alice.in_(alice.user.id).inline_query("search")

        assert chat_types == ["sender"]

    async def test_an_inline_query_from_a_group(self, env, alice, team, chat_types):
        await alice.in_(team).inline_query("search")

        assert chat_types == ["supergroup"]

    async def test_fields_override_the_query(self, env, dp, alice):
        seen = []
        dp.inline_query.register(lambda query: seen.append((query.chat_type, query.location)))
        here = Location(latitude=1.5, longitude=2.5)

        await alice.inline_query("search", fields={"chat_type": "private", "location": here})

        ((chat_type, location),) = seen
        assert chat_type == "private"
        assert (location.latitude, location.longitude) == (1.5, 2.5)


class TestVotes:
    @pytest.fixture
    def answers(self, dp):
        seen = []
        dp.poll_answer.register(lambda answer: seen.append(answer.option_ids))
        return seen

    async def test_an_option_the_poll_does_not_have_is_refused(self, env, private, alice, answers):
        sent = await send_poll(env, private)

        with pytest.raises(WorldLookupError, match=r"no option\(s\) \[3\]"):
            await alice.vote(sent.poll.id, [3])
        with pytest.raises(WorldLookupError, match=r"no option\(s\) \[-1\]"):
            await alice.vote(sent.poll.id, [-1])

        assert answers == []

    async def test_two_answers_on_a_single_answer_poll(self, env, private, alice, answers):
        sent = await send_poll(env, private)

        with pytest.raises(WorldLookupError, match="does not allow multiple answers"):
            await alice.vote(sent.poll.id, [0, 1])

        assert answers == []
        assert env.world.poll(sent.poll.id).votes == {}

    async def test_a_multiple_answer_poll_takes_several(self, env, private, alice, answers):
        sent = await send_poll(env, private, allows_multiple_answers=True)

        await alice.vote(sent.poll.id, [0, 2])

        assert answers == [[0, 2]]

    async def test_a_changed_vote_needs_revoting(self, env, private, alice, answers):
        sent = await send_poll(env, private, allows_revoting=False)
        await alice.vote(sent.poll.id, [0])

        with pytest.raises(WorldLookupError, match="does not allow revoting"):
            await alice.vote(sent.poll.id, [1])

        assert answers == [[0]]
        assert env.world.poll(sent.poll.id).votes[alice.user.id] == [0]

    async def test_a_retraction_needs_revoting(self, env, private, alice, answers):
        sent = await send_poll(env, private, allows_revoting=False)
        await alice.vote(sent.poll.id, [0])

        with pytest.raises(WorldLookupError, match="does not allow revoting"):
            await alice.vote(sent.poll.id, [])

        assert answers == [[0]]

    async def test_a_quiz_without_revoting_keeps_its_answer(self, env, private, alice):
        sent = await send_poll(env, private, type="quiz", correct_option_id=1)
        await alice.vote(sent.poll.id, [0])

        with pytest.raises(WorldLookupError, match="does not allow revoting"):
            await alice.vote(sent.poll.id, [1])

    async def test_an_allowed_revote_works(self, env, private, alice, answers):
        sent = await send_poll(env, private, allows_revoting=True)

        await alice.vote(sent.poll.id, [0])
        await alice.vote(sent.poll.id, [1])
        await alice.vote(sent.poll.id, [])

        assert answers == [[0], [1], []]
        assert env.world.poll(sent.poll.id).votes == {}

    async def test_repeating_the_same_vote_is_no_change(self, env, private, alice, answers):
        sent = await send_poll(env, private, allows_revoting=False)

        await alice.vote(sent.poll.id, [0])
        await alice.vote(sent.poll.id, [0])

        assert answers == [[0], [0]]


class TestGuestMessages:
    async def test_the_canonical_guest_handler_works(self, env, dp, alice):
        @dp.guest_message()
        async def guest(message):
            result = InlineQueryResultArticle(
                id="1",
                title="Hi",
                input_message_content=InputTextMessageContent(message_text="hello"),
            )
            await message.answer_guest_query(result=result)
            return message.guest_query_id

        query_id = await alice.guest_message("let me in")

        assert query_id is not None
        assert env.calls.last(AnswerGuestQuery).guest_query_id == query_id

    async def test_guest_query_ids_are_unique(self, env, dp, alice):
        dp.guest_message.register(lambda message: message.guest_query_id)

        first = await alice.guest_message("one")
        second = await alice.guest_message("two")
        inline_id = env.world.next_query_id()

        assert len({first, second, inline_id}) == 3

    async def test_fields_override_the_message(self, env, dp, alice, private):
        dp.guest_message.register(lambda message: message.guest_query_id)

        assert await alice.guest_message("hi", fields={"guest_query_id": "fixed"}) == "fixed"
        assert private.messages[-1].guest_query_id == "fixed"

    async def test_a_fed_guest_message_is_registered(self, env, dp, alice, private):
        dp.guest_message.register(lambda message: None)
        message = Message(
            message_id=50,
            date=env.world.now,
            chat=private.as_chat(),
            from_user=alice.user.as_user(),
            text="from outside",
            guest_query_id="outside",
        )

        await env.feed(Update(update_id=env.world.next_update_id(), guest_message=message))

        assert private.find_message(50) is message
        assert private.last_message_id == 50
