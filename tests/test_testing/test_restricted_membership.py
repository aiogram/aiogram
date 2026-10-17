import datetime

import pytest

from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import Blueprint, BotTestEnvironment, WorldLookupError
from aiogram.test.world import UNTIL_FOREVER
from aiogram.types import ChatPermissions

EVERYTHING = ChatPermissions(**dict.fromkeys(ChatPermissions.model_fields, True))
LATER = datetime.datetime(2030, 1, 1, tzinfo=datetime.timezone.utc)


@pytest.fixture
def world_blueprint(moderated):
    blueprint = Blueprint()
    alice = blueprint.add_user("Alice")
    blueprint.add_user("Bob")
    blueprint.add_supergroup("Team", members={alice: ChatMemberStatus.MEMBER})
    blueprint.add_group("Club", members={alice: ChatMemberStatus.MEMBER})
    # The bot moderates both chats; that is what this module tests.
    return moderated(blueprint)


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
def club(env, world_blueprint):
    return env.chat(world_blueprint.chats[1])


async def read(env, chat, user):
    return await env.bot.get_chat_member(chat_id=chat.id, user_id=user.id)


async def restrict(env, chat, user, permissions=None, **kwargs):
    await env.bot.restrict_chat_member(
        chat_id=chat.id,
        user_id=user.id,
        permissions=permissions or ChatPermissions(can_send_messages=False),
        **kwargs,
    )


class TestPresenceOfRestrictedUsers:
    async def test_a_present_member_stays_present(self, env, team, alice):
        await restrict(env, team, alice)

        member = await read(env, team, alice)
        assert member.status == ChatMemberStatus.RESTRICTED
        assert member.is_member is True
        assert await env.bot.get_chat_member_count(chat_id=team.id) == 2

    async def test_an_absent_user_stays_absent(self, env, team, bob):
        await restrict(env, team, bob)

        member = await read(env, team, bob)
        assert member.status == ChatMemberStatus.RESTRICTED
        assert member.is_member is False
        assert await env.bot.get_chat_member_count(chat_id=team.id) == 2

    async def test_a_second_restriction_keeps_presence(self, env, team, bob):
        await restrict(env, team, bob)
        await restrict(env, team, bob, ChatPermissions(can_send_polls=False))

        assert (await read(env, team, bob)).is_member is False

    async def test_leaving_and_rejoining_keep_the_restriction(self, env, team, alice):
        updates = []
        env.dispatcher.chat_member.register(updates.append)
        await restrict(env, team, alice, ChatPermissions(can_send_messages=True))
        actor = env.user(alice).in_(team)

        await actor.leave()
        await actor.join()

        left, joined = updates
        assert left.old_chat_member.status == ChatMemberStatus.RESTRICTED
        assert left.old_chat_member.is_member is True
        assert left.new_chat_member.status == ChatMemberStatus.RESTRICTED
        assert left.new_chat_member.is_member is False
        assert left.new_chat_member.can_send_messages is True
        assert joined.new_chat_member.status == ChatMemberStatus.RESTRICTED
        assert joined.new_chat_member.is_member is True
        assert joined.new_chat_member.can_send_messages is True

    async def test_the_bot_leaving_keeps_its_restriction(self, env, team, alice):
        await restrict(env, team, env.world.bot_user)

        await env.bot.leave_chat(chat_id=team.id)

        member = await read(env, team, env.world.bot_user)
        assert member.status == ChatMemberStatus.RESTRICTED
        assert member.is_member is False

    async def test_an_approved_join_request_keeps_the_restriction(self, env, team, bob):
        await restrict(env, team, bob, ChatPermissions(can_send_messages=True))
        await env.user(bob).in_(team).request_join()

        await env.bot.approve_chat_join_request(chat_id=team.id, user_id=bob.id)

        member = await read(env, team, bob)
        assert member.status == ChatMemberStatus.RESTRICTED
        assert member.is_member is True
        assert member.can_send_messages is True


