import pytest

from aiogram.methods import GetChatAdministrators, GetMe, SendMessage
from aiogram.test import FakeTelegramSession
from aiogram.test.errors import NoFileContentError
from aiogram.types import Chat, Message, ReplyParameters, User


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


class TestResultsAreMountedToTheBot:
    """
    Results must carry the bot, the way a parsed response does.

    A real session validates every response with ``context={"bot": bot}``, which is what
    makes ``message.delete()`` and friends work on whatever a call returned. Without the
    same treatment here every shortcut on a result would raise "not mounted to a any bot
    instance", and the toolkit would only be usable for methods called on ``bot`` itself.
    """

    async def test_shortcut_on_a_result_reaches_the_world(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        assert message.bot is env.bot
        await message.delete()

        assert private.messages == []

    async def test_answer_shortcut_sends_into_the_same_chat(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        answer = await message.answer("there")

        assert answer.chat.id == private.id
        assert [item.text for item in private.messages] == ["hi", "there"]

    async def test_shortcut_on_an_edit_result_works(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        edited = await message.edit_text("bye")
        # The edit result is mounted too, so it can be edited again in turn.
        again = await edited.edit_text("later")

        assert again.text == "later"
        assert private.messages[-1].text == "later"

    async def test_nested_objects_are_mounted(self, env, private):
        original = await env.bot.send_message(chat_id=private.id, text="hi")

        reply = await env.bot.send_message(
            chat_id=private.id,
            text="re",
            reply_parameters=ReplyParameters(message_id=original.message_id),
        )

        assert reply.reply_to_message is not None
        assert reply.reply_to_message.bot is env.bot
        assert reply.chat.bot is env.bot
        assert reply.from_user.bot is env.bot
        # Nested objects are usable, not merely annotated with a bot.
        await reply.reply_to_message.delete()

        assert [item.message_id for item in private.messages] == [reply.message_id]

    async def test_every_item_of_a_list_result_is_mounted(self, env, team):
        administrators = await env.bot.get_chat_administrators(chat_id=team.id)

        assert administrators
        for member in administrators:
            assert member.bot is env.bot
            assert member.user.bot is env.bot

    async def test_overridden_results_are_mounted(self, env, private, alice):
        override = Message(
            message_id=777,
            date=env.world.next_date(),
            chat=Chat(id=private.id, type="private"),
            from_user=User(id=alice.user.id, is_bot=False, first_name="Alice"),
            text="canned",
        )
        env.on(SendMessage).returns(override)

        message = await env.bot.send_message(chat_id=private.id, text="hi")

        assert message.bot is env.bot
        assert message.chat.bot is env.bot

    async def test_unknown_fields_are_mounted_too(self, env, private, alice):
        """
        Extras stand in for fields a newer Bot API grew.

        ``TelegramObject`` allows extras, so a result may carry objects in fields this
        aiogram release has no annotation for — production binds those as well, because
        the validation context reaches every model it builds.
        """
        nested = Chat(id=private.id, type="private")
        override = Message(
            message_id=778,
            date=env.world.next_date(),
            chat=Chat(id=private.id, type="private"),
            from_user=User(id=alice.user.id, is_bot=False, first_name="Alice"),
            text="canned",
            future_field={"deep": nested},
        )
        env.on(SendMessage).returns(override)

        message = await env.bot.send_message(chat_id=private.id, text="hi")

        assert message.future_field["deep"].bot is env.bot

    async def test_non_model_results_pass_through_unchanged(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        deleted = await env.bot.delete_message(chat_id=private.id, message_id=message.message_id)
        count = await env.bot.get_chat_member_count(chat_id=private.id)

        assert deleted is True
        assert isinstance(count, int)

    async def test_mounting_survives_a_self_referential_result(self, env, private):
        """A cycle in the result graph must not send the walker into recursion."""
        message = await env.bot.send_message(chat_id=private.id, text="hi")
        looping = message.model_copy()
        # `frozen=True` forbids assignment, so plant the cycle in the field storage itself.
        looping.__dict__["pinned_message"] = looping
        assert looping.pinned_message is looping
        env.on(GetChatAdministrators).returns([looping])

        result = await env.bot.get_chat_administrators(chat_id=private.id)

        assert result[0].bot is env.bot


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
