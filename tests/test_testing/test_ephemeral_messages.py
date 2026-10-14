import pytest

from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import Blueprint, BotTestEnvironment, WorldLookupError
from aiogram.test.errors import WaitTimeoutError
from aiogram.test.world import BASE_DATE
from aiogram.types import (
    BufferedInputFile,
    EphemeralMessageParameters,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputRichBlockParagraph,
    InputRichMessage,
    Message,
    ReplyParameters,
    Update,
)


def keyboard(callback_data="ok"):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="OK", callback_data=callback_data)]],
    )


def to(user, **kwargs):
    return EphemeralMessageParameters(receiver_user_id=user.id, **kwargs)


@pytest.fixture
def world_blueprint():
    blueprint = Blueprint()
    alice = blueprint.add_user("Alice")
    bob = blueprint.add_user("Bob")
    blueprint.add_user("Carol")
    group = blueprint.add_supergroup(
        "Team",
        members={alice: ChatMemberStatus.MEMBER, bob: ChatMemberStatus.MEMBER},
    )
    blueprint.add_topic(group, "Support")
    blueprint.add_private_chat(alice)
    blueprint.add_channel("News")
    blueprint.add_business_connection(alice)
    return blueprint


@pytest.fixture
def env(world_blueprint, dp):
    environment = BotTestEnvironment(blueprint=world_blueprint, dispatcher=dp)
    try:
        yield environment
    finally:
        environment.dispose_sync()


@pytest.fixture
def alice(world_blueprint):
    return world_blueprint.users[0]


@pytest.fixture
def bob(world_blueprint):
    return world_blueprint.users[1]


@pytest.fixture
def team(env, world_blueprint):
    return env.chat(world_blueprint.chats[0])


@pytest.fixture
def private(env, world_blueprint):
    return env.chat(world_blueprint.chats[1])


@pytest.fixture
def channel(env, world_blueprint):
    return env.chat(world_blueprint.chats[2])


@pytest.fixture
def support(world_blueprint):
    return world_blueprint.topics[0]


async def send_to(env, chat, user, text="only you", **kwargs):
    return await env.bot.send_message(
        chat_id=chat.id,
        text=text,
        ephemeral_message_parameters=to(user),
        **kwargs,
    )


class TestOutgoingEphemeralMessages:
    async def test_the_shape_is_telegrams(self, env, team, alice):
        message = await send_to(env, team, alice)

        assert message.message_id == 0
        assert message.ephemeral_message_id == 1
        assert message.receiver_user.id == alice.id

    async def test_the_deprecated_receiver_user_id_sends_one_too(self, env, team, alice):
        message = await env.bot.send_message(
            chat_id=team.id,
            text="only you",
            receiver_user_id=alice.id,
        )

        assert message.message_id == 0
        assert message.receiver_user.id == alice.id
        assert team.ephemeral_messages(alice) == [message]
        assert not any(m.text == "only you" for m in team.messages)

    async def test_it_stays_out_of_the_shared_history(self, env, team, alice):
        await env.bot.send_message(chat_id=team.id, text="public")
        await send_to(env, team, alice)

        assert [m.text for m in team.messages if m.text] == ["public"]
        with pytest.raises(TimeoutError):
            await team.wait_for_message(lambda m: m.text == "only you", timeout=0.05)

    async def test_it_is_read_back_per_receiver_and_direction(self, env, team, alice, bob):
        await send_to(env, team, alice, "first")
        await send_to(env, team, bob, "for bob")
        await send_to(env, team, alice, "second")
        await env.user(alice).in_(team).send("/mine", ephemeral=True)

        assert [m.text for m in team.ephemeral_messages(alice)] == ["first", "second"]
        assert [m.text for m in team.ephemeral_messages(bob.id)] == ["for bob"]
        assert [m.text for m in team.ephemeral_commands(alice)] == ["/mine"]

    @pytest.mark.parametrize("chat_fixture", ["private", "channel"])
    async def test_it_is_refused_outside_a_group(self, env, alice, chat_fixture, request):
        chat = request.getfixturevalue(chat_fixture)

        with pytest.raises(TelegramBadRequest, match="group and supergroup"):
            await send_to(env, chat, alice)

        assert chat.sent_ephemeral == {}

    async def test_an_undeclared_receiver_is_a_setup_error(self, env, team):
        with pytest.raises(WorldLookupError, match="User 424242"):
            await env.bot.send_message(
                chat_id=team.id,
                text="x",
                ephemeral_message_parameters=EphemeralMessageParameters(receiver_user_id=424242),
            )

        assert team.sent_ephemeral == {}

    async def test_a_non_member_receiver_is_not_checked(self, env, team, world_blueprint):
        carol = world_blueprint.users[2]

        message = await send_to(env, team, carol)

        assert message.receiver_user.id == carol.id

    async def test_it_keeps_its_topic(self, env, team, alice, support):
        message = await send_to(env, team, alice, message_thread_id=support.message_thread_id)

        assert message.message_thread_id == support.message_thread_id

    async def test_a_photo_takes_the_same_path(self, env, team, alice):
        message = await env.bot.send_photo(
            chat_id=team.id,
            photo=BufferedInputFile(b"x", "x.jpg"),
            ephemeral_message_parameters=to(alice),
        )

        assert message.message_id == 0
        assert message.photo
        assert team.ephemeral_messages(alice) == [message]

    async def test_a_rich_message_takes_the_same_path(self, env, team, alice):
        message = await env.bot.send_rich_message(
            chat_id=team.id,
            rich_message=InputRichMessage(blocks=[InputRichBlockParagraph(text="hi")]),
            ephemeral_message_parameters=to(alice),
        )

        assert message.ephemeral_message_id is not None
        assert message.rich_message.blocks[0].text == "hi"