class TestSupergroupsOnly:
    async def test_a_basic_group_member_cannot_be_restricted(self, env, club, alice):
        with pytest.raises(TelegramBadRequest):
            await restrict(env, club, alice)

        assert club.member(alice.id).status == ChatMemberStatus.MEMBER


class TestLiftingARestriction:
    async def test_lifting_a_present_member(self, env, team, alice):
        await restrict(env, team, alice, until_date=LATER)
        await restrict(env, team, alice, EVERYTHING)

        member = await read(env, team, alice)
        assert member.status == ChatMemberStatus.MEMBER
        assert member.until_date is None
        assert team.member(alice.id).permissions is None

    async def test_lifting_an_absent_user(self, env, team, bob):
        await restrict(env, team, bob)
        await restrict(env, team, bob, EVERYTHING)

        assert (await read(env, team, bob)).status == ChatMemberStatus.LEFT

    async def test_granting_everything_to_an_unrestricted_member_changes_nothing(
        self,
        env,
        team,
        alice,
    ):
        await restrict(env, team, alice, EVERYTHING)

        assert (await read(env, team, alice)).status == ChatMemberStatus.MEMBER

    async def test_demoting_a_restricted_user_keeps_the_restriction(self, env, team, bob):
        await restrict(env, team, bob)

        await env.bot.promote_chat_member(chat_id=team.id, user_id=bob.id)

        member = await read(env, team, bob)
        assert member.status == ChatMemberStatus.RESTRICTED
        assert member.is_member is False


class TestEndDates:
    async def test_a_permanent_ban_reads_as_the_epoch(self, env, team, alice):
        await env.bot.ban_chat_member(chat_id=team.id, user_id=alice.id)

        assert (await read(env, team, alice)).until_date == UNTIL_FOREVER

    async def test_a_permanent_restriction_reads_as_the_epoch(self, env, team, alice):
        await restrict(env, team, alice)

        assert (await read(env, team, alice)).until_date == UNTIL_FOREVER

    async def test_unbanning_clears_the_end_date(self, env, team, alice):
        await env.bot.ban_chat_member(chat_id=team.id, user_id=alice.id, until_date=LATER)
        await env.bot.unban_chat_member(chat_id=team.id, user_id=alice.id)
        await env.user(alice).in_(team).join()

        member = await read(env, team, alice)
        assert member.status == ChatMemberStatus.MEMBER
        assert member.until_date is None

    async def test_a_basic_group_ban_has_no_end(self, env, club, alice):
        await env.bot.ban_chat_member(chat_id=club.id, user_id=alice.id, until_date=LATER)

        assert (await read(env, club, alice)).until_date == UNTIL_FOREVER

    async def test_a_basic_group_ban_drops_an_earlier_restrictions_end(self, env, club, alice):
        # restrictChatMember is for supergroups, so the end date is set by hand.
        member = club.member(alice.id)
        member.set_status(ChatMemberStatus.RESTRICTED)
        member.until_date = env.now + datetime.timedelta(hours=1)
        await env.bot.ban_chat_member(chat_id=club.id, user_id=alice.id)
        await env.advance_time(datetime.timedelta(hours=2))

        member = await read(env, club, alice)
        assert member.status == ChatMemberStatus.KICKED
        assert member.until_date == UNTIL_FOREVER

    async def test_a_promotion_clears_the_end_date(self, env, team, alice):
        await restrict(env, team, alice, until_date=LATER)
        await env.bot.promote_chat_member(chat_id=team.id, user_id=alice.id, can_pin_messages=True)

        assert team.member(alice.id).until_date is None

    async def test_joining_again_keeps_a_subscriptions_expiry(self, env, team, alice):
        team.member(alice.id).until_date = LATER
        await env.user(alice).in_(team).join(service_message=False)

        member = await read(env, team, alice)
        assert member.status == ChatMemberStatus.MEMBER
        assert member.until_date == LATER


