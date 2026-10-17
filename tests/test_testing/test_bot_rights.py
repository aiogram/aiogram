import pytest

from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.test import Blueprint, BotTestEnvironment, administrator_rights
from aiogram.test.modeling import BOT_RIGHTS, holds_right
from aiogram.types import (
    BufferedInputFile,
    ChatAdministratorRights,
    ChatPermissions,
    InputMediaDocument,
    InputMediaPhoto,
    InputPaidMediaPhoto,
    ReplyParameters,
)

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

        with pytest.raises(TelegramBadRequest):
            await self.pin_call(env, chat, name)

    @pytest.mark.parametrize("name", PINS)
    async def test_an_administrator_manages_pins(self, world, name):
        env, chat, _alice = world(status=ADMIN)

        assert await self.pin_call(env, chat, name) is True

    async def test_an_administrator_without_the_right_cannot_pin(self, world):
        env, chat, _alice = world(rights=administrator_rights(can_pin_messages=False))

        with pytest.raises(TelegramBadRequest):
            await self.pin_call(env, chat, "pin_chat_message")

    async def test_a_channel_takes_the_right_to_edit_messages(self, world):
        env, chat, _alice = world(
            ChatType.CHANNEL,
            rights=administrator_rights(can_edit_messages=False),
        )

        with pytest.raises(TelegramBadRequest):
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
            with pytest.raises(TelegramBadRequest):
                await env.bot.unpin_all_forum_topic_messages(
                    chat_id=chat.id,
                    message_thread_id=topic.message_thread_id,
                )
            with pytest.raises(TelegramBadRequest):
                await env.bot.unpin_all_general_forum_topic_messages(chat_id=chat.id)
        finally:
            env.dispose_sync()


class TestModeration:
    async def test_a_member_bot_cannot_restrict(self, world):
        env, chat, alice = world()

        with pytest.raises(TelegramBadRequest):
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

        with pytest.raises(TelegramBadRequest):
            await getattr(env.bot, name)(chat_id=chat.id, user_id=alice.user.id)

    async def test_a_basic_group_answers_admin_required(self, world):
        env, chat, alice = world(ChatType.GROUP)

        with pytest.raises(TelegramBadRequest):
            await env.bot.ban_chat_member(chat_id=chat.id, user_id=alice.user.id)

    async def test_an_administrator_without_the_right_cannot_ban(self, world):
        env, chat, alice = world(rights=administrator_rights(can_restrict_members=False))

        with pytest.raises(TelegramBadRequest):
            await env.bot.ban_chat_member(chat_id=chat.id, user_id=alice.user.id)

    async def test_an_administrator_bans(self, world):
        env, chat, alice = world(status=ADMIN)

        await env.bot.ban_chat_member(chat_id=chat.id, user_id=alice.user.id)

        assert chat.member(alice.user.id).status == ChatMemberStatus.KICKED

    async def test_an_ordinary_administrator_cannot_promote(self, world):
        env, chat, alice = world(status=ADMIN)

        with pytest.raises(TelegramBadRequest):
            await env.bot.promote_chat_member(
                chat_id=chat.id,
                user_id=alice.user.id,
                can_pin_messages=True,
            )

    @pytest.mark.parametrize("name", ["promote_chat_member", "unban_chat_member"])
    @pytest.mark.parametrize("enforce", [True, False])
    async def test_a_basic_group_takes_neither_at_all(self, world, name, enforce):
        env, chat, alice = world(ChatType.GROUP, status=ADMIN, enforce_bot_rights=enforce)

        with pytest.raises(TelegramBadRequest):
            await getattr(env.bot, name)(chat_id=chat.id, user_id=alice.user.id)

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
            with pytest.raises(TelegramBadRequest):
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

        with pytest.raises(TelegramBadRequest):
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

        with pytest.raises(TelegramBadRequest):
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
        with pytest.raises(TelegramBadRequest):
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

        with pytest.raises(TelegramBadRequest):
            await env.bot.send_message(chat_id=chat.id, text="x")

        assert chat.last_message_id == before

    async def test_each_kind_is_named_by_its_permission(self, world):
        env, chat, _alice = world(chat_permissions=NO_PHOTOS)

        await env.bot.send_message(chat_id=chat.id, text="text is fine")
        with pytest.raises(TelegramBadRequest):
            await env.bot.send_photo(chat_id=chat.id, photo="file")

    async def test_a_poll_takes_the_poll_permission(self, world):
        env, chat, _alice = world(chat_permissions=ChatPermissions(can_send_messages=True))

        with pytest.raises(TelegramBadRequest):
            await env.bot.send_poll(chat_id=chat.id, question="?", options=["a", "b"])

    async def test_a_media_group_checks_its_items(self, world):
        env, chat, _alice = world(chat_permissions=NO_PHOTOS)

        with pytest.raises(TelegramBadRequest):
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

        with pytest.raises(TelegramBadRequest):
            await env.bot.send_message(chat_id=chat.id, text="x")

    async def test_a_restriction_with_no_permissions_denies_all(self, world):
        env, chat, _alice = world()
        bot = chat.member(env.world.bot_user.id)
        bot.set_status(ChatMemberStatus.RESTRICTED)

        with pytest.raises(TelegramBadRequest):
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

        with pytest.raises(TelegramBadRequest):
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

        with pytest.raises(TelegramBadRequest):
            await getattr(env.bot, move)(
                chat_id=chat.id,
                from_chat_id=private.id,
                message_ids=[text.message_id, photo.message_id],
            )

        assert chat.messages == before

    async def test_a_member_bot_cannot_post_into_a_channel(self, world):
        env, chat, _alice = world(ChatType.CHANNEL)

        with pytest.raises(TelegramBadRequest):
            await env.bot.send_message(chat_id=chat.id, text="x")

    async def test_a_channel_administrator_without_the_right_cannot_post(self, world):
        env, chat, _alice = world(
            ChatType.CHANNEL,
            rights=administrator_rights(can_post_messages=False),
        )

        with pytest.raises(TelegramBadRequest):
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