class TestEphemeralClicks:
    async def test_the_receiver_clicks(self, env, team, alice):
        seen = []
        env.dispatcher.callback_query.register(lambda query: seen.append(query.message))
        sent = await send_to(env, team, alice, reply_markup=keyboard())

        await env.user(alice).in_(team).click("ok")

        (message,) = seen
        assert message.ephemeral_message_id == sent.ephemeral_message_id
        assert message.receiver_user.id == alice.id

    async def test_the_receivers_message_wins_over_the_shared_history(self, env, team, alice):
        seen = []
        env.dispatcher.callback_query.register(lambda query: seen.append(query.message))
        await env.bot.send_message(chat_id=team.id, text="public", reply_markup=keyboard())
        await send_to(env, team, alice, reply_markup=keyboard())

        await env.user(alice).in_(team).click("ok")

        assert seen[0].ephemeral_message_id is not None

    async def test_another_member_is_told_who_it_is_for(self, env, team, alice, bob):
        await send_to(env, team, alice, reply_markup=keyboard())

        with pytest.raises(WorldLookupError, match=f"addressed to user {alice.id}"):
            await env.user(bob).in_(team).click("ok")

    async def test_a_miss_does_not_point_at_the_actors_own_messages(self, env, team, alice):
        await send_to(env, team, alice, reply_markup=keyboard("other"))

        with pytest.raises(WorldLookupError) as failure:
            await env.user(alice).in_(team).click("missing")

        assert "addressed to user" not in str(failure.value)

    async def test_passing_someone_elses_message_is_refused(self, env, team, alice, bob):
        sent = await send_to(env, team, alice, reply_markup=keyboard())

        with pytest.raises(WorldLookupError, match="is not addressed to user"):
            await env.user(bob).in_(team).click("ok", message=sent)

    async def test_a_refusal_names_the_passed_messages_own_receiver(
        self, env, team, world_blueprint, alice, bob
    ):
        carol = world_blueprint.users[2]
        await send_to(env, team, carol, reply_markup=keyboard())
        await send_to(env, team, bob, reply_markup=keyboard())
        (for_bob,) = team.ephemeral_messages(bob)

        with pytest.raises(WorldLookupError) as failure:
            await env.user(alice).in_(team).click("ok", message=for_bob)

        assert f"addressed to user {bob.id}" in str(failure.value)
        assert str(carol.id) not in str(failure.value)

    async def test_passing_ones_own_message_works(self, env, team, alice):
        seen = []
        env.dispatcher.callback_query.register(lambda query: seen.append(query.data))
        sent = await send_to(env, team, alice, reply_markup=keyboard())

        await env.user(alice).in_(team).click("ok", message=sent)

        assert seen == ["ok"]

    async def test_the_receiver_follows_a_deep_link_on_it(self, env, team, alice):
        seen = []
        env.dispatcher.message.register(lambda message: seen.append(message.text))
        username = env.world.bot_user.username
        link = InlineKeyboardButton(text="Go", url=f"https://t.me/{username}?start=abc")
        await send_to(
            env, team, alice, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[link]])
        )

        await env.user(alice).in_(team).follow_deep_link()

        assert seen == ["/start abc"]

    async def test_another_member_cannot_follow_its_deep_link(self, env, team, alice, bob):
        username = env.world.bot_user.username
        link = InlineKeyboardButton(text="Go", url=f"https://t.me/{username}?start=abc")
        sent = await send_to(
            env, team, alice, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[link]])
        )

        with pytest.raises(WorldLookupError, match="is not addressed to user"):
            await env.user(bob).in_(team).follow_deep_link(message=sent)

    async def test_a_deleted_one_cannot_be_clicked(self, env, team, alice):
        sent = await send_to(env, team, alice, reply_markup=keyboard())
        await env.bot.delete_ephemeral_message(
            chat_id=team.id,
            receiver_user_id=alice.id,
            ephemeral_message_id=sent.ephemeral_message_id,
        )

        with pytest.raises(WorldLookupError, match="Ephemeral message .* does not exist"):
            await env.user(alice).in_(team).click("ok", message=sent)

    async def test_a_command_is_not_a_button_target(self, env, team, alice):
        actor = env.user(alice).in_(team)
        await actor.send("/x", ephemeral=True)
        (command,) = team.ephemeral_commands(alice)

        with pytest.raises(WorldLookupError, match="is not addressed to user"):
            await actor.click("ok", message=command)


