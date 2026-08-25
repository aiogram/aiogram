import pytest

from aiogram.enums import ChatMemberStatus
from aiogram.test import Blueprint, BotTestEnvironment, WorldLookupError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class TestSendReplyTo:
    async def test_reply_to_a_message_object(self, env, private, alice):
        await alice.send("question")
        question = private.messages[-1]

        await alice.send("answer", reply_to=question)

        assert private.messages[-1].reply_to_message is question

    async def test_reply_to_resolves_an_int_through_the_bound_chat(self, env, private, alice):
        await alice.send("question")
        question = private.messages[-1]

        await alice.send("answer", reply_to=question.message_id)

        assert private.messages[-1].reply_to_message is question

    async def test_explicit_fields_reply_to_message_still_wins(self, env, private, alice):
        await alice.send("first")
        first = private.messages[-1]
        await alice.send("second")
        second = private.messages[-1]

        await alice.send("third", reply_to=first, fields={"reply_to_message": second})

        assert private.messages[-1].reply_to_message is second

    async def test_reply_to_an_unknown_id_fails(self, env, private, alice):
        with pytest.raises(WorldLookupError, match="does not exist in chat"):
            await alice.send("orphan reply", reply_to=999)

    async def test_reply_to_is_equivalent_to_the_raw_field(self, env, private, alice):
        """`reply_to` is documented sugar for `fields={"reply_to_message": ...}`."""
        await alice.send("question")
        question = private.messages[-1]

        await alice.send("via keyword", reply_to=question)
        via_keyword = private.messages[-1]
        await alice.send("via raw field", fields={"reply_to_message": question})
        via_field = private.messages[-1]

        assert via_keyword.reply_to_message is via_field.reply_to_message is question


class TestReplySugar:
    async def test_reply_sends_with_reply_to_message_set(self, env, private, alice):
        await alice.send("question")
        question = private.messages[-1]

        await alice.reply(question, "answer")

        assert private.messages[-1].text == "answer"
        assert private.messages[-1].reply_to_message is question

    async def test_reply_accepts_a_message_id(self, env, private, alice):
        await alice.send("question")
        question = private.messages[-1]

        await alice.reply(question.message_id, "answer")

        assert private.messages[-1].reply_to_message is question

    async def test_reply_chains_reach_for_chat_messages(self, two_users):
        """The stored message is `actor.chat.messages[-1]` right after `send()`/`reply()`."""
        alice, bob = two_users
        await alice.send("question")
        question = alice.chat.messages[-1]

        await bob.reply(question, "first reply")
        first_reply = bob.chat.messages[-1]

        await alice.reply(first_reply, "second reply")

        assert alice.chat.messages[-1].reply_to_message is first_reply
        assert first_reply.reply_to_message is question

    async def test_reply_forwards_fields_and_data(self, env, dp, private, alice):
        await alice.send("question")
        question = private.messages[-1]
        seen = []
        dp.message.register(lambda message, marker: seen.append((message.text, marker)))

        await alice.reply(question, "answer", marker="handler-data")

        assert seen[-1] == ("answer", "handler-data")
        assert private.messages[-1].reply_to_message is question


@pytest.fixture
def two_users(dp):
    """
    A group with two members — a reply chain needs two distinct authors, and the shared
    ``blueprint``/``env`` fixtures only declare one user.
    """
    blueprint = Blueprint()
    alice_spec = blueprint.add_user("Alice")
    bob_spec = blueprint.add_user("Bob")
    team = blueprint.add_supergroup(
        "Team",
        members={alice_spec: ChatMemberStatus.MEMBER, bob_spec: ChatMemberStatus.MEMBER},
    )
    environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
    try:
        yield environment.user(alice_spec).in_(team), environment.user(bob_spec).in_(team)
    finally:
        environment.dispose_sync()


class TestClickMisdirectionHint:
    @staticmethod
    def keyboard(data: str = "go") -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data=data)]],
        )

    @pytest.fixture
    def two_chats(self, dp):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        blueprint.add_private_chat(alice)
        team = blueprint.add_supergroup("Team", members={alice: "administrator"})
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            yield environment, environment.user(alice), team
        finally:
            environment.dispose_sync()

    async def test_the_hint_names_the_chat_that_actually_has_the_button(self, two_chats):
        env, alice, team_spec = two_chats
        team = env.chat(team_spec)
        await alice.in_(team_spec).send("pick", fields={"reply_markup": self.keyboard("go")})

        with pytest.raises(WorldLookupError) as excinfo:
            # Forgot `.in_(team)` — clicks the private chat, where the button never was.
            await alice.click("go")

        message = str(excinfo.value)
        assert f"a button with this callback_data exists in chat {team.id}" in message
        assert "'Team'" in message
        assert "bind the actor with `.in_(...)`" in message

    async def test_no_hint_when_the_button_exists_nowhere(self, two_chats):
        env, alice, team_spec = two_chats

        with pytest.raises(WorldLookupError) as excinfo:
            await alice.click("never-existed")

        message = str(excinfo.value)
        assert "callback_data='never-existed'" in message
        assert "exists in chat" not in message

    async def test_the_hint_does_not_fire_for_a_button_in_the_actors_own_chat(self, two_chats):
        """A button genuinely missing from the bound chat gets no false-positive hint."""
        env, alice, team_spec = two_chats
        await alice.send("pick", fields={"reply_markup": self.keyboard("go")})

        with pytest.raises(WorldLookupError) as excinfo:
            await alice.click("missing")

        assert "exists in chat" not in str(excinfo.value)