class TestTheRightsTable:
    """Every call the table names is refused for lack of the right."""

    CALLS = [
        ("set_chat_title", {"title": "T"}),
        (
            "set_chat_description",
            {"description": "D"},
        ),
        ("delete_chat_photo", {}),
        ("set_chat_photo", {"photo": BufferedInputFile(b"x", "p.jpg")}),
        ("create_chat_invite_link", {}),
        ("export_chat_invite_link", {}),
        ("approve_chat_join_request", {"user_id": 1000}),
        ("decline_chat_join_request", {"user_id": 1000}),
    ]

    @pytest.mark.parametrize(("name", "kwargs"), CALLS)
    @pytest.mark.parametrize("chat_type", [ChatType.GROUP, ChatType.SUPERGROUP])
    async def test_a_member_bot_is_refused(self, world, name, kwargs, chat_type):
        env, chat, _alice = world(chat_type)

        with pytest.raises(TelegramBadRequest):
            await getattr(env.bot, name)(chat_id=chat.id, **kwargs)

    async def test_the_right_lets_the_call_through(self, world):
        env, chat, _alice = world(rights=administrator_rights(can_invite_users=False))

        assert await env.bot.set_chat_title(chat_id=chat.id, title="T")
        with pytest.raises(TelegramBadRequest):
            await env.bot.create_chat_invite_link(chat_id=chat.id)

    async def test_a_record_only_call_into_an_undeclared_chat_is_not_checked(self, world):
        env, _chat, _alice = world()

        photo = BufferedInputFile(b"x", "p.jpg")
        assert await env.bot.set_chat_photo(chat_id=-1, photo=photo) is True

    def test_every_rule_names_a_right_the_bot_api_knows(self):
        for method_type, rule in BOT_RIGHTS.items():
            for chat_type in rule.chat_types:
                assert rule.right_in(chat_type) in ChatAdministratorRights.model_fields, (
                    method_type
                )


@pytest.fixture
def forum(dp):
    """A forum with a declared topic and one the bot opens."""
    environments = []

    async def build(*, rights=None):
        blueprint = Blueprint()
        chat = blueprint.add_supergroup("Forum", is_forum=True)
        declared = blueprint.add_topic(chat, "Declared")
        if rights is not None:
            blueprint.set_member(chat, blueprint.bot, rights=rights)
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        environments.append(environment)
        state = environment.chat(chat)
        # Opened while the bot may, so it is the bot's own.
        owner = state.member(environment.world.bot_user.id)
        status, owner.status = owner.status, ChatMemberStatus.CREATOR
        opened = await environment.bot.create_forum_topic(chat_id=chat.id, name="Own")
        owner.status = status
        return environment, state, declared.message_thread_id, opened.message_thread_id

    yield build
    for environment in environments:
        environment.dispose_sync()


