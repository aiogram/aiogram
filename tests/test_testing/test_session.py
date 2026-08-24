import pytest

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.methods import GetChatAdministrators, GetMe, SendMessage
from aiogram.test import BotTestEnvironment, FakeTelegramSession
from aiogram.test.errors import NoFileContentError
from aiogram.test.mounting import mount
from aiogram.types import (
    Chat,
    ChatPermissions,
    ChatPhoto,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MessageEntity,
    ReplyParameters,
    User,
)


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
        looping.as_(None)
        assert looping.pinned_message is looping
        env.on(GetChatAdministrators).returns([looping])

        result = await env.bot.get_chat_administrators(chat_id=private.id)

        assert result[0].bot is env.bot

    async def test_a_keyboard_on_a_result_is_mounted(self, env, private):
        """The markup and every button in it, not only the message that carries them."""
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )

        message = await env.bot.send_message(chat_id=private.id, text="pick", reply_markup=markup)

        assert message.reply_markup.bot is env.bot
        assert message.reply_markup.inline_keyboard[0][0].bot is env.bot

    async def test_a_keyboard_added_by_an_edit_is_mounted(self, env, private):
        """The edited message is a copy of an already-bound one, so it is easy to miss."""
        message = await env.bot.send_message(chat_id=private.id, text="pick")

        edited = await message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
            ),
        )

        assert edited.bot is env.bot
        assert edited.reply_markup.bot is env.bot
        assert edited.reply_markup.inline_keyboard[0][0].bot is env.bot

    async def test_a_deep_reply_chain_is_mounted_without_recursion(self, env, private):
        """
        The walk must be iterative: a modeled reply chain nests as deep as it is long.

        A recursive walker died at a few hundred replies — a length a chat simulated over
        a whole test can plausibly reach, and a failure that would look like a toolkit
        crash rather than anything the bot under test did.
        """
        chain = Message(
            message_id=1,
            date=env.world.next_date(),
            chat=private.as_chat(),
            text="0",
        )
        for index in range(1500):
            chain = Message(
                message_id=index + 2,
                date=env.world.next_date(),
                chat=private.as_chat(),
                text=str(index + 1),
                reply_to_message=chain,
            )

        mount(chain, env.bot)

        deepest = chain
        while deepest.reply_to_message is not None:
            deepest = deepest.reply_to_message
        assert chain.bot is env.bot
        assert deepest.bot is env.bot

    async def test_a_long_modeled_reply_chain_is_answered(self, env, private):
        """The same depth, built the way a test actually builds it."""
        previous = await env.bot.send_message(chat_id=private.id, text="start")
        for _ in range(1200):
            previous = await env.bot.send_message(
                chat_id=private.id,
                text="re",
                reply_parameters=ReplyParameters(message_id=previous.message_id),
            )

        assert previous.bot is env.bot
        assert previous.reply_to_message.bot is env.bot


class TestTheWorldOwnsWhatItStores:
    """
    Everything is bound the moment it enters the world, and stays bound to its owner.

    Binding at storage time is what makes the world's own objects usable — a message a
    *user* sent never passes through a result, so nothing else would ever bind it — and
    the ownership rule is what keeps a second bot sharing the session from stealing them.
    """

    async def test_a_message_a_user_sent_is_bound(self, env, alice, private):
        await alice.send("hello")

        stored = private.messages[-1]
        assert stored.bot is env.bot
        # The shortcut is the point: unbound, this raises "not mounted to any bot".
        answer = await stored.answer("hi")

        assert [item.text for item in private.messages] == ["hello", "hi"]
        assert answer.reply_to_message is None

    async def test_a_handler_receives_the_world_s_own_message(self, env, dp, alice, private):
        """
        Not a copy of it: identity is the whole reason the update is mounted before it is
        fed. A dispatcher re-mounts an update built for another bot by round-tripping it
        through JSON, and a handler would then hold a twin of the stored message.
        """
        seen = {}

        @dp.message()
        async def handler(message):
            seen["message"] = message

        await alice.send("hello")

        assert seen["message"] is private.messages[-1]
        assert seen["message"].bot is env.bot

    async def test_a_service_message_nobody_returned_is_bound(self, env, team):
        """`setChatTitle` posts a service message the result never carries."""
        await env.bot.set_chat_title(chat_id=team.id, title="Renamed")

        service = team.messages[-1]
        assert service.new_chat_title == "Renamed"
        assert service.bot is env.bot
        assert service.chat.bot is env.bot

    async def test_a_second_bot_does_not_steal_a_stored_message(self, env, private):
        """
        The documented recipe for a bot that sends through a module-level instance points
        that instance at the same session. Its calls land in the same world — but the
        objects the world already owns stay bound to the environment's bot, or every later
        shortcut on them would silently resolve another bot's defaults.
        """
        other = Bot(
            token="43:OTHER",
            session=env.session,
            default=DefaultBotProperties(parse_mode="MarkdownV2"),
        )

        returned = await other.send_message(chat_id=private.id, text="from the singleton")

        assert returned is private.messages[-1]
        assert returned.bot is env.bot
        # And the defaults that shortcut resolves are still the environment's own.
        await returned.answer("re")
        assert env.calls.last(SendMessage).parse_mode is None

    async def test_a_second_bot_still_gets_its_own_fresh_results_bound(self, env, private):
        other = Bot(token="43:OTHER", session=env.session)

        me = await other.get_me()

        assert me.bot is other


