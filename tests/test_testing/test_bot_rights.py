import pytest

from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import Blueprint, BotTestEnvironment, administrator_rights
from aiogram.types import ChatPermissions, InputMediaDocument, InputMediaPhoto

ADMIN = ChatMemberStatus.ADMINISTRATOR
NO_TEXT = ChatPermissions(can_send_messages=False, can_send_photos=True)
NO_PHOTOS = ChatPermissions(can_send_messages=True, can_send_photos=False)


@pytest.fixture
def world(dp):
    """Build an environment around one chat the bot is declared into."""
    environments = []

    def build(
        chat_type=ChatType.SUPERGROUP,
        *,
        status=None,
        rights=None,
        permissions=None,
        chat_permissions=None,
        enforce_bot_rights=True,
    ):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        add = {
            ChatType.GROUP: blueprint.add_group,
            ChatType.SUPERGROUP: blueprint.add_supergroup,
            ChatType.CHANNEL: blueprint.add_channel,
        }[chat_type]
        chat = add("Chat", members={alice: ChatMemberStatus.MEMBER}, bot_status=status)
        chat.permissions = chat_permissions
        if rights is not None:
            blueprint.set_member(chat, blueprint.bot, rights=rights)
        if permissions is not None:
            blueprint.set_member(chat, blueprint.bot, permissions=permissions)
        blueprint.add_private_chat(alice)
        environment = BotTestEnvironment(
            blueprint=blueprint,
            dispatcher=dp,
            enforce_bot_rights=enforce_bot_rights,
        )
        environments.append(environment)
        return environment, environment.chat(chat), environment.user(alice)

    yield build
    for environment in environments:
        environment.dispose_sync()


async def users_message(chat, alice):
    await alice.in_(chat).send("from alice")
    return chat.messages[-1]


class TestPinning:
    PINS = ["pin_chat_message", "unpin_chat_message", "unpin_all_chat_messages"]

    async def pin_call(self, env, chat, name):
        message = await env.bot.send_message(chat_id=chat.id, text="x")
        kwargs = {} if name == "unpin_all_chat_messages" else {"message_id": message.message_id}
        return await getattr(env.bot, name)(chat_id=chat.id, **kwargs)

    @pytest.mark.parametrize("name", PINS)
    @pytest.mark.parametrize("chat_type", [ChatType.GROUP, ChatType.SUPERGROUP])
    async def test_a_member_bot_cannot_manage_pins(self, world, name, chat_type):
        env, chat, _alice = world(chat_type)

        with pytest.raises(
            TelegramBadRequest,
            match="Bad Request: not enough rights to manage pinned messages in the chat$",
        ):
            await self.pin_call(env, chat, name)

    @pytest.mark.parametrize("name", PINS)
    async def test_an_administrator_manages_pins(self, world, name):
        env, chat, _alice = world(status=ADMIN)

        assert await self.pin_call(env, chat, name) is True

    async def test_an_administrator_without_the_right_cannot_pin(self, world):
        env, chat, _alice = world(rights=administrator_rights(can_pin_messages=False))

        with pytest.raises(TelegramBadRequest, match="manage pinned messages"):
            await self.pin_call(env, chat, "pin_chat_message")

    async def test_a_channel_takes_the_right_to_edit_messages(self, world):
        env, chat, _alice = world(
            ChatType.CHANNEL,
            rights=administrator_rights(can_edit_messages=False),
        )

        with pytest.raises(TelegramBadRequest, match="manage pinned messages"):
            await self.pin_call(env, chat, "pin_chat_message")

    async def test_a_channel_administrator_pins(self, world):
        env, chat, _alice = world(ChatType.CHANNEL, status=ADMIN)

        assert await self.pin_call(env, chat, "pin_chat_message") is True

    async def test_the_owner_pins(self, world):
        env, chat, _alice = world(status=ChatMemberStatus.CREATOR)

        assert await self.pin_call(env, chat, "pin_chat_message") is True

    async def test_a_private_chat_needs_no_right(self, world):
        env, _chat, alice = world()
        private = env.chat(alice.user.id)

        message = await env.bot.send_message(chat_id=private.id, text="x")

        assert await env.bot.pin_chat_message(chat_id=private.id, message_id=message.message_id)

    async def test_unpinning_a_topic_takes_the_right(self, dp):
        blueprint = Blueprint()
        chat = blueprint.add_supergroup("Forum")
        topic = blueprint.add_topic(chat, "Game")
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            with pytest.raises(TelegramBadRequest, match="manage pinned messages"):
                await env.bot.unpin_all_forum_topic_messages(
                    chat_id=chat.id,
                    message_thread_id=topic.message_thread_id,
                )
            with pytest.raises(TelegramBadRequest, match="manage pinned messages"):
                await env.bot.unpin_all_general_forum_topic_messages(chat_id=chat.id)
        finally:
            env.dispose_sync()