class TestForumRights:
    TOPIC_CALLS = [
        ("edit_forum_topic", {"name": "N"}),
        ("close_forum_topic", {}),
        ("reopen_forum_topic", {}),
        ("delete_forum_topic", {}),
    ]
    GENERAL_CALLS = [
        ("edit_general_forum_topic", {"name": "N"}),
        ("close_general_forum_topic", {}),
        ("reopen_general_forum_topic", {}),
        ("hide_general_forum_topic", {}),
        ("unhide_general_forum_topic", {}),
    ]

    async def test_creating_takes_the_right(self, forum):
        env, chat, _declared, _own = await forum()

        with pytest.raises(TelegramBadRequest):
            await env.bot.create_forum_topic(chat_id=chat.id, name="New")

    async def test_a_chat_that_is_not_a_forum_is_refused_first(self, world):
        env, chat, _alice = world()

        with pytest.raises(TelegramBadRequest):
            await env.bot.create_forum_topic(chat_id=chat.id, name="New")

    @pytest.mark.parametrize(("name", "kwargs"), TOPIC_CALLS)
    async def test_a_topic_of_someone_else_takes_the_right(self, forum, name, kwargs):
        env, chat, declared, _own = await forum()

        with pytest.raises(TelegramBadRequest):
            await getattr(env.bot, name)(
                chat_id=chat.id,
                message_thread_id=declared,
                **kwargs,
            )

    @pytest.mark.parametrize(("name", "kwargs"), TOPIC_CALLS)
    async def test_the_bots_own_topic_takes_no_right(self, forum, name, kwargs):
        env, chat, _declared, own = await forum()

        assert await getattr(env.bot, name)(chat_id=chat.id, message_thread_id=own, **kwargs)

    @pytest.mark.parametrize(("name", "kwargs"), GENERAL_CALLS)
    async def test_the_general_topic_always_takes_the_right(self, forum, name, kwargs):
        env, chat, _declared, _own = await forum()

        with pytest.raises(TelegramBadRequest):
            await getattr(env.bot, name)(chat_id=chat.id, **kwargs)

    async def test_deleting_takes_the_right_to_delete_messages(self, forum):
        env, chat, declared, _own = await forum(
            rights=administrator_rights(can_delete_messages=False),
        )

        assert await env.bot.close_forum_topic(chat_id=chat.id, message_thread_id=declared)
        with pytest.raises(TelegramBadRequest):
            await env.bot.delete_forum_topic(chat_id=chat.id, message_thread_id=declared)

    async def test_the_bot_posts_into_its_own_closed_topic(self, forum):
        env, chat, declared, own = await forum()
        chat.topic(own).is_closed = True
        chat.topic(declared).is_closed = True

        await env.bot.send_message(chat_id=chat.id, text="x", message_thread_id=own)
        with pytest.raises(TelegramBadRequest):
            await env.bot.send_message(chat_id=chat.id, text="x", message_thread_id=declared)