class TestTheCallersObjectsStayTheCallers:
    """
    A request's models belong to the code under test; the world keeps copies of them.

    Storing the caller's own object puts it *in* the world, where it is bound to the bot
    the moment any result carries it back out. A module-level ``reply_markup`` would then
    hold a reference to an environment long after it was disposed, and would stop comparing
    equal to a plainly declared twin, since pydantic counts the binding in ``__eq__`` while
    hiding it from ``__repr__``. This is the outbound twin of what a trigger does with the
    fields a test hands it.
    """

    async def test_a_reply_markup_constant_is_not_captured(self, env, private):
        button = InlineKeyboardButton(text="Go", callback_data="go")
        markup = InlineKeyboardMarkup(inline_keyboard=[[button]])

        message = await env.bot.send_message(chat_id=private.id, text="pick", reply_markup=markup)

        assert message.reply_markup is not markup
        assert message.reply_markup.inline_keyboard[0][0] is not button
        assert markup.bot is None
        assert button.bot is None
        # ...and the constant still compares equal to a freshly declared twin.
        assert markup == InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )

    async def test_entities_are_not_captured(self, env, private):
        entity = MessageEntity(type="bold", offset=0, length=4)

        await env.bot.send_message(chat_id=private.id, text="bold", entities=[entity])

        assert private.messages[-1].entities[0] is not entity
        assert entity.bot is None

    async def test_an_edit_does_not_capture_its_markup(self, env, private):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )
        message = await env.bot.send_message(chat_id=private.id, text="pick")

        await env.bot.edit_message_reply_markup(
            chat_id=private.id,
            message_id=message.message_id,
            reply_markup=markup,
        )

        assert private.messages[-1].reply_markup is not markup
        assert markup.bot is None

    async def test_a_disposed_environment_is_not_kept_alive_by_a_constant(self, blueprint, dp):
        """The reason it matters beyond equality: constants outlive environments."""
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )

        for _ in range(2):
            environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
            await environment.bot.send_message(
                chat_id=blueprint.chats[0].id,
                text="pick",
                reply_markup=markup,
            )
            await environment.dispose()

        assert markup.bot is None


class TestTheWorldsValueObjectsStayTheWorlds:
    """
    A result carries copies of the value objects the world stores, never the objects.

    The result is mounted to the calling bot, so handing out the stored object binds the
    world's own state — and a test asserting ``chat.permissions == DECLARED`` then fails
    with two identical-looking sides. Messages are the deliberate exception: a returned
    message *is* the one the chat holds, and that identity is a feature.
    """

    async def test_get_chat_does_not_hand_out_the_stored_permissions(self, env, team):
        permissions = ChatPermissions(can_send_messages=True)
        await env.bot.set_chat_permissions(chat_id=team.id, permissions=permissions)

        full = await env.bot.get_chat(chat_id=team.id)

        assert full.permissions is not team.permissions
        assert team.permissions.bot is None
        assert team.permissions == permissions

    async def test_get_chat_does_not_hand_out_the_stored_photo(self, env, blueprint, dp):
        photo = ChatPhoto(
            small_file_id="s",
            small_file_unique_id="su",
            big_file_id="b",
            big_file_unique_id="bu",
        )
        blueprint.chats[1].photo = photo
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            full = await environment.bot.get_chat(chat_id=blueprint.chats[1].id)

            assert full.photo is not environment.chat(blueprint.chats[1].id).photo
            assert environment.chat(blueprint.chats[1].id).photo.bot is None
        finally:
            environment.dispose_sync()

    async def test_a_returned_message_is_still_the_stored_one(self, env, private):
        """The exception, stated as a test so the copying does not spread to messages."""
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        assert message is private.messages[-1]


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