class TestReplacingACallbackMessage:
    async def answer(self, env, team, alice, *, ephemeral_origin):
        outcome = []

        async def handler(query):
            try:
                await query.bot.send_message(
                    chat_id=team.id,
                    text="instead",
                    ephemeral_message_parameters=to(
                        alice,
                        callback_query_id=query.id,
                        replace_callback_query_message=True,
                    ),
                )
                outcome.append("sent")
            except TelegramBadRequest:
                outcome.append("refused")
            outcome.append(query.id in env.world.pending_queries)

        env.dispatcher.callback_query.register(handler)
        if ephemeral_origin:
            await send_to(env, team, alice, reply_markup=keyboard())
        else:
            await env.bot.send_message(chat_id=team.id, text="public", reply_markup=keyboard())
        await env.user(alice).in_(team).click("ok")
        return outcome

    async def test_an_ephemeral_origin_cannot_be_replaced(self, env, team, alice):
        assert await self.answer(env, team, alice, ephemeral_origin=True) == ["refused", True]

    async def test_a_shared_origin_can_be_replaced(self, env, team, alice):
        assert await self.answer(env, team, alice, ephemeral_origin=False) == ["sent", True]


class TestEphemeralEditsAndDeletions:
    async def test_editing_text(self, env, team, alice):
        sent = await send_to(env, team, alice)

        assert await env.bot.edit_ephemeral_message_text(
            chat_id=team.id,
            receiver_user_id=alice.id,
            ephemeral_message_id=sent.ephemeral_message_id,
            text="edited",
        )

        assert [m.text for m in team.ephemeral_messages(alice)] == ["edited"]
        assert team.messages == [m for m in team.messages if m.ephemeral_message_id is None]

    async def test_editing_rich_content(self, env, team, alice):
        sent = await send_to(env, team, alice)

        await env.bot.edit_ephemeral_message_text(
            chat_id=team.id,
            receiver_user_id=alice.id,
            ephemeral_message_id=sent.ephemeral_message_id,
            rich_message=InputRichMessage(blocks=[InputRichBlockParagraph(text="rich")]),
        )

        (stored,) = team.ephemeral_messages(alice)
        assert stored.text is None
        assert stored.rich_message.blocks[0].text == "rich"

    async def test_editing_caption_media_and_markup(self, env, team, alice):
        sent = await env.bot.send_photo(
            chat_id=team.id,
            photo=BufferedInputFile(b"x", "x.jpg"),
            caption="old",
            ephemeral_message_parameters=to(alice),
        )
        target = {
            "chat_id": team.id,
            "receiver_user_id": alice.id,
            "ephemeral_message_id": sent.ephemeral_message_id,
        }

        await env.bot.edit_ephemeral_message_caption(**target, caption="new")
        assert team.ephemeral_messages(alice)[0].caption == "new"
        await env.bot.edit_ephemeral_message_media(
            **target,
            media=InputMediaPhoto(media="other", caption="swapped"),
        )
        assert team.ephemeral_messages(alice)[0].caption == "swapped"
        await env.bot.edit_ephemeral_message_reply_markup(**target, reply_markup=keyboard("x"))
        (stored,) = team.ephemeral_messages(alice)
        assert stored.reply_markup.inline_keyboard[0][0].callback_data == "x"

    async def test_deleting(self, env, team, alice):
        sent = await send_to(env, team, alice)
        target = {
            "chat_id": team.id,
            "receiver_user_id": alice.id,
            "ephemeral_message_id": sent.ephemeral_message_id,
        }

        assert await env.bot.delete_ephemeral_message(**target)

        assert team.ephemeral_messages(alice) == []
        with pytest.raises(TelegramBadRequest, match="message to edit not found"):
            await env.bot.edit_ephemeral_message_text(**target, text="late")
        with pytest.raises(TelegramBadRequest, match="message to delete not found"):
            await env.bot.delete_ephemeral_message(**target)

    async def test_the_wrong_receiver_does_not_match(self, env, team, alice, bob):
        sent = await send_to(env, team, alice)

        with pytest.raises(TelegramBadRequest, match="message to edit not found"):
            await env.bot.edit_ephemeral_message_text(
                chat_id=team.id,
                receiver_user_id=bob.id,
                ephemeral_message_id=sent.ephemeral_message_id,
                text="hijack",
            )

        assert team.ephemeral_messages(alice)[0].text == "only you"

    async def test_a_refused_media_edit_registers_no_upload(self, env, team, alice, bob):
        sent = await send_to(env, team, alice)
        files = dict(env.world.files)

        with pytest.raises(TelegramBadRequest, match="message to edit not found"):
            await env.bot.edit_ephemeral_message_media(
                chat_id=team.id,
                receiver_user_id=bob.id,
                ephemeral_message_id=sent.ephemeral_message_id,
                media=InputMediaPhoto(media=BufferedInputFile(b"x", "x.jpg")),
            )

        assert env.world.files == files

    async def test_the_messages_own_shortcuts(self, env, team, alice):
        sent = await send_to(env, team, alice)

        await sent.edit_ephemeral_text("via shortcut")
        assert team.ephemeral_messages(alice)[0].text == "via shortcut"
        await sent.delete_ephemeral()
        assert team.ephemeral_messages(alice) == []

    async def test_regular_edits_do_not_reach_it(self, env, team, alice):
        sent = await send_to(env, team, alice)

        with pytest.raises(TelegramBadRequest):
            await sent.edit_text("regular")
        with pytest.raises(TelegramBadRequest):
            await sent.delete()

        assert team.ephemeral_messages(alice)[0].text == "only you"


