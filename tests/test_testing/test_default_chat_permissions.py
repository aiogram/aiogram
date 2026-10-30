import pytest

from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import (
    Blueprint,
    BotTestEnvironment,
    ChatSpec,
    default_chat_permissions,
    rejections,
)
from aiogram.test.world import granted_permissions
from aiogram.types import ChatPermissions

from .conftest import refused_with


@pytest.fixture
def make(dp):
    environments = []

    def build(**chats):
        blueprint = Blueprint()
        blueprint.add_user("Alice")
        specs = {name: add(blueprint) for name, add in chats.items()}
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        environments.append(env)
        return env, specs

    yield build
    for env in environments:
        env.dispose_sync()


class TestTheDefault:
    def test_every_member_permission_is_granted(self):
        permissions = default_chat_permissions()

        values = {name: getattr(permissions, name) for name in ChatPermissions.model_fields}
        assert set(values.values()) == {True}

    def test_it_is_what_the_api_would_store(self):
        permissions = default_chat_permissions()

        assert granted_permissions(permissions, None) == permissions
        assert granted_permissions(permissions, True) == permissions

    def test_every_call_is_a_new_object(self):
        first = default_chat_permissions()
        first.can_send_polls = False

        assert default_chat_permissions().can_send_polls is True


class TestWhatAChatReports:
    @pytest.mark.parametrize("kind", ["add_group", "add_supergroup"])
    async def test_a_group_reports_the_defaults(self, make, kind):
        env, specs = make(chat=getattr(Blueprint, kind))

        info = await env.bot.get_chat(chat_id=specs["chat"].id)

        assert info.permissions.model_dump() == default_chat_permissions().model_dump()
        assert env.chat(specs["chat"]).permissions == default_chat_permissions()

    async def test_a_private_chat_and_a_channel_have_none(self, make):
        def private(blueprint):
            return blueprint.add_private_chat(blueprint.users[0])

        env, specs = make(private=private, channel=Blueprint.add_channel)

        assert env.chat(specs["private"]).permissions is None
        assert env.chat(specs["channel"]).permissions is None

    @pytest.mark.parametrize("kind", ["add_group", "add_supergroup"])
    async def test_the_blueprint_overrides_them(self, make, kind):
        declared = ChatPermissions(can_send_messages=True, can_send_photos=False)

        env, specs = make(chat=lambda b: getattr(b, kind)("Chat", permissions=declared))

        info = await env.bot.get_chat(chat_id=specs["chat"].id)
        assert info.permissions.model_dump() == granted_permissions(declared, None).model_dump()
        assert info.permissions.can_send_photos is False
        assert info.permissions.can_pin_messages is None

    async def test_one_permission_changed_from_the_defaults(self, make):
        changed = default_chat_permissions().model_copy(update={"can_send_polls": False})

        env, specs = make(chat=lambda b: b.add_supergroup("Chat", permissions=changed))

        reported = (await env.bot.get_chat(chat_id=specs["chat"].id)).permissions
        assert reported.can_send_polls is False
        assert reported.can_send_messages is True

    async def test_a_hand_built_group_spec_gets_them_too(self, dp):
        blueprint = Blueprint()
        blueprint.chats.append(ChatSpec(id=-5, type=ChatType.GROUP, title="Hand"))
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            assert env.chat(-5).permissions == default_chat_permissions()
        finally:
            env.dispose_sync()

    async def test_setting_the_permissions_replaces_them(self, make):
        env, specs = make(chat=lambda b: b.add_supergroup("Chat", bot_status="administrator"))
        chat = specs["chat"]

        await env.bot.set_chat_permissions(
            chat_id=chat.id,
            permissions=ChatPermissions(can_send_messages=False),
        )

        assert env.chat(chat).permissions.can_send_messages is False
        assert env.chat(chat).permissions.can_invite_users is None


class TestTheSameValueIsEnforced:
    @pytest.fixture
    def member_bot(self, make):
        env, specs = make(chat=lambda b: b.add_supergroup("Chat"))
        return env, env.chat(specs["chat"])

    async def test_a_plain_member_bot_sends_what_the_defaults_allow(self, member_bot):
        env, chat = member_bot

        await env.bot.send_message(chat_id=chat.id, text="x")
        await env.bot.send_poll(chat_id=chat.id, question="q", options=["a", "b"])
        await env.bot.send_dice(chat_id=chat.id)

    async def test_what_the_chat_stopped_allowing_is_refused(self, member_bot):
        env, chat = member_bot
        chat.permissions = chat.permissions.model_copy(update={"can_send_polls": False})

        with refused_with(TelegramBadRequest, rejections.NO_RIGHTS_TO_SEND, noun="polls"):
            await env.bot.send_poll(chat_id=chat.id, question="q", options=["a", "b"])

    async def test_the_chat_defaults_bound_a_restricted_bot_too(self, make):
        denied = default_chat_permissions().model_copy(update={"can_send_polls": False})
        env, specs = make(
            chat=lambda b: b.add_supergroup("Chat", permissions=denied),
        )
        chat = env.chat(specs["chat"])
        chat.member(env.world.bot_user.id).set_status(ChatMemberStatus.RESTRICTED)
        chat.member(env.world.bot_user.id).permissions = granted_permissions(
            ChatPermissions(can_send_messages=True, can_send_polls=True),
            None,
        )

        await env.bot.send_message(chat_id=chat.id, text="x")
        with refused_with(TelegramBadRequest, rejections.NO_RIGHTS_TO_SEND, noun="polls"):
            await env.bot.send_poll(chat_id=chat.id, question="q", options=["a", "b"])

    async def test_restricting_with_the_defaults_restricts_nothing(self, make):
        env, specs = make(chat=lambda b: b.add_supergroup("Chat", bot_status="administrator"))
        chat = env.chat(specs["chat"])
        alice = next(iter(env.world.users.values()))
        await env.bot.restrict_chat_member(
            chat_id=chat.id,
            user_id=alice.id,
            permissions=default_chat_permissions(),
        )

        # Granting every permission lifts a restriction: none is made.
        assert chat.member(alice.id).status != ChatMemberStatus.RESTRICTED
        assert chat.member(alice.id).permissions is None