class TestModeration:
    async def test_a_member_bot_cannot_restrict(self, world):
        env, chat, alice = world()

        with pytest.raises(
            TelegramBadRequest,
            match="Bad Request: not enough rights to restrict/unrestrict chat member$",
        ):
            await env.bot.restrict_chat_member(
                chat_id=chat.id,
                user_id=alice.user.id,
                permissions=NO_TEXT,
            )

        assert chat.member(alice.user.id).status == ChatMemberStatus.MEMBER

    @pytest.mark.parametrize("name", ["ban_chat_member", "unban_chat_member"])
    @pytest.mark.parametrize("chat_type", [ChatType.SUPERGROUP, ChatType.CHANNEL])
    async def test_a_member_bot_cannot_ban_or_unban(self, world, name, chat_type):
        env, chat, alice = world(chat_type)

        with pytest.raises(TelegramBadRequest, match="restrict/unrestrict chat member"):
            await getattr(env.bot, name)(chat_id=chat.id, user_id=alice.user.id)

    async def test_a_basic_group_answers_admin_required(self, world):
        env, chat, alice = world(ChatType.GROUP)

        with pytest.raises(TelegramBadRequest, match="Bad Request: CHAT_ADMIN_REQUIRED$"):
            await env.bot.ban_chat_member(chat_id=chat.id, user_id=alice.user.id)

    async def test_an_administrator_without_the_right_cannot_ban(self, world):
        env, chat, alice = world(rights=administrator_rights(can_restrict_members=False))

        with pytest.raises(TelegramBadRequest, match="restrict/unrestrict"):
            await env.bot.ban_chat_member(chat_id=chat.id, user_id=alice.user.id)

    async def test_an_administrator_bans(self, world):
        env, chat, alice = world(status=ADMIN)

        await env.bot.ban_chat_member(chat_id=chat.id, user_id=alice.user.id)

        assert chat.member(alice.user.id).status == ChatMemberStatus.KICKED

    async def test_an_ordinary_administrator_cannot_promote(self, world):
        env, chat, alice = world(status=ADMIN)

        with pytest.raises(TelegramBadRequest, match="Bad Request: not enough rights$"):
            await env.bot.promote_chat_member(
                chat_id=chat.id,
                user_id=alice.user.id,
                can_pin_messages=True,
            )

    async def test_a_basic_group_answers_owner_rights(self, world):
        env, chat, alice = world(ChatType.GROUP, status=ADMIN)

        with pytest.raises(TelegramBadRequest, match="need owner rights in the group chat"):
            await env.bot.promote_chat_member(
                chat_id=chat.id,
                user_id=alice.user.id,
                can_pin_messages=True,
            )

    async def test_an_administrator_that_may_promote_promotes(self, world):
        env, chat, alice = world(rights=administrator_rights(can_promote_members=True))

        await env.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=alice.user.id,
            can_pin_messages=True,
        )

        assert chat.member(alice.user.id).status == ADMIN

    async def test_the_owner_guard_comes_first(self, dp):
        blueprint = Blueprint()
        owner = blueprint.add_user("Owner")
        chat = blueprint.add_supergroup("Chat", members={owner: ChatMemberStatus.CREATOR})
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            with pytest.raises(TelegramBadRequest, match="can't remove chat owner"):
                await env.bot.ban_chat_member(chat_id=chat.id, user_id=owner.id)
        finally:
            env.dispose_sync()


