import pytest

from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import Blueprint, BotTestEnvironment
from aiogram.types import (
    ChatMemberAdministrator,
    ChatMemberMember,
    ChatPermissions,
    ChatPhoto,
)

SILENCED = ChatPermissions(can_send_messages=False, can_send_other_messages=False)


class TestChatMetadata:
    async def test_renaming_is_visible_to_get_chat(self, env, team):
        await env.bot.set_chat_title(chat_id=team.id, title="Renamed")

        assert (await env.bot.get_chat(chat_id=team.id)).title == "Renamed"

    async def test_description_and_permissions_round_trip(self, env, team):
        await env.bot.set_chat_description(chat_id=team.id, description="Our team")
        await env.bot.set_chat_permissions(chat_id=team.id, permissions=SILENCED)

        chat = await env.bot.get_chat(chat_id=team.id)

        assert chat.description == "Our team"
        assert chat.permissions.can_send_messages is False

    async def test_sticker_set_round_trips_and_clears(self, env, team):
        await env.bot.set_chat_sticker_set(chat_id=team.id, sticker_set_name="pack")
        assert (await env.bot.get_chat(chat_id=team.id)).sticker_set_name == "pack"

        await env.bot.delete_chat_sticker_set(chat_id=team.id)

        assert (await env.bot.get_chat(chat_id=team.id)).sticker_set_name is None

    async def test_clearing_a_sticker_set_that_was_never_set_is_a_no_op(self, env, team):
        assert await env.bot.delete_chat_sticker_set(chat_id=team.id) is True

    async def test_other_chats_are_unaffected(self, env, team, private):
        await env.bot.set_chat_description(chat_id=team.id, description="Our team")

        assert (await env.bot.get_chat(chat_id=private.id)).description is None

    async def test_administering_an_unknown_chat_fails(self, env):
        with pytest.raises(TelegramBadRequest, match="chat not found"):
            await env.bot.set_chat_title(chat_id=-99, title="Nope")

    @pytest.mark.parametrize(
        ("method_name", "kwargs"),
        [
            ("set_chat_title", {"title": "Nope"}),
            ("set_chat_description", {"description": "Nope"}),
            ("set_chat_permissions", {"permissions": SILENCED}),
            ("set_chat_sticker_set", {"sticker_set_name": "pack"}),
            ("delete_chat_sticker_set", {}),
            ("delete_chat_photo", {}),
        ],
    )
    async def test_administering_a_private_chat_fails(self, env, private, method_name, kwargs):
        with pytest.raises(TelegramBadRequest, match="supergroup and channel chats only"):
            await getattr(env.bot, method_name)(chat_id=private.id, **kwargs)


class TestChatPhoto:
    @pytest.fixture
    def photographed(self, dp):
        blueprint = Blueprint()
        chat = blueprint.add_supergroup("Team")
        chat.photo = ChatPhoto(
            small_file_id="s",
            small_file_unique_id="su",
            big_file_id="b",
            big_file_unique_id="bu",
        )
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            yield environment, environment.chat(chat)
        finally:
            environment.dispose_sync()

    async def test_a_declared_photo_reaches_get_chat(self, photographed):
        env, chat = photographed

        assert (await env.bot.get_chat(chat_id=chat.id)).photo is not None

    async def test_deleting_clears_it(self, photographed):
        env, chat = photographed

        await env.bot.delete_chat_photo(chat_id=chat.id)

        assert (await env.bot.get_chat(chat_id=chat.id)).photo is None


class TestServiceMessages:
    async def test_a_rename_posts_a_service_message(self, env, team):
        await env.bot.set_chat_title(chat_id=team.id, title="Renamed")

        assert team.messages[-1].new_chat_title == "Renamed"
        assert team.messages[-1].message_id > 0

    async def test_a_photo_deletion_posts_a_service_message(self, env, team):
        await env.bot.delete_chat_photo(chat_id=team.id)

        assert team.messages[-1].delete_chat_photo is True

    async def test_the_service_message_reaches_a_handler(self, env, team, alice):
        seen = []
        env.dispatcher.message.register(lambda message: seen.append(message.new_chat_title))
        await alice.in_(team).send("trigger the routing")

        await env.bot.set_chat_title(chat_id=team.id, title="Renamed")
        await alice.in_(team).send("and again")

        # The service message is stored; the chat now holds it alongside the two sends.
        assert [message.new_chat_title for message in team.messages] == [
            None,
            "Renamed",
            None,
        ]

    async def test_setting_a_description_posts_nothing(self, env, team):
        await env.bot.set_chat_description(chat_id=team.id, description="Our team")

        assert team.messages == []


class TestMembershipReads:
    async def test_promoting_changes_the_administrator_list(self, env, team, alice):
        await env.bot.promote_chat_member(
            chat_id=team.id,
            user_id=alice.user.id,
            can_delete_messages=True,
        )

        admins = await env.bot.get_chat_administrators(chat_id=team.id)

        assert alice.user.id in {admin.user.id for admin in admins}

    async def test_the_creator_comes_first(self, dp):
        blueprint = Blueprint()
        owner = blueprint.add_user("Owner")
        admin = blueprint.add_user("Admin")
        team = blueprint.add_supergroup(
            "Team",
            members={owner: ChatMemberStatus.CREATOR, admin: ChatMemberStatus.ADMINISTRATOR},
        )
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            admins = await env.bot.get_chat_administrators(chat_id=team.id)

            assert [item.user.id for item in admins] == [owner.id, admin.id]
        finally:
            env.dispose_sync()

    async def test_other_bots_are_omitted_unless_asked_for(self, dp):
        blueprint = Blueprint()
        other_bot = blueprint.add_user("Helper")
        other_bot.is_bot = True
        team = blueprint.add_supergroup(
            "Team",
            members={other_bot: ChatMemberStatus.ADMINISTRATOR},
        )
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            without = await env.bot.get_chat_administrators(chat_id=team.id)
            with_bots = await env.bot.get_chat_administrators(chat_id=team.id, return_bots=True)

            assert other_bot.id not in {item.user.id for item in without}
            assert other_bot.id in {item.user.id for item in with_bots}
        finally:
            env.dispose_sync()

    async def test_member_count_follows_membership_changes(self, env, team, alice):
        before = await env.bot.get_chat_member_count(chat_id=team.id)

        await env.bot.ban_chat_member(chat_id=team.id, user_id=alice.user.id)

        assert await env.bot.get_chat_member_count(chat_id=team.id) == before - 1

    @pytest.mark.parametrize(
        "method_name",
        ["get_chat_member_count", "get_chat_administrators"],
    )
    async def test_reading_an_unknown_chat_fails(self, env, method_name):
        with pytest.raises(TelegramBadRequest, match="chat not found"):
            await getattr(env.bot, method_name)(chat_id=-99)


