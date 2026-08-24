import pytest

from aiogram.methods import GetMe, SendMessage
from aiogram.test import FakeTelegramSession
from aiogram.test.errors import NoFileContentError


class TestFakeTelegramSession:
    async def test_no_token_is_required(self, env):
        assert env.bot.token == "42:TEST"
        assert isinstance(env.bot.session, FakeTelegramSession)

    async def test_calls_are_answered_from_the_world(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        assert message.chat.id == private.id
        assert private.messages[-1].text == "hi"

    async def test_get_me_returns_the_blueprint_identity(self, env):
        me = await env.bot(GetMe())

        assert me.id == env.blueprint.bot.id
        assert me.is_bot

    async def test_session_tracks_open_state(self, env, private):
        assert env.session.closed is False

        await env.bot.send_message(chat_id=private.id, text="hi")
        assert env.session.closed is False

        await env.session.close()
        assert env.session.closed is True

    async def test_stream_content_refuses_a_url_it_has_no_content_for(self, env):
        """It used to yield ``b""``, which was indistinguishable from an empty file."""
        with pytest.raises(NoFileContentError):
            [chunk async for chunk in env.session.stream_content("http://example.com")]

    async def test_stream_content_serves_registered_content(self, env):
        env.world.files["known-id"] = b"payload"

        chunks = [
            chunk async for chunk in env.session.stream_content("http://example.com/known-id")
        ]

        assert b"".join(chunks) == b"payload"

    async def test_no_network_layer_is_reachable(self, env, private):
        # A real session would need a connector; this one must not have any.
        assert not hasattr(env.session, "_session")

        await env.bot(SendMessage(chat_id=private.id, text="hi"))

        assert env.calls.count(SendMessage) == 1


class TestDisposal:
    async def test_async_dispose_is_idempotent(self, env):
        await env.dispose()
        await env.dispose()

        assert env.session.closed is True

    async def test_sync_dispose_after_async_dispose(self, env):
        await env.dispose()
        env.dispose_sync()

        assert env.session.closed is True

    async def test_context_manager(self, blueprint, dp):
        from aiogram.test import BotTestEnvironment

        async with BotTestEnvironment(blueprint=blueprint, dispatcher=dp) as environment:
            assert environment.session.closed is False

        assert environment.session.closed is True

    async def test_dispatcher_state_is_restored(self, blueprint, dp):
        from aiogram.test import BotTestEnvironment

        original_storage = dp.fsm.storage
        dp.workflow_data["shared"] = "value"

        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        assert dp.fsm.storage is not original_storage
        dp.workflow_data["leaked"] = True
        await environment.dispose()

        assert dp.fsm.storage is original_storage
        assert dp.workflow_data == {"shared": "value"}

    async def test_dispatcher_state_is_restored_even_when_close_fails(self, blueprint, dp):
        from aiogram.test import BotTestEnvironment

        original_storage = dp.fsm.storage
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)

        async def boom():
            raise RuntimeError("storage exploded")

        environment._storage.close = boom

        with pytest.raises(RuntimeError, match="storage exploded"):
            await environment.dispose()

        assert dp.fsm.storage is original_storage