class TestDeleting:
    async def test_a_member_bot_deletes_its_own_message(self, world):
        env, chat, _alice = world()
        sent = await env.bot.send_message(chat_id=chat.id, text="mine")

        assert await env.bot.delete_message(chat_id=chat.id, message_id=sent.message_id)

    @pytest.mark.parametrize("chat_type", [ChatType.GROUP, ChatType.SUPERGROUP])
    async def test_a_member_bot_cannot_delete_a_users_message(self, world, chat_type):
        env, chat, alice = world(chat_type)
        message = await users_message(chat, alice)

        with pytest.raises(TelegramBadRequest, match="Bad Request: message can't be deleted$"):
            await env.bot.delete_message(chat_id=chat.id, message_id=message.message_id)

        assert chat.find_message(message.message_id) is not None

    async def test_any_administrator_deletes_in_a_basic_group(self, world):
        env, chat, alice = world(
            ChatType.GROUP,
            rights=administrator_rights(can_delete_messages=False),
        )
        message = await users_message(chat, alice)

        assert await env.bot.delete_message(chat_id=chat.id, message_id=message.message_id)

    async def test_a_supergroup_takes_the_right_to_delete(self, world):
        env, chat, alice = world(rights=administrator_rights(can_delete_messages=False))
        message = await users_message(chat, alice)

        with pytest.raises(TelegramBadRequest, match="message can't be deleted"):
            await env.bot.delete_message(chat_id=chat.id, message_id=message.message_id)

    async def test_a_supergroup_administrator_deletes(self, world):
        env, chat, alice = world(status=ADMIN)
        message = await users_message(chat, alice)

        assert await env.bot.delete_message(chat_id=chat.id, message_id=message.message_id)

    async def test_a_channel_poster_deletes_its_own_posts_only(self, world):
        env, chat, alice = world(
            ChatType.CHANNEL,
            rights=administrator_rights(can_delete_messages=False),
        )
        own = await env.bot.send_message(chat_id=chat.id, text="mine")
        signed = await users_message(chat, alice)

        assert await env.bot.delete_message(chat_id=chat.id, message_id=own.message_id)
        with pytest.raises(TelegramBadRequest, match="message can't be deleted"):
            await env.bot.delete_message(chat_id=chat.id, message_id=signed.message_id)

    async def test_a_channel_deleter_deletes_any_post(self, world):
        env, chat, alice = world(ChatType.CHANNEL, status=ADMIN)
        signed = await users_message(chat, alice)

        assert await env.bot.delete_message(chat_id=chat.id, message_id=signed.message_id)

    async def test_deleting_many_skips_what_the_bot_may_not_delete(self, world):
        env, chat, alice = world()
        own = await env.bot.send_message(chat_id=chat.id, text="mine")
        theirs = await users_message(chat, alice)

        await env.bot.delete_messages(
            chat_id=chat.id,
            message_ids=[own.message_id, theirs.message_id],
        )

        assert chat.find_message(own.message_id) is None
        assert chat.find_message(theirs.message_id) is not None


