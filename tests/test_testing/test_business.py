import pytest

from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SendMessage, SetBusinessAccountName
from aiogram.test import Blueprint, BotTestEnvironment
from aiogram.test.world import WorldLookupError
from aiogram.types import BusinessBotRights


@pytest.fixture
def business_blueprint():
    blueprint = Blueprint()
    owner = blueprint.add_user("Alice", username="alice")
    customer = blueprint.add_user("Bob")
    blueprint.add_private_chat(owner)
    blueprint.add_private_chat(customer)
    blueprint.add_business_connection(
        owner,
        rights=BusinessBotRights(can_reply=True, can_read_messages=True),
    )
    return blueprint


@pytest.fixture
def business_env(business_blueprint, dp):
    environment = BotTestEnvironment(blueprint=business_blueprint, dispatcher=dp)
    try:
        yield environment
    finally:
        environment.dispose_sync()


@pytest.fixture
def connection(business_blueprint):
    return business_blueprint.business_connections[0]


@pytest.fixture
def customer_chat(business_blueprint):
    return business_blueprint.chats[1]


class TestDeclaration:
    def test_connection_is_materialized(self, business_env, connection, business_blueprint):
        state = business_env.business_connection(connection)

        assert state.id == connection.id
        assert state.user_id == business_blueprint.users[0].id
        assert state.is_enabled
        assert state.rights.can_read_messages

    def test_explicit_id(self):
        blueprint = Blueprint()
        owner = blueprint.add_user("Alice")

        assert blueprint.add_business_connection(owner, id="custom").id == "custom"

    def test_connections_do_not_leak_between_environments(self, business_blueprint, dp):
        first = BotTestEnvironment(blueprint=business_blueprint, dispatcher=dp)
        connection_id = business_blueprint.business_connections[0].id
        first.world.business_connection(connection_id).is_enabled = False
        first.dispose_sync()

        second = BotTestEnvironment(blueprint=business_blueprint, dispatcher=dp)
        try:
            assert second.world.business_connection(connection_id).is_enabled is True
        finally:
            second.dispose_sync()

    def test_unknown_connection(self, business_env):
        with pytest.raises(WorldLookupError, match="not declared in the blueprint"):
            business_env.business_connection("missing")

    def test_state_is_accepted_directly(self, business_env, connection):
        state = business_env.business_connection(connection)

        assert business_env.business_connection(state) is state
        assert business_env.business_connection(connection.id) is state


class TestModeledMethods:
    async def test_get_business_connection(self, business_env, connection, business_blueprint):
        result = await business_env.bot.get_business_connection(
            business_connection_id=connection.id,
        )

        assert result.id == connection.id
        assert result.user.id == business_blueprint.users[0].id
        assert result.is_enabled

    async def test_get_unknown_connection_fails(self, business_env):
        """A connection the blueprint never declared is a setup gap, not a Bad Request."""
        with pytest.raises(WorldLookupError, match="not declared in the blueprint"):
            await business_env.bot.get_business_connection(business_connection_id="missing")

    async def test_read_business_message(self, business_env, connection, customer_chat):
        message = await business_env.bot.send_message(
            chat_id=customer_chat.id,
            text="hi",
            business_connection_id=connection.id,
        )

        assert await business_env.bot.read_business_message(
            business_connection_id=connection.id,
            chat_id=customer_chat.id,
            message_id=message.message_id,
        )

    async def test_read_missing_message_fails(self, business_env, connection, customer_chat):
        with pytest.raises(TelegramBadRequest, match="message to read not found"):
            await business_env.bot.read_business_message(
                business_connection_id=connection.id,
                chat_id=customer_chat.id,
                message_id=404,
            )

    async def test_delete_business_messages(self, business_env, connection, customer_chat):
        chat = business_env.chat(customer_chat)
        first = await business_env.bot.send_message(
            chat_id=customer_chat.id,
            text="one",
            business_connection_id=connection.id,
        )
        ordinary = await business_env.bot.send_message(chat_id=customer_chat.id, text="two")

        assert await business_env.bot.delete_business_messages(
            business_connection_id=connection.id,
            message_ids=[first.message_id, ordinary.message_id],
        )

        # Only the message that belongs to the connection is removed.
        assert [item.text for item in chat.messages] == ["two"]

    async def test_account_methods_still_answer_from_synthesis(self, business_env):
        """The business *account* profile surface stays on the synthesize path."""
        result = await business_env.bot.set_business_account_name(
            business_connection_id="anything",
            first_name="Renamed",
        )

        assert result is not None
        assert business_env.calls.count(SetBusinessAccountName) == 1