class TestBannedUsersStayOut:
    @pytest.mark.parametrize("action", ["join", "leave", "request_join"])
    async def test_a_banned_user_cannot_lift_their_own_ban(self, env, team, alice, action):
        await env.bot.ban_chat_member(chat_id=team.id, user_id=alice.id)

        with pytest.raises(WorldLookupError, match="is banned"):
            await getattr(env.user(alice).in_(team), action)()

        assert team.member(alice.id).status == ChatMemberStatus.KICKED
        assert alice.id not in team.join_requests

    async def test_a_ban_drops_a_pending_join_request(self, env, team, bob):
        await env.user(bob).in_(team).request_join()

        await env.bot.ban_chat_member(chat_id=team.id, user_id=bob.id)

        assert bob.id not in team.join_requests
        with pytest.raises(TelegramBadRequest):
            await env.bot.approve_chat_join_request(chat_id=team.id, user_id=bob.id)
        assert team.member(bob.id).status == ChatMemberStatus.KICKED

    async def test_a_ban_that_ended_lets_the_user_join(self, env, team, alice):
        await env.bot.ban_chat_member(
            chat_id=team.id,
            user_id=alice.id,
            until_date=datetime.timedelta(minutes=5),
        )
        await env.advance_time(datetime.timedelta(minutes=6))

        await env.user(alice).in_(team).join(service_message=False)

        assert team.member(alice.id).status == ChatMemberStatus.MEMBER


class TestDemotingOnlyAdministrators:
    async def test_the_demote_trigger_refuses_a_restricted_member(self, env, team, alice):
        await restrict(env, team, alice)

        with pytest.raises(WorldLookupError, match="nothing to demote"):
            await env.user(alice).in_(team).demote(subject=alice)

        assert team.member(alice.id).status == ChatMemberStatus.RESTRICTED

    async def test_the_demote_trigger_refuses_an_absent_user(self, env, team, alice, bob):
        with pytest.raises(WorldLookupError, match="nothing to demote"):
            await env.user(alice).in_(team).demote(subject=bob)

        assert team.member(bob.id).status == ChatMemberStatus.LEFT


class TestJoiningKeepsStanding:
    async def test_joining_does_not_demote_an_administrator(self, env, team, alice):
        await env.bot.promote_chat_member(chat_id=team.id, user_id=alice.id, can_pin_messages=True)

        await env.user(alice).in_(team).join()

        member = await read(env, team, alice)
        assert member.status == ChatMemberStatus.ADMINISTRATOR
        assert member.can_pin_messages is True


class TestUnbanning:
    async def test_unbanning_removes_a_present_member_by_default(self, env, team, alice):
        await env.bot.unban_chat_member(chat_id=team.id, user_id=alice.id)

        assert (await read(env, team, alice)).status == ChatMemberStatus.LEFT

    async def test_only_if_banned_leaves_a_member_alone(self, env, team, alice):
        await env.bot.unban_chat_member(chat_id=team.id, user_id=alice.id, only_if_banned=True)

        assert (await read(env, team, alice)).status == ChatMemberStatus.MEMBER

    async def test_the_owner_cannot_be_unbanned_out(self, env, world_blueprint):
        owner = world_blueprint.add_user("Owner")
        world_blueprint.add_supergroup("Owned", members={owner: ChatMemberStatus.CREATOR})
        owned_env = BotTestEnvironment(blueprint=world_blueprint)
        try:
            owned = owned_env.chat(world_blueprint.chats[-1])

            with pytest.raises(TelegramBadRequest):
                await owned_env.bot.unban_chat_member(chat_id=owned.id, user_id=owner.id)
            assert await owned_env.bot.unban_chat_member(
                chat_id=owned.id,
                user_id=owner.id,
                only_if_banned=True,
            )
            assert owned.member(owner.id).status == ChatMemberStatus.CREATOR
        finally:
            await owned_env.dispose()

    async def test_only_if_banned_still_unbans(self, env, team, alice):
        await env.bot.ban_chat_member(chat_id=team.id, user_id=alice.id)
        await env.bot.unban_chat_member(chat_id=team.id, user_id=alice.id, only_if_banned=True)

        assert (await read(env, team, alice)).status == ChatMemberStatus.LEFT
