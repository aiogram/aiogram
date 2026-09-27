import pytest

from aiogram import F
from aiogram.enums import ChatMemberStatus
from aiogram.test import Blueprint, BotTestEnvironment, WorldLookupError
from aiogram.types import ChatMemberAdministrator, ChatMemberMember


class TestPromote:
    async def test_promoting_the_bot_is_the_default(self, env, dp, team, alice):
        """`admin.in_(group).promote()` — their main case: no subject names the bot."""
        seen = []
        dp.my_chat_member.register(lambda event: seen.append(event.new_chat_member))

        await alice.in_(team).promote(can_delete_messages=True)

        assert isinstance(seen[-1], ChatMemberAdministrator)
        assert seen[-1].can_delete_messages is True
        assert team.member(env.world.bot_user.id).status == ChatMemberStatus.ADMINISTRATOR

    async def test_promoting_a_named_user_produces_chat_member(self, env, dp, team, alice):
        bob = env.world.bot_user
        seen_mine, seen_others = [], []
        dp.my_chat_member.register(seen_mine.append)
        dp.chat_member.register(lambda event: seen_others.append(event.new_chat_member))

        await alice.in_(team).promote(subject=alice.user, can_pin_messages=True)

        assert seen_mine == []
        assert isinstance(seen_others[-1], ChatMemberAdministrator)
        assert seen_others[-1].can_pin_messages is True
        assert team.member(alice.user.id).status == ChatMemberStatus.ADMINISTRATOR
        # Untouched: promoting alice must not have promoted the bot too.
        assert team.member(bob.id).status != ChatMemberStatus.ADMINISTRATOR

    async def test_promoting_a_bare_id_resolves_through_the_world(self, env, team, alice):
        await alice.in_(team).promote(subject=alice.user.id, can_invite_users=True)

        member = team.member(alice.user.id)
        assert member.status == ChatMemberStatus.ADMINISTRATOR
        assert member.rights.can_invite_users is True

    async def test_only_the_named_rights_are_granted(self, env, team, alice):
        """Exactly like `promoteChatMember`: the mask is whole, not additive."""
        await alice.in_(team).promote(can_delete_messages=True)

        member = team.member(env.world.bot_user.id)
        assert member.rights.can_delete_messages is True
        assert member.rights.can_pin_messages is False
        assert member.rights.can_invite_users is False

    async def test_no_rights_at_all_still_promotes(self, env, team, alice):
        """
        Unlike a bare `promoteChatMember(...)`, this does not read as a demotion — there
        is no way to "explicitly ask for nothing" here, so nothing asked for is simply
        nothing granted, not a request to leave the administrator status.
        """
        await alice.in_(team).promote()

        member = team.member(env.world.bot_user.id)
        assert member.status == ChatMemberStatus.ADMINISTRATOR
        assert member.rights.can_delete_messages is False

    async def test_a_second_promotion_replaces_the_first(self, env, team, alice):
        await alice.in_(team).promote(can_delete_messages=True)

        await alice.in_(team).promote(can_invite_users=True)

        member = team.member(env.world.bot_user.id)
        assert member.rights.can_invite_users is True
        assert member.rights.can_delete_messages is False

    async def test_old_and_new_chat_member_are_truthful(self, env, dp, team, alice):
        seen = []
        dp.my_chat_member.register(seen.append)

        await alice.in_(team).promote(can_pin_messages=True)

        event = seen[-1]
        assert isinstance(event.old_chat_member, ChatMemberMember)
        assert isinstance(event.new_chat_member, ChatMemberAdministrator)
        assert event.new_chat_member.can_pin_messages is True