class TestSenderAttribution:
    async def test_business_send_is_attributed_to_the_account(
        self,
        business_env,
        connection,
        customer_chat,
        business_blueprint,
    ):
        chat = business_env.chat(customer_chat)

        await business_env.bot.send_message(
            chat_id=customer_chat.id,
            text="hi",
            business_connection_id=connection.id,
        )

        stored = chat.messages[-1]
        assert stored.from_user.id == business_blueprint.users[0].id
        assert stored.sender_business_bot.id == business_blueprint.bot.id
        assert stored.business_connection_id == connection.id

    async def test_ordinary_send_is_attributed_to_the_bot(
        self,
        business_env,
        customer_chat,
        business_blueprint,
    ):
        chat = business_env.chat(customer_chat)

        await business_env.bot.send_message(chat_id=customer_chat.id, text="hi")

        stored = chat.messages[-1]
        assert stored.from_user.id == business_blueprint.bot.id
        assert stored.sender_business_bot is None

    async def test_the_outgoing_call_is_recorded_unchanged(
        self,
        business_env,
        connection,
        customer_chat,
    ):
        await business_env.bot.send_message(
            chat_id=customer_chat.id,
            text="hi",
            business_connection_id=connection.id,
        )

        assert business_env.calls.last(SendMessage).business_connection_id == connection.id


class TestTriggers:
    @pytest.fixture
    def actor(self, business_env, business_blueprint, connection, customer_chat):
        return business_env.user(business_blueprint.users[1]).in_(
            customer_chat,
            business=connection,
        )

    async def test_business_message(self, business_env, dp, actor, connection):
        @dp.business_message()
        async def handler(message, event_from_user):
            return message.business_connection_id, event_from_user.id

        result = await actor.send("hello")

        assert result == (connection.id, actor.user.id)

    async def test_edited_business_message(self, business_env, dp, actor, customer_chat):
        @dp.business_message()
        async def created(message):
            return None

        @dp.edited_business_message()
        async def edited(message):
            return message.text

        await actor.send("before")
        original = business_env.chat(customer_chat).messages[-1]

        assert await actor.edit(original, "after") == "after"

    async def test_connection_enabled_and_disabled(self, business_env, dp, actor, connection):
        @dp.business_connection()
        async def handler(event):
            return event.is_enabled

        assert await actor.disable_business_connection() is False
        assert business_env.business_connection(connection).is_enabled is False

        assert await actor.enable_business_connection() is True
        assert business_env.business_connection(connection).is_enabled is True

    async def test_deleted_business_messages(self, business_env, dp, actor, customer_chat):
        @dp.business_message()
        async def created(message):
            return None

        @dp.deleted_business_messages()
        async def deleted(event):
            return event.message_ids

        await actor.send("one")
        chat = business_env.chat(customer_chat)
        message_id = chat.messages[-1].message_id

        assert await actor.delete_business_messages([message_id]) == [message_id]
        assert chat.messages == []

    async def test_deleting_an_unknown_message_is_tolerated(self, business_env, dp, actor):
        @dp.deleted_business_messages()
        async def deleted(event):
            return "seen"

        assert await actor.delete_business_messages([404]) == "seen"

    async def test_triggers_require_a_binding(self, business_env, business_blueprint):
        actor = business_env.user(business_blueprint.users[1])

        with pytest.raises(WorldLookupError, match="not bound to a business connection"):
            await actor.disable_business_connection()

    def test_binding_does_not_mutate_the_source_actor(
        self, business_env, business_blueprint, connection, customer_chat
    ):
        actor = business_env.user(business_blueprint.users[1])

        bound = actor.in_(customer_chat, business=connection)

        assert bound.business.id == connection.id
        assert actor.business is None