class TestSending:
    async def test_the_chat_permissions_bind_a_member_bot(self, world):
        env, chat, _alice = world(chat_permissions=NO_TEXT)
        before = chat.last_message_id

        with pytest.raises(
            TelegramBadRequest,
            match="Bad Request: not enough rights to send text messages to the chat$",
        ):
            await env.bot.send_message(chat_id=chat.id, text="x")

        assert chat.last_message_id == before

    async def test_each_kind_is_named_by_its_permission(self, world):
        env, chat, _alice = world(chat_permissions=NO_PHOTOS)

        await env.bot.send_message(chat_id=chat.id, text="text is fine")
        with pytest.raises(TelegramBadRequest, match="not enough rights to send photos"):
            await env.bot.send_photo(chat_id=chat.id, photo="file")

    async def test_a_poll_takes_the_poll_permission(self, world):
        env, chat, _alice = world(chat_permissions=ChatPermissions(can_send_messages=True))

        with pytest.raises(TelegramBadRequest, match="not enough rights to send polls"):
            await env.bot.send_poll(chat_id=chat.id, question="?", options=["a", "b"])

    async def test_a_media_group_checks_its_items(self, world):
        env, chat, _alice = world(chat_permissions=NO_PHOTOS)

        with pytest.raises(TelegramBadRequest, match="photos"):
            await env.bot.send_media_group(
                chat_id=chat.id,
                media=[InputMediaPhoto(media="a"), InputMediaPhoto(media="b")],
            )

    async def test_a_media_group_of_allowed_kinds_goes_through(self, world):
        env, chat, _alice = world(
            chat_permissions=ChatPermissions(can_send_documents=True),
        )

        sent = await env.bot.send_media_group(
            chat_id=chat.id,
            media=[InputMediaDocument(media="a"), InputMediaDocument(media="b")],
        )

        assert len(sent) == 2

    async def test_the_bots_own_restriction_narrows_the_chat(self, world):
        env, chat, _alice = world(permissions=NO_TEXT)

        with pytest.raises(TelegramBadRequest, match="send text messages"):
            await env.bot.send_message(chat_id=chat.id, text="x")

    async def test_a_restriction_with_no_permissions_denies_all(self, world):
        env, chat, _alice = world()
        bot = chat.member(env.world.bot_user.id)
        bot.set_status(ChatMemberStatus.RESTRICTED)

        with pytest.raises(TelegramBadRequest, match="send text messages"):
            await env.bot.send_message(chat_id=chat.id, text="x")

    async def test_an_administrator_ignores_the_chat_permissions(self, world):
        env, chat, _alice = world(status=ADMIN, chat_permissions=NO_TEXT)

        await env.bot.send_message(chat_id=chat.id, text="x")

        assert chat.messages[-1].text == "x"

    @pytest.mark.parametrize("move", ["copy_message", "forward_message"])
    async def test_a_move_takes_the_permission_of_what_it_carries(self, world, move):
        env, chat, alice = world(chat_permissions=NO_PHOTOS)
        private = env.chat(alice.user.id)
        photo = await env.bot.send_photo(chat_id=private.id, photo="file")

        with pytest.raises(TelegramBadRequest, match="send photos"):
            await getattr(env.bot, move)(
                chat_id=chat.id,
                from_chat_id=private.id,
                message_id=photo.message_id,
            )

    @pytest.mark.parametrize("move", ["copy_messages", "forward_messages"])
    async def test_a_refused_batch_stores_nothing(self, world, move):
        env, chat, alice = world(chat_permissions=NO_PHOTOS)
        private = env.chat(alice.user.id)
        text = await env.bot.send_message(chat_id=private.id, text="fine")
        photo = await env.bot.send_photo(chat_id=private.id, photo="file")
        before = list(chat.messages)

        with pytest.raises(TelegramBadRequest, match="send photos"):
            await getattr(env.bot, move)(
                chat_id=chat.id,
                from_chat_id=private.id,
                message_ids=[text.message_id, photo.message_id],
            )

        assert chat.messages == before

    async def test_a_member_bot_cannot_post_into_a_channel(self, world):
        env, chat, _alice = world(ChatType.CHANNEL)

        with pytest.raises(
            TelegramBadRequest,
            match="Bad Request: need administrator rights in the channel chat$",
        ):
            await env.bot.send_message(chat_id=chat.id, text="x")

    async def test_a_channel_administrator_without_the_right_cannot_post(self, world):
        env, chat, _alice = world(
            ChatType.CHANNEL,
            rights=administrator_rights(can_post_messages=False),
        )

        with pytest.raises(TelegramBadRequest, match="need administrator rights"):
            await env.bot.send_message(chat_id=chat.id, text="x")

    async def test_a_channel_administrator_posts(self, world):
        env, chat, _alice = world(ChatType.CHANNEL, status=ADMIN)

        await env.bot.send_message(chat_id=chat.id, text="x")

        assert chat.messages[-1].text == "x"


class TestOptingOut:
    async def test_the_bot_holds_every_right_it_needs(self, world):
        env, chat, alice = world(chat_permissions=NO_TEXT, enforce_bot_rights=False)
        message = await users_message(chat, alice)

        sent = await env.bot.send_message(chat_id=chat.id, text="x")
        await env.bot.pin_chat_message(chat_id=chat.id, message_id=sent.message_id)
        await env.bot.delete_message(chat_id=chat.id, message_id=message.message_id)
        await env.bot.promote_chat_member(
            chat_id=chat.id,
            user_id=alice.user.id,
            can_pin_messages=True,
        )
        await env.bot.ban_chat_member(chat_id=chat.id, user_id=alice.user.id)

        assert env.enforce_bot_rights is False
        assert chat.member(alice.user.id).status == ChatMemberStatus.KICKED

    async def test_a_closed_topic_takes_the_bots_messages(self, dp):
        blueprint = Blueprint()
        chat = blueprint.add_supergroup("Forum")
        topic = blueprint.add_topic(chat, "Game")
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp, enforce_bot_rights=False)
        try:
            state = env.chat(chat)
            state.topic(topic.message_thread_id).is_closed = True

            await env.bot.send_message(
                chat_id=chat.id,
                text="x",
                message_thread_id=topic.message_thread_id,
            )

            assert state.messages[-1].text == "x"
        finally:
            env.dispose_sync()