class TestStanding:
    """A bot that is not in the chat is answered with a 403."""

    @pytest.mark.parametrize(
        ("chat_type", "status", "refusal"),
        [
            (ChatType.GROUP, ChatMemberStatus.KICKED, "bot was kicked from the group chat"),
            (ChatType.GROUP, ChatMemberStatus.LEFT, "bot is not a member of the group chat"),
            (
                ChatType.SUPERGROUP,
                ChatMemberStatus.KICKED,
                "bot was kicked from the supergroup chat",
            ),
            (
                ChatType.SUPERGROUP,
                ChatMemberStatus.LEFT,
                "bot is not a member of the supergroup chat",
            ),
            (ChatType.CHANNEL, ChatMemberStatus.KICKED, "bot was kicked from the channel chat"),
            (ChatType.CHANNEL, ChatMemberStatus.LEFT, "bot is not a member of the channel chat"),
        ],
    )
    async def test_a_send_is_forbidden(self, world, chat_type, status, refusal):
        env, chat, _alice = world(chat_type, status=status)

        with pytest.raises(TelegramForbiddenError, match=f"Forbidden: {refusal}$"):
            await env.bot.send_message(chat_id=chat.id, text="x")

        assert chat.messages == []

    async def test_an_administrative_call_is_forbidden_too(self, world):
        env, chat, _alice = world(status=ChatMemberStatus.KICKED)

        with pytest.raises(TelegramForbiddenError, match="kicked from the supergroup"):
            await env.bot.set_chat_title(chat_id=chat.id, title="T")

    @pytest.mark.parametrize("move", ["copy_message", "forward_message"])
    async def test_a_move_into_the_chat_is_forbidden(self, world, move):
        env, chat, alice = world(status=ChatMemberStatus.LEFT)
        private = env.chat(alice.user.id)
        sent = await env.bot.send_message(chat_id=private.id, text="x")

        with pytest.raises(TelegramForbiddenError, match="not a member"):
            await getattr(env.bot, move)(
                chat_id=chat.id,
                from_chat_id=private.id,
                message_id=sent.message_id,
            )

    @pytest.mark.parametrize("move", ["copy_messages", "forward_messages"])
    async def test_a_batch_into_the_chat_is_forbidden(self, world, move):
        env, chat, alice = world(status=ChatMemberStatus.LEFT)
        private = env.chat(alice.user.id)
        sent = await env.bot.send_message(chat_id=private.id, text="x")

        with pytest.raises(TelegramForbiddenError, match="not a member"):
            await getattr(env.bot, move)(
                chat_id=chat.id,
                from_chat_id=private.id,
                message_ids=[sent.message_id],
            )

    async def test_a_media_group_is_forbidden(self, world):
        env, chat, _alice = world(status=ChatMemberStatus.KICKED)

        with pytest.raises(TelegramForbiddenError, match="kicked"):
            await env.bot.send_media_group(
                chat_id=chat.id,
                media=[InputMediaPhoto(media="a"), InputMediaPhoto(media="b")],
            )

    async def test_a_bot_that_left_on_its_own_is_not_a_member(self, world):
        env, chat, _alice = world()
        await env.bot.leave_chat(chat_id=chat.id)

        with pytest.raises(TelegramForbiddenError, match="not a member of the supergroup"):
            await env.bot.send_message(chat_id=chat.id, text="x")

    async def test_opting_out_lets_it_send(self, world):
        env, chat, _alice = world(status=ChatMemberStatus.KICKED, enforce_bot_rights=False)

        await env.bot.send_message(chat_id=chat.id, text="x")

        assert chat.messages[-1].text == "x"


class TestContentRules:
    async def test_a_live_location_has_its_own_refusal(self, world):
        env, chat, _alice = world(chat_permissions=NO_TEXT)

        with pytest.raises(TelegramBadRequest):
            await env.bot.send_location(
                chat_id=chat.id,
                latitude=1.0,
                longitude=2.0,
                live_period=60,
            )
        with pytest.raises(TelegramBadRequest):
            await env.bot.send_location(chat_id=chat.id, latitude=1.0, longitude=2.0)

    async def test_a_bot_sends_paid_media_without_the_permissions(self, world):
        env, chat, _alice = world(chat_permissions=NO_PHOTOS)

        await env.bot.send_paid_media(
            chat_id=chat.id,
            star_count=1,
            media=[InputPaidMediaPhoto(media="a")],
        )

        assert chat.messages[-1].paid_media is not None

    @pytest.mark.parametrize("missing", ["can_send_photos", "can_send_videos"])
    async def test_forwarded_paid_media_takes_photos_and_videos(self, world, missing):
        everything = {"can_send_messages": True, "can_send_photos": True, "can_send_videos": True}
        env, chat, alice = world(
            chat_permissions=ChatPermissions(**{**everything, missing: False})
        )
        private = env.chat(alice.user.id)
        paid = await env.bot.send_paid_media(
            chat_id=private.id,
            star_count=1,
            media=[InputPaidMediaPhoto(media="a")],
        )

        with pytest.raises(TelegramBadRequest):
            await env.bot.forward_message(
                chat_id=chat.id,
                from_chat_id=private.id,
                message_id=paid.message_id,
            )

    async def test_a_forwarded_live_location_is_named_as_one(self, world):
        env, chat, alice = world(chat_permissions=NO_TEXT)
        private = env.chat(alice.user.id)
        live = await env.bot.send_location(
            chat_id=private.id,
            latitude=1.0,
            longitude=2.0,
            live_period=60,
        )

        with pytest.raises(TelegramBadRequest):
            await env.bot.forward_message(
                chat_id=chat.id,
                from_chat_id=private.id,
                message_id=live.message_id,
            )


class TestHoldsRight:
    def test_a_right_the_chat_type_lacks_is_not_held(self, world):
        env, chat, _alice = world(ChatType.CHANNEL, status=ADMIN)
        bot_id = env.world.bot_user.id

        assert holds_right(chat, bot_id, "can_edit_messages") is True
        assert holds_right(chat, bot_id, "can_pin_messages") is False