class TestEphemeralCommands:
    async def test_two_commands_both_dispatch(self, env, team, alice):
        seen = []
        env.dispatcher.message.register(
            lambda message: seen.append((message.message_id, message.ephemeral_message_id)),
        )
        actor = env.user(alice).in_(team)

        await actor.send("/one", ephemeral=True)
        await actor.send("/two", ephemeral=True)

        assert seen == [(0, 1), (0, 2)]
        assert [m for m in team.messages if m.ephemeral_message_id is not None] == []

    async def test_a_topic_bound_actor_tags_the_command(self, env, team, alice, support):
        seen = []
        env.dispatcher.message.register(lambda message: seen.append(message.message_thread_id))

        await env.user(alice).in_(team, topic=support).send("/x", ephemeral=True)

        assert seen == [support.message_thread_id]

    async def test_a_hand_fed_command_is_registered(self, env, team, alice):
        message = Message(
            message_id=0,
            ephemeral_message_id=7,
            date=BASE_DATE,
            chat=team.as_chat(),
            from_user=env.world.user(alice.id).as_user(),
            text="/fed",
        )

        await env.feed(Update(update_id=1, message=message))
        await env.feed(Update(update_id=2, message=message))

        assert [m.text for m in team.ephemeral_commands(alice)] == ["/fed"]
        assert team.allocate_ephemeral_message_id() == 8

    async def test_a_hand_fed_command_colliding_with_another_is_refused(self, env, team, alice):
        await env.user(alice).in_(team).send("/own", ephemeral=True)
        (own,) = team.ephemeral_commands(alice)
        message = Message(
            message_id=0,
            ephemeral_message_id=own.ephemeral_message_id,
            date=BASE_DATE,
            chat=team.as_chat(),
            from_user=env.world.user(alice.id).as_user(),
            text="/fed",
        )

        with pytest.raises(WorldLookupError, match="different ephemeral message"):
            await env.feed(Update(update_id=99, message=message))

    async def test_a_hand_fed_command_reusing_a_sent_id_is_refused(self, env, team, alice, bob):
        await send_to(env, team, bob)
        (sent,) = team.ephemeral_messages(bob)
        message = Message(
            message_id=0,
            ephemeral_message_id=sent.ephemeral_message_id,
            date=BASE_DATE,
            chat=team.as_chat(),
            from_user=env.world.user(alice.id).as_user(),
            text="/fed",
        )

        with pytest.raises(WorldLookupError, match="different ephemeral message"):
            await env.feed(Update(update_id=99, message=message))

        assert team.received_ephemeral == {}

    async def test_a_hand_fed_command_without_a_sender_is_refused(self, env, team):
        message = Message(
            message_id=0,
            ephemeral_message_id=7,
            date=BASE_DATE,
            chat=team.as_chat(),
            text="/fed",
        )

        with pytest.raises(WorldLookupError, match="names no sender"):
            await env.feed(Update(update_id=1, message=message))

        assert team.received_ephemeral == {}

    async def test_a_fields_override_is_registered_too(self, env, team, alice):
        await (
            env.user(alice)
            .in_(team)
            .send(
                "/raw",
                fields={"message_id": 0, "ephemeral_message_id": 5},
            )
        )

        assert [m.text for m in team.ephemeral_commands(alice)] == ["/raw"]
        assert all(m.message_id != 0 for m in team.messages)

    async def test_a_fields_override_reusing_an_id_is_refused_before_storing(
        self, env, team, alice, bob
    ):
        await send_to(env, team, bob)
        (sent,) = team.ephemeral_messages(bob)
        actor = env.user(alice).in_(team)
        await actor.send("/own", ephemeral=True)
        (own,) = team.ephemeral_commands(alice)

        for taken in (own.ephemeral_message_id, sent.ephemeral_message_id):
            with pytest.raises(WorldLookupError, match="already holds an ephemeral message"):
                await actor.send("/again", fields={"ephemeral_message_id": taken})

        assert [m.text for m in team.ephemeral_commands(alice)] == ["/own"]

    async def test_outside_a_group_is_a_setup_error(self, env, private, alice):
        with pytest.raises(WorldLookupError, match="groups and supergroups only"):
            await env.user(alice).in_(private).send("/x", ephemeral=True)

    async def test_a_business_binding_is_a_setup_error(self, env, team, alice, world_blueprint):
        actor = env.user(alice).in_(team, business=world_blueprint.business_connections[0])

        with pytest.raises(WorldLookupError, match="business connection"):
            await actor.send("/x", ephemeral=True)

    async def test_a_user_cannot_edit_or_reply_to_one(self, env, team, alice):
        actor = env.user(alice).in_(team)
        await actor.send("/x", ephemeral=True)
        (command,) = team.ephemeral_commands(alice)

        with pytest.raises(WorldLookupError, match="cannot be edited"):
            await actor.edit(command, "changed")
        with pytest.raises(WorldLookupError, match="cannot be replied to"):
            await actor.reply(command, "answer")