class TestMemberAnnotations:
    async def test_custom_title_round_trips(self, env, team, alice):
        await env.bot.set_chat_administrator_custom_title(
            chat_id=team.id,
            user_id=alice.user.id,
            custom_title="Boss",
        )

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=alice.user.id)

        assert member.custom_title == "Boss"

    async def test_a_custom_title_for_an_ordinary_member_fails(self, env, team, alice):
        await env.bot.restrict_chat_member(
            chat_id=team.id,
            user_id=alice.user.id,
            permissions=SILENCED,
        )

        with pytest.raises(TelegramBadRequest, match="not an administrator"):
            await env.bot.set_chat_administrator_custom_title(
                chat_id=team.id,
                user_id=alice.user.id,
                custom_title="Boss",
            )

    async def test_member_tag_round_trips(self, dp):
        blueprint = Blueprint()
        member = blueprint.add_user("Member")
        team = blueprint.add_supergroup("Team", members={member: ChatMemberStatus.MEMBER})
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            await env.bot.set_chat_member_tag(chat_id=team.id, user_id=member.id, tag="VIP")

            stored = await env.bot.get_chat_member(chat_id=team.id, user_id=member.id)

            assert stored.tag == "VIP"
        finally:
            env.dispose_sync()

    async def test_a_tag_on_an_administrator_fails(self, env, team, alice):
        """A tag belongs to a regular member; an administrator carries a custom title."""
        with pytest.raises(TelegramBadRequest, match="not a regular member"):
            await env.bot.set_chat_member_tag(
                chat_id=team.id,
                user_id=alice.user.id,
                tag="VIP",
            )

    async def test_annotating_an_unknown_user_fails(self, env, team):
        with pytest.raises(TelegramBadRequest, match="not declared in the blueprint"):
            await env.bot.set_chat_member_tag(chat_id=team.id, user_id=424242, tag="VIP")


class TestBotAdminStatus:
    async def test_bot_status_can_be_declared_as_administrator(self, dp):
        blueprint = Blueprint()
        team = blueprint.add_supergroup("Team", bot_status=ChatMemberStatus.ADMINISTRATOR)
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            member = await env.bot.get_chat_member(chat_id=team.id, user_id=env.bot.id)

            assert isinstance(member, ChatMemberAdministrator)
            assert [m.user_id for m in blueprint.chats[0].members].count(env.bot.id) == 1
        finally:
            env.dispose_sync()

    async def test_bot_can_be_declared_admin_via_members(self, dp):
        blueprint = Blueprint()
        team = blueprint.add_supergroup(
            "Team",
            members={blueprint.bot: ChatMemberStatus.ADMINISTRATOR},
        )
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            member = await env.bot.get_chat_member(chat_id=team.id, user_id=env.bot.id)

            assert isinstance(member, ChatMemberAdministrator)
            assert [m.user_id for m in blueprint.chats[0].members].count(env.bot.id) == 1
        finally:
            env.dispose_sync()

    async def test_declaring_both_is_ambiguous(self):
        blueprint = Blueprint()

        with pytest.raises(ValueError, match="both"):
            blueprint.add_supergroup(
                "Team",
                members={blueprint.bot: ChatMemberStatus.ADMINISTRATOR},
                bot_status=ChatMemberStatus.CREATOR,
            )

    async def test_bot_status_defaults_to_member(self, env, team):
        member = await env.bot.get_chat_member(chat_id=team.id, user_id=env.bot.id)

        assert isinstance(member, ChatMemberMember)

    async def test_the_synthesized_administrator_carries_ordinary_admin_rights(
        self,
        env,
        team,
        alice,
    ):
        """A bot/user admin checked for a specific right must pass that check."""
        member = await env.bot.get_chat_member(chat_id=team.id, user_id=alice.user.id)

        assert isinstance(member, ChatMemberAdministrator)
        assert member.can_pin_messages is True
        assert member.can_manage_topics is True


class TestPermissionsAreNotEnforced:
    async def test_a_silenced_chat_still_accepts_messages(self, env, team, alice):
        """The fake models the shape of administration, not its policy."""
        await env.bot.set_chat_permissions(chat_id=team.id, permissions=SILENCED)

        await env.bot.send_message(chat_id=team.id, text="still sent")
        await alice.in_(team).send("so is this")

        assert [message.text for message in team.messages] == ["still sent", "so is this"]

    async def test_a_restricted_member_can_still_send(self, env, team, alice):
        await env.bot.restrict_chat_member(
            chat_id=team.id,
            user_id=alice.user.id,
            permissions=SILENCED,
        )

        await alice.in_(team).send("still sent")

        assert team.messages[-1].text == "still sent"