class TestMoreRows:
    SUPERGROUP_CALLS = [
        (
            "set_chat_permissions",
            {"permissions": ChatPermissions(can_send_messages=True)},
        ),
        (
            "set_chat_sticker_set",
            {"sticker_set_name": "pack"},
        ),
        ("delete_chat_sticker_set", {}),
        (
            "ban_chat_sender_chat",
            {"sender_chat_id": -100},
        ),
        ("unban_chat_sender_chat", {"sender_chat_id": -100}),
        ("set_chat_member_tag", {"user_id": 1000, "tag": "VIP"}),
    ]

    @pytest.mark.parametrize(("name", "kwargs"), SUPERGROUP_CALLS)
    async def test_a_member_bot_is_refused(self, world, name, kwargs):
        env, chat, _alice = world()

        with pytest.raises(TelegramBadRequest):
            await getattr(env.bot, name)(chat_id=chat.id, **kwargs)

    @pytest.mark.parametrize("name", ["approve_suggested_post", "decline_suggested_post"])
    async def test_a_suggested_post_takes_the_right_to_post(self, world, name):
        env, chat, _alice = world(
            ChatType.CHANNEL,
            rights=administrator_rights(can_post_messages=False),
        )

        with pytest.raises(TelegramBadRequest):
            await getattr(env.bot, name)(chat_id=chat.id, message_id=1)

    async def test_banning_a_basic_groups_owner_is_left_to_the_server(self, dp):
        blueprint = Blueprint()
        owner = blueprint.add_user("Owner")
        chat = blueprint.add_group(
            "G",
            members={owner: ChatMemberStatus.CREATOR},
            bot_status=ADMIN,
        )
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            with pytest.raises(TelegramBadRequest):
                await env.bot.ban_chat_member(chat_id=chat.id, user_id=owner.id)
        finally:
            env.dispose_sync()


class TestRightsBeforeTheTopic:
    async def test_an_unknown_topic_goes_on_to_the_server(self, forum):
        env, chat, _declared, _own = await forum(
            rights=administrator_rights(can_manage_topics=True),
        )

        with pytest.raises(TelegramBadRequest, match="message thread not found"):
            await env.bot.close_forum_topic(chat_id=chat.id, message_thread_id=999)

    @pytest.mark.parametrize(
        ("name", "kwargs", "right"),
        [
            ("edit_forum_topic", {"name": "N"}, "can_manage_topics"),
            ("close_forum_topic", {}, "can_manage_topics"),
            ("reopen_forum_topic", {}, "can_manage_topics"),
            ("delete_forum_topic", {}, "can_delete_messages"),
        ],
    )
    async def test_an_unknown_topic_is_refused_for_the_rights_first(
        self,
        forum,
        name,
        kwargs,
        right,
    ):
        # No topic, so no creator to excuse the bot from the right.
        env, chat, _declared, _own = await forum()
        call = getattr(env.bot, name)

        with pytest.raises(TelegramBadRequest):
            await call(chat_id=chat.id, message_thread_id=999, **kwargs)

        held = administrator_rights(**{right: True})
        env.chat(chat.id).member(env.world.bot_user.id).rights = held
        env.chat(chat.id).member(env.world.bot_user.id).status = ChatMemberStatus.ADMINISTRATOR
        with pytest.raises(TelegramBadRequest, match="message thread not found"):
            await call(chat_id=chat.id, message_thread_id=999, **kwargs)

    async def test_unpinning_an_unknown_topic_is_refused_for_the_rights(self, forum):
        env, chat, _declared, _own = await forum()

        with pytest.raises(TelegramBadRequest):
            await env.bot.unpin_all_forum_topic_messages(
                chat_id=chat.id,
                message_thread_id=999,
            )


class TestStandingComesFirst:
    async def test_a_copy_with_a_missing_reply_is_forbidden(self, world):
        env, chat, alice = world(status=ChatMemberStatus.KICKED)
        private = env.chat(alice.user.id)
        sent = await env.bot.send_message(chat_id=private.id, text="x")

        with pytest.raises(TelegramForbiddenError, match="kicked"):
            await env.bot.copy_message(
                chat_id=chat.id,
                from_chat_id=private.id,
                message_id=sent.message_id,
                reply_parameters=ReplyParameters(message_id=999),
            )

    async def test_a_forward_into_an_unknown_thread_names_the_thread(self, dp):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        private = blueprint.add_private_chat(alice)
        chat = blueprint.add_supergroup("Forum", is_forum=True)
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            with pytest.raises(TelegramBadRequest, match="message thread not found"):
                await env.bot.forward_message(
                    chat_id=chat.id,
                    from_chat_id=private.id,
                    message_id=999,
                    message_thread_id=99,
                )
        finally:
            env.dispose_sync()