class TestRepliesToEphemeralCommands:
    async def test_the_reply_shortcut_answers_ephemerally(self, env, team, alice):
        replies = []

        async def handler(message):
            replies.append(await message.reply("only for you"))

        env.dispatcher.message.register(handler)

        await env.user(alice).in_(team).send("/secret", ephemeral=True)

        (reply,) = replies
        assert reply.ephemeral_message_id is not None
        assert reply.receiver_user.id == alice.id
        assert reply.reply_to_message is None
        assert team.ephemeral_messages(alice) == [reply]

    async def test_answer_sends_an_ordinary_message(self, env, team, alice):
        async def handler(message):
            await message.answer("for everyone")

        env.dispatcher.message.register(handler)

        await env.user(alice).in_(team).send("/secret", ephemeral=True)

        assert team.messages[-1].text == "for everyone"

    async def test_a_non_ephemeral_reply_is_refused(self, env, team, alice):
        await env.user(alice).in_(team).send("/x", ephemeral=True)
        (command,) = team.ephemeral_commands(alice)
        before = list(team.messages)

        with pytest.raises(TelegramBadRequest, match="must itself be an ephemeral message"):
            await env.bot.send_message(
                chat_id=team.id,
                text="public",
                reply_parameters=ReplyParameters(
                    ephemeral_message_id=command.ephemeral_message_id,
                ),
            )

        assert team.messages == before

    async def test_an_unknown_id_is_refused(self, env, team, alice):
        with pytest.raises(TelegramBadRequest, match="message to be replied not found"):
            await send_to(
                env, team, alice, reply_parameters=ReplyParameters(ephemeral_message_id=99)
            )

        assert team.ephemeral_messages(alice) == []

    async def test_an_ephemeral_reply_to_a_shared_message_keeps_it(self, env, team, alice):
        public = await env.bot.send_message(chat_id=team.id, text="public")

        reply = await send_to(
            env,
            team,
            alice,
            reply_parameters=ReplyParameters(message_id=public.message_id),
        )

        assert reply.reply_to_message.message_id == public.message_id

    async def test_the_bots_own_ephemeral_message_is_not_incoming(self, env, team, alice):
        own = await send_to(env, team, alice)

        with pytest.raises(TelegramBadRequest, match="message to be replied not found"):
            await send_to(
                env,
                team,
                alice,
                reply_parameters=ReplyParameters(ephemeral_message_id=own.ephemeral_message_id),
            )


