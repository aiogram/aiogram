import pytest

from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import Blueprint, BotTestEnvironment, administrator_rights
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

    async def test_declaring_both_is_ambiguous_even_when_bot_status_is_member(self):
        # `bot_status=MEMBER` is still an explicit choice, not "unset" — it must not
        # silently lose to a contradicting `members` entry.
        blueprint = Blueprint()

        with pytest.raises(ValueError, match="both"):
            blueprint.add_supergroup(
                "Team",
                members={blueprint.bot: ChatMemberStatus.ADMINISTRATOR},
                bot_status=ChatMemberStatus.MEMBER,
            )

    async def test_bot_status_defaults_to_member(self, env, team):
        member = await env.bot.get_chat_member(chat_id=team.id, user_id=env.bot.id)

        assert isinstance(member, ChatMemberMember)

    async def test_an_administrator_declared_without_rights_carries_the_ordinary_ones(
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


class TestDeclaredRights:
    """What a declared member may do, which the status alone does not say."""

    @pytest.fixture
    def rights_env(self, dp):
        blueprint = Blueprint()
        moderator = blueprint.add_user("Moderator")
        team = blueprint.add_supergroup("Team")
        blueprint.set_member(
            team,
            moderator,
            rights=administrator_rights(can_restrict_members=False),
            custom_title="Mod",
        )
        blueprint.set_member(
            team,
            blueprint.bot,
            rights=administrator_rights(can_delete_messages=False),
        )
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            yield environment, team, moderator
        finally:
            environment.dispose_sync()

    async def test_a_partial_rights_admin_reads_back_as_declared(self, rights_env):
        env, team, moderator = rights_env

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=moderator.id)

        assert isinstance(member, ChatMemberAdministrator)
        assert member.can_restrict_members is False
        assert member.can_delete_messages is True
        assert member.custom_title == "Mod"

    async def test_the_bot_can_be_declared_to_lack_a_right(self, rights_env):
        """The case behind every "give me that right" branch a group bot has."""
        env, team, _moderator = rights_env

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=env.bot.id)

        assert member.can_delete_messages is False
        assert member.can_manage_chat is True

    async def test_declared_rights_reach_the_administrator_list(self, rights_env):
        env, team, moderator = rights_env

        admins = await env.bot.get_chat_administrators(chat_id=team.id, return_bots=True)

        assert {admin.user.id: admin.can_delete_messages for admin in admins} == {
            moderator.id: True,
            env.bot.id: False,
        }

    async def test_a_restricted_member_can_be_declared(self, dp):
        blueprint = Blueprint()
        quiet = blueprint.add_user("Quiet")
        team = blueprint.add_supergroup("Team")
        blueprint.set_member(
            team,
            quiet,
            permissions=ChatPermissions(can_send_messages=False, can_send_polls=True),
        )
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            member = await env.bot.get_chat_member(chat_id=team.id, user_id=quiet.id)

            assert member.status == ChatMemberStatus.RESTRICTED
            assert member.can_send_messages is False
            assert member.can_send_polls is True
        finally:
            env.dispose_sync()

    async def test_amending_a_member_declared_by_the_shorthand(self, dp):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        team = blueprint.add_supergroup("Team", members={alice: ChatMemberStatus.ADMINISTRATOR})
        blueprint.set_member(team, alice, tag="VIP", status=ChatMemberStatus.MEMBER)
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            member = await env.bot.get_chat_member(chat_id=team.id, user_id=alice.id)

            assert len([item for item in team.members if item.user_id == alice.id]) == 1
            assert isinstance(member, ChatMemberMember)
            assert member.tag == "VIP"
        finally:
            env.dispose_sync()

    def test_rights_and_permissions_belong_to_different_statuses(self):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        team = blueprint.add_supergroup("Team")

        with pytest.raises(ValueError, match="only one of them"):
            blueprint.set_member(
                team,
                alice,
                rights=administrator_rights(),
                permissions=ChatPermissions(),
            )


class TestRightsFollowTheChatType:
    """The Bot API reports some rights only in some chat types, and so does the world."""

    @pytest.fixture
    def typed_env(self, dp):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        supergroup = blueprint.add_supergroup(
            "Team",
            members={alice: ChatMemberStatus.ADMINISTRATOR},
        )
        channel = blueprint.add_channel("News", members={alice: ChatMemberStatus.ADMINISTRATOR})
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            yield environment, supergroup, channel, alice
        finally:
            environment.dispose_sync()

    async def test_a_supergroup_administrator(self, typed_env):
        env, supergroup, _channel, alice = typed_env

        member = await env.bot.get_chat_member(chat_id=supergroup.id, user_id=alice.id)

        assert member.can_manage_topics is True
        assert member.can_pin_messages is True
        assert member.can_post_messages is None
        assert member.can_edit_messages is None

    async def test_a_channel_administrator(self, typed_env):
        env, _supergroup, channel, alice = typed_env

        member = await env.bot.get_chat_member(chat_id=channel.id, user_id=alice.id)

        assert member.can_post_messages is True
        assert member.can_edit_messages is True
        assert member.can_manage_topics is None
        assert member.can_pin_messages is None

    async def test_promoted_rights_are_scoped_too(self, typed_env):
        """A right granted where it cannot exist is not reported back as if it did."""
        env, supergroup, _channel, alice = typed_env

        await env.bot.promote_chat_member(
            chat_id=supergroup.id,
            user_id=alice.id,
            can_post_messages=True,
            can_manage_topics=True,
        )
        member = await env.bot.get_chat_member(chat_id=supergroup.id, user_id=alice.id)

        assert member.can_post_messages is None
        assert member.can_manage_topics is True