class TestDemote:
    async def test_demoting_the_bot_is_the_default(self, env, dp, team, alice):
        await alice.in_(team).promote(can_pin_messages=True)
        seen = []
        dp.my_chat_member.register(lambda event: seen.append(event.new_chat_member))

        await alice.in_(team).demote()

        assert isinstance(seen[-1], ChatMemberMember)
        assert team.member(env.world.bot_user.id).status == ChatMemberStatus.MEMBER

    async def test_demotion_clears_rights_and_custom_title(self, env, team, alice):
        await alice.in_(team).promote(can_pin_messages=True)
        await env.bot.set_chat_administrator_custom_title(
            chat_id=team.id,
            user_id=env.world.bot_user.id,
            custom_title="Boss",
        )

        await alice.in_(team).demote()

        member = team.member(env.world.bot_user.id)
        assert member.rights is None
        assert member.custom_title is None

        # A later promotion does not resurrect the dropped title.
        await alice.in_(team).promote(can_pin_messages=True)
        assert team.member(env.world.bot_user.id).custom_title is None

    async def test_demotion_keeps_the_tag(self, env, team, alice):
        team.member(env.world.bot_user.id).tag = "veteran"
        await alice.in_(team).promote(can_pin_messages=True)

        await alice.in_(team).demote()

        assert team.member(env.world.bot_user.id).tag == "veteran"

    async def test_demoting_a_named_user(self, env, team, alice):
        await alice.in_(team).promote(subject=alice.user, can_pin_messages=True)

        await alice.in_(team).demote(subject=alice.user)

        assert team.member(alice.user.id).status == ChatMemberStatus.MEMBER


class TestOwnerGuard:
    @pytest.fixture
    def owned(self, dp):
        blueprint = Blueprint()
        owner = blueprint.add_user("Owner")
        admin = blueprint.add_user("Admin")
        team = blueprint.add_supergroup(
            "Team",
            members={owner: ChatMemberStatus.CREATOR, admin: ChatMemberStatus.ADMINISTRATOR},
        )
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            yield (
                environment,
                environment.chat(team),
                environment.user(owner),
                environment.user(admin),
            )
        finally:
            environment.dispose_sync()

    async def test_the_owner_cannot_be_promoted(self, owned):
        env, team, owner, admin = owned

        # A `WorldLookupError`, not an `ApiRejection`: a trigger arranges the world, and
        # arranging something Telegram would never allow is the test's own setup bug — not
        # a modeled refusal the bot under test could catch.
        with pytest.raises(WorldLookupError, match="can't remove chat owner"):
            await admin.in_(team).promote(subject=owner.user, can_delete_messages=True)

        assert team.member(owner.user.id).status == ChatMemberStatus.CREATOR

    async def test_the_owner_cannot_be_demoted(self, owned):
        env, team, owner, admin = owned

        with pytest.raises(WorldLookupError, match="can't remove chat owner"):
            await admin.in_(team).demote(subject=owner.user)

        assert team.member(owner.user.id).status == ChatMemberStatus.CREATOR

    async def test_the_owner_can_promote_someone_else(self, owned):
        """The guard is about the target being promoted/demoted, not about who acts."""
        env, team, owner, admin = owned

        await owner.in_(team).promote(subject=admin.user, can_delete_messages=True)

        assert team.member(admin.user.id).status == ChatMemberStatus.ADMINISTRATOR


class TestNewChatMembersServiceMessage:
    """Item 2: `add_bot()`/`join()` also produce the `new_chat_members` service message."""

    async def test_add_bot_feeds_a_welcome_reachable_service_message(self, env, dp, team, alice):
        welcomed = []

        @dp.message(F.new_chat_members)
        async def welcome(message):
            welcomed.append([user.id for user in message.new_chat_members])

        await alice.in_(team).add_bot()

        assert welcomed == [[env.world.bot_user.id]]
        assert [user.id for user in team.messages[-1].new_chat_members] == [env.world.bot_user.id]

    async def test_join_feeds_the_service_message_too(self, env, dp, team, alice):
        welcomed = []
        dp.message.register(
            lambda message: welcomed.append([user.id for user in message.new_chat_members]),
            F.new_chat_members,
        )

        await alice.in_(team).join()

        assert welcomed == [[alice.user.id]]

    async def test_membership_update_arrives_before_the_service_message(
        self, env, dp, team, alice
    ):
        """Documented order: the membership transition, then the group's own announcement."""
        seen = []
        dp.my_chat_member.register(lambda event: seen.append("my_chat_member"))
        dp.message.register(lambda message: seen.append("service_message"), F.new_chat_members)

        await alice.in_(team).add_bot()

        assert seen == ["my_chat_member", "service_message"]

    async def test_the_bots_return_value_is_unaffected_by_the_service_message(
        self, env, dp, team, alice
    ):
        dp.my_chat_member.register(lambda event: "membership-result")
        dp.message.register(lambda message: "service-result", F.new_chat_members)

        assert await alice.in_(team).add_bot() == "membership-result"

    async def test_a_private_chat_gets_no_service_message(self, env, dp, private, alice):
        """Real Telegram never sends `new_chat_members` for a private chat."""
        messages_before = len(private.messages)

        await alice.add_bot()

        assert len(private.messages) == messages_before

    async def test_service_message_can_be_suppressed(self, env, team, alice):
        messages_before = len(team.messages)

        await alice.in_(team).add_bot(service_message=False)

        assert len(team.messages) == messages_before

    async def test_service_message_can_be_suppressed_for_join(self, env, team, alice):
        messages_before = len(team.messages)

        await alice.in_(team).join(service_message=False)

        assert len(team.messages) == messages_before

    async def test_leave_and_remove_bot_are_unaffected(self, env, team, alice):
        """Only join()/add_bot() gained a service message; leave()/remove_bot() did not."""
        await alice.in_(team).add_bot(service_message=False)
        messages_before = len(team.messages)

        await alice.in_(team).remove_bot()
        await alice.in_(team).leave()

        assert len(team.messages) == messages_before