class TestStoreGuards:
    def test_an_outgoing_message_names_its_receiver(self, team):
        with pytest.raises(ValueError, match="receiver_user"):
            team.add_ephemeral_message(
                Message(message_id=0, date=BASE_DATE, chat=team.as_chat()),
            )

    def test_an_incoming_message_names_sender_and_id(self, team):
        with pytest.raises(ValueError, match="sender and its id"):
            team.add_ephemeral_command(
                Message(message_id=0, date=BASE_DATE, chat=team.as_chat()),
            )


class TestWaitingForEphemeralMessages:
    async def test_the_receivers_view_is_waited_on(self, env, team, alice):
        await send_to(env, team, alice, text="first")
        await send_to(env, team, alice, text="second")

        newest = await team.wait_for_message(receiver=alice, timeout=0.05)
        first = await team.wait_for_message(
            lambda m: m.text == "first", receiver=alice, timeout=0.05
        )

        assert newest.text == "second"
        assert first.text == "first"

    async def test_the_shared_wait_points_to_them(self, env, team, alice):
        await send_to(env, team, alice, text="psst")

        with pytest.raises(WaitTimeoutError, match="receiver=<user>"):
            await team.wait_for_message(lambda m: m.text == "psst", timeout=0.05)

    async def test_another_receivers_view_times_out(self, env, team, alice, bob):
        await send_to(env, team, alice, text="psst")

        with pytest.raises(WaitTimeoutError, match="as seen by user"):
            await team.wait_for_message(receiver=bob, timeout=0.05)

    async def test_a_timeout_names_each_message_the_predicate_raised_on(self, env, team, alice):
        """Every ephemeral message has message_id 0, so they are told apart by ephemeral id."""
        await send_to(env, team, alice, text="one")
        await send_to(env, team, alice, text="two")

        with pytest.raises(WaitTimeoutError) as raised:
            await team.wait_for_message(
                lambda m: m.caption.startswith("x"),
                receiver=alice,
                timeout=0.05,
            )

        text = str(raised.value)
        assert "raised on 2 of them" in text
        assert "ephemeral #1 'one'" in text
        assert "on ephemeral message #2" in text