class TestPromoteAndRestrictPersist:
    @pytest.fixture
    def owned(self):
        """A supergroup with a declared owner, plus the environment it lives in."""
        blueprint = Blueprint()
        owner = blueprint.add_user("Owner")
        team = blueprint.add_supergroup("Team", members={owner: ChatMemberStatus.CREATOR})
        environment = BotTestEnvironment(blueprint=blueprint)
        try:
            yield environment, team, owner
        finally:
            environment.dispose_sync()

    async def test_promote_grants_exactly_what_was_asked_for(self, env, team, alice):
        await env.bot.promote_chat_member(
            chat_id=team.id,
            user_id=alice.user.id,
            can_pin_messages=True,
        )

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=alice.user.id)

        assert isinstance(member, ChatMemberAdministrator)
        assert member.can_pin_messages is True
        # Not asked for, so not granted — `promoteChatMember` sets the whole mask.
        assert member.can_delete_messages is False
        assert member.can_manage_chat is False

    async def test_a_second_promotion_replaces_the_first(self, env, team, alice):
        await env.bot.promote_chat_member(
            chat_id=team.id,
            user_id=alice.user.id,
            can_delete_messages=True,
        )

        await env.bot.promote_chat_member(
            chat_id=team.id,
            user_id=alice.user.id,
            can_invite_users=True,
        )

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=alice.user.id)
        assert member.can_invite_users is True
        assert member.can_delete_messages is False

    async def test_promoting_only_is_anonymous_keeps_the_administrator(self, env, team, alice):
        """Hiding an administrator is a right like any other, not a demotion."""
        await env.bot.promote_chat_member(
            chat_id=team.id,
            user_id=alice.user.id,
            is_anonymous=True,
        )

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=alice.user.id)

        assert isinstance(member, ChatMemberAdministrator)
        assert member.is_anonymous is True

    @pytest.mark.parametrize(
        "kwargs",
        [
            pytest.param({}, id="nothing-passed"),
            pytest.param(
                {"can_delete_messages": False, "can_pin_messages": False},
                id="explicitly-false",
            ),
        ],
    )
    async def test_a_promotion_that_grants_nothing_demotes(self, env, team, alice, kwargs):
        await env.bot.promote_chat_member(chat_id=team.id, user_id=alice.user.id, **kwargs)

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=alice.user.id)

        assert isinstance(member, ChatMemberMember)

    async def test_a_demoted_administrator_can_be_promoted_again(self, env, team, alice):
        await env.bot.promote_chat_member(chat_id=team.id, user_id=alice.user.id)

        await env.bot.promote_chat_member(
            chat_id=team.id,
            user_id=alice.user.id,
            can_manage_chat=True,
        )

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=alice.user.id)
        assert member.can_manage_chat is True
        assert member.can_delete_messages is False

    async def test_the_chat_owner_cannot_be_promoted(self, owned):
        """
        Telegram refuses; without the guard the fake was more permissive than the API.

        And permissive in the one direction a test cannot notice: a bot that promotes a
        list of users would quietly turn the owner into an administrator here, keep passing,
        and fail only in production.
        """
        env, team, owner = owned

        with pytest.raises(TelegramBadRequest, match="can't remove chat owner"):
            await env.bot.promote_chat_member(
                chat_id=team.id,
                user_id=owner.id,
                can_delete_messages=True,
            )

        assert env.chat(team.id).member(owner.id).status == ChatMemberStatus.CREATOR

    async def test_the_chat_owner_cannot_be_demoted_either(self, owned):
        """A promotion granting nothing is a demotion, and the owner is not demotable."""
        env, team, owner = owned

        with pytest.raises(TelegramBadRequest, match="can't remove chat owner"):
            await env.bot.promote_chat_member(chat_id=team.id, user_id=owner.id)

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=owner.id)
        assert member.status == ChatMemberStatus.CREATOR

    async def test_restrict_persists_the_permissions_it_was_given(self, env, team, alice):
        await env.bot.restrict_chat_member(
            chat_id=team.id,
            user_id=alice.user.id,
            permissions=ChatPermissions(can_send_messages=True, can_send_photos=True),
        )

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=alice.user.id)

        assert member.status == ChatMemberStatus.RESTRICTED
        assert member.can_send_messages is True
        assert member.can_send_photos is True
        assert member.can_send_polls is False

    async def test_restrict_does_not_keep_the_callers_permissions_object(self, env, team, alice):
        """A shared constant stays what the test wrote, whatever the world does with it."""
        await env.bot.restrict_chat_member(
            chat_id=team.id,
            user_id=alice.user.id,
            permissions=SILENCED,
        )

        assert team.member(alice.user.id).permissions is not SILENCED
        assert SILENCED.can_send_messages is False
        assert SILENCED.bot is None

    async def test_restricting_an_administrator_drops_their_rights(self, env, team, alice):
        await env.bot.restrict_chat_member(
            chat_id=team.id,
            user_id=alice.user.id,
            permissions=SILENCED,
        )
        await env.bot.promote_chat_member(
            chat_id=team.id,
            user_id=alice.user.id,
            can_pin_messages=True,
        )

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=alice.user.id)

        assert isinstance(member, ChatMemberAdministrator)
        assert member.can_pin_messages is True


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