class TestPromoteRightsAreValidated:
    """
    ``**rights`` is a wide-open keyword space, and a typo in it used to grant nothing.

    :func:`aiogram.test.world.mask` reads the fields it knows off the namespace and ignores
    the rest, so ``promote(can_pin_message=True)`` produced an administrator who could not
    pin — and the test then failed on the bot's "you are missing a right" branch, which is
    the correct behavior for the world it was actually handed and says nothing at all about
    the typo.
    """

    async def test_a_misspelled_right_names_itself(self, env, team, alice):
        with pytest.raises(TypeError) as failure:
            await alice.in_(team).promote(can_pin_message=True)

        message = str(failure.value)
        assert "can_pin_message" in message
        assert "can_pin_messages" in message
        assert "known rights:" in message

    async def test_several_typos_are_all_reported(self, env, team, alice):
        with pytest.raises(TypeError, match="can_delete, can_pin"):
            await alice.in_(team).promote(can_pin=True, can_delete=True)

    async def test_a_real_right_is_still_granted(self, env, team, alice):
        await alice.in_(team).promote(can_pin_messages=True)

        rights = team.member(env.world.bot_user.id).rights
        assert rights.can_pin_messages is True

    async def test_the_typo_is_refused_before_the_world_changes(self, env, team, alice):
        """A rejected call must not leave a half-applied promotion behind."""
        before = team.member(env.world.bot_user.id).status

        with pytest.raises(TypeError):
            await alice.in_(team).promote(can_pin_message=True)

        assert team.member(env.world.bot_user.id).status == before


class TestMembershipTriggerDispatcherData:
    """
    ``promote`` claims ``**kwargs`` for rights, so both twins spell dispatcher data
    ``data=``.

    The asymmetry that made this worth resolving rather than documenting: the same keyword
    meant "a right" on one method and "dispatcher data" on the other, and ``promote`` could
    not pass dispatcher data at all.
    """

    async def test_promote_passes_dispatcher_data(self, env, dp, team, alice):
        seen = {}

        @dp.my_chat_member()
        async def on_promoted(event, ledger):
            seen["ledger"] = ledger

        await alice.in_(team).promote(can_pin_messages=True, data={"ledger": "the-ledger"})

        assert seen["ledger"] == "the-ledger"

    async def test_demote_passes_dispatcher_data(self, env, dp, team, alice):
        seen = {}

        @dp.my_chat_member()
        async def on_demoted(event, ledger):
            seen["ledger"] = ledger

        await alice.in_(team).promote(can_pin_messages=True, data={"ledger": "setup"})
        await alice.in_(team).demote(data={"ledger": "the-ledger"})

        assert seen["ledger"] == "the-ledger"

    async def test_the_data_reaches_the_service_message_update_too(self, env, dp, blueprint):
        """A trigger's two updates carry the same data, as they always did."""
        seen = []

        @dp.message(F.new_chat_members)
        async def on_joined(message, ledger):
            seen.append(ledger)

        member = env.user(blueprint.users[0]).in_(blueprint.chats[1])
        await member.join(ledger="the-ledger")

        assert seen == ["the-ledger"]
