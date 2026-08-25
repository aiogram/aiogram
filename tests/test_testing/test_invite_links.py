import datetime

import pytest

from aiogram import Dispatcher
from aiogram.exceptions import TelegramBadRequest
from aiogram.test import Blueprint, BotTestEnvironment, WorldLookupError
from aiogram.test.modeling import SUBSCRIPTION_PERIOD


def active_primaries(chat):
    return [link for link in chat.invite_links if link.is_primary and not link.is_revoked]


class TestCreatingLinks:
    async def test_a_created_link_is_stored(self, env, team):
        link = await env.bot.create_chat_invite_link(chat_id=team.id, name="Recruiting")

        assert link.name == "Recruiting"
        assert team.invite_link(link.invite_link).name == "Recruiting"

    async def test_links_are_unique(self, env, team):
        first = await env.bot.create_chat_invite_link(chat_id=team.id)
        second = await env.bot.create_chat_invite_link(chat_id=team.id)

        assert first.invite_link != second.invite_link

    async def test_a_created_link_is_not_primary(self, env, team):
        link = await env.bot.create_chat_invite_link(chat_id=team.id)

        assert link.is_primary is False
        assert link.is_revoked is False

    async def test_limits_and_flags_round_trip(self, env, team):
        expires = datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc)

        link = await env.bot.create_chat_invite_link(
            chat_id=team.id,
            member_limit=5,
            creates_join_request=False,
            expire_date=expires,
        )

        assert link.member_limit == 5
        assert link.expire_date == expires

    async def test_creating_in_an_unknown_chat_fails(self, env):
        with pytest.raises(WorldLookupError, match="not declared in the blueprint"):
            await env.bot.create_chat_invite_link(chat_id=-99)


class TestSubscriptionLinks:
    async def test_a_subscription_link_keeps_its_terms(self, env, team):
        link = await env.bot.create_chat_subscription_invite_link(
            chat_id=team.id,
            subscription_period=SUBSCRIPTION_PERIOD,
            subscription_price=10,
            name="Members",
        )

        assert link.subscription_period == SUBSCRIPTION_PERIOD
        assert link.subscription_price == 10

    async def test_a_timedelta_period_is_accepted(self, env, team):
        """aiogram lets a timedelta stand in for the seconds the Bot API wants."""
        link = await env.bot.create_chat_subscription_invite_link(
            chat_id=team.id,
            subscription_period=datetime.timedelta(days=30),
            subscription_price=10,
        )

        assert link.subscription_period == SUBSCRIPTION_PERIOD

    async def test_an_unsupported_period_fails(self, env, team):
        with pytest.raises(TelegramBadRequest, match="subscription period must be"):
            await env.bot.create_chat_subscription_invite_link(
                chat_id=team.id,
                subscription_period=60,
                subscription_price=10,
            )

    async def test_a_datetime_is_not_a_period(self, env, team):
        """A period is a duration; passing an expiry date instead is a real mistake."""
        with pytest.raises(TelegramBadRequest, match="subscription period must be"):
            await env.bot.create_chat_subscription_invite_link(
                chat_id=team.id,
                subscription_period=datetime.datetime(2026, 6, 1, tzinfo=datetime.timezone.utc),
                subscription_price=10,
            )

    async def test_editing_a_subscription_link_keeps_its_terms(self, env, team):
        link = await env.bot.create_chat_subscription_invite_link(
            chat_id=team.id,
            subscription_period=SUBSCRIPTION_PERIOD,
            subscription_price=10,
            name="Members",
        )

        edited = await env.bot.edit_chat_subscription_invite_link(
            chat_id=team.id,
            invite_link=link.invite_link,
            name="Supporters",
        )

        assert edited.name == "Supporters"
        assert edited.subscription_period == SUBSCRIPTION_PERIOD
        assert edited.subscription_price == 10

    async def test_editing_an_ordinary_link_as_a_subscription_fails(self, env, team):
        link = await env.bot.create_chat_invite_link(chat_id=team.id)

        with pytest.raises(TelegramBadRequest, match="not a subscription invite link"):
            await env.bot.edit_chat_subscription_invite_link(
                chat_id=team.id,
                invite_link=link.invite_link,
                name="Supporters",
            )


class TestEditingAndRevoking:
    async def test_create_then_revoke_returns_the_same_link(self, env, team):
        created = await env.bot.create_chat_invite_link(chat_id=team.id, name="Recruiting")

        revoked = await env.bot.revoke_chat_invite_link(
            chat_id=team.id,
            invite_link=created.invite_link,
        )

        assert revoked.invite_link == created.invite_link
        assert revoked.name == "Recruiting"
        assert revoked.is_revoked is True

    async def test_editing_mutates_the_stored_link(self, env, team):
        created = await env.bot.create_chat_invite_link(chat_id=team.id, name="Old")

        edited = await env.bot.edit_chat_invite_link(
            chat_id=team.id,
            invite_link=created.invite_link,
            name="New",
            member_limit=3,
        )

        assert edited.invite_link == created.invite_link
        assert edited.name == "New"
        stored = team.invite_link(created.invite_link)
        assert (stored.name, stored.member_limit) == ("New", 3)

    @pytest.mark.parametrize(
        ("method_name", "kwargs"),
        [
            ("edit_chat_invite_link", {"name": "New"}),
            ("edit_chat_subscription_invite_link", {"name": "New"}),
            ("revoke_chat_invite_link", {}),
        ],
    )
    async def test_acting_on_an_unknown_link_fails(self, env, team, method_name, kwargs):
        with pytest.raises(TelegramBadRequest, match="does not exist in chat"):
            await getattr(env.bot, method_name)(
                chat_id=team.id,
                invite_link="https://t.me/+nope",
                **kwargs,
            )


class TestPrimaryLink:
    async def test_exporting_replaces_the_primary_link(self, env, team):
        first = await env.bot.export_chat_invite_link(chat_id=team.id)
        second = await env.bot.export_chat_invite_link(chat_id=team.id)

        assert first != second
        assert team.invite_link(first).is_revoked is True
        assert team.primary_invite_link.invite_link == second

    async def test_get_chat_reports_the_primary_link(self, env, team):
        exported = await env.bot.export_chat_invite_link(chat_id=team.id)

        assert (await env.bot.get_chat(chat_id=team.id)).invite_link == exported

    async def test_a_chat_with_no_primary_link_reports_none(self, env, team):
        await env.bot.create_chat_invite_link(chat_id=team.id)

        assert (await env.bot.get_chat(chat_id=team.id)).invite_link is None

    async def test_revoking_the_primary_link_generates_a_replacement(self, env, team):
        exported = await env.bot.export_chat_invite_link(chat_id=team.id)

        revoked = await env.bot.revoke_chat_invite_link(
            chat_id=team.id,
            invite_link=exported,
        )

        assert revoked.is_revoked is True
        replacement = team.primary_invite_link
        assert replacement is not None
        assert replacement.invite_link != exported

    async def test_revoking_a_secondary_link_does_not_touch_the_primary(self, env, team):
        exported = await env.bot.export_chat_invite_link(chat_id=team.id)
        secondary = await env.bot.create_chat_invite_link(chat_id=team.id)

        await env.bot.revoke_chat_invite_link(chat_id=team.id, invite_link=secondary.invite_link)

        assert team.primary_invite_link.invite_link == exported

    @pytest.mark.parametrize("rounds", [1, 2, 3])
    async def test_exactly_one_active_primary_after_each_transition(self, env, team, rounds):
        for _ in range(rounds):
            await env.bot.export_chat_invite_link(chat_id=team.id)

        assert len(active_primaries(team)) == 1

    async def test_one_active_primary_after_revoking_it(self, env, team):
        exported = await env.bot.export_chat_invite_link(chat_id=team.id)

        await env.bot.revoke_chat_invite_link(chat_id=team.id, invite_link=exported)

        assert len(active_primaries(team)) == 1


class TestDeclaredLinks:
    @pytest.fixture
    def declared(self, dp):
        blueprint = Blueprint()
        chat = blueprint.add_supergroup("Team")
        link = blueprint.add_invite_link(chat, name="Declared", member_limit=2)
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            yield environment, environment.chat(chat), link
        finally:
            environment.dispose_sync()

    async def test_a_declared_link_is_editable_without_being_created(self, declared):
        env, chat, link = declared

        edited = await env.bot.edit_chat_invite_link(
            chat_id=chat.id,
            invite_link=link.invite_link,
            name="Renamed",
        )

        assert edited.name == "Renamed"

    async def test_a_declared_link_is_revocable(self, declared):
        env, chat, link = declared

        revoked = await env.bot.revoke_chat_invite_link(
            chat_id=chat.id,
            invite_link=link.invite_link,
        )

        assert revoked.is_revoked is True

    async def test_links_are_isolated_between_environments(self, dp):
        blueprint = Blueprint()
        chat = blueprint.add_supergroup("Team")
        link = blueprint.add_invite_link(chat, name="Declared")

        first = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        second = BotTestEnvironment(blueprint=blueprint, dispatcher=Dispatcher())
        try:
            await first.bot.revoke_chat_invite_link(
                chat_id=chat.id,
                invite_link=link.invite_link,
            )

            assert second.chat(chat).invite_link(link.invite_link).is_revoked is False
        finally:
            first.dispose_sync()
            second.dispose_sync()

    async def test_a_declared_primary_link_reaches_get_chat(self, dp):
        blueprint = Blueprint()
        chat = blueprint.add_supergroup("Team")
        link = blueprint.add_invite_link(chat, is_primary=True)
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            assert (await env.bot.get_chat(chat_id=chat.id)).invite_link == link.invite_link
        finally:
            env.dispose_sync()


class TestLinksAreMetadataOnly:
    async def test_a_member_limit_does_not_gate_joining(self, env, team, alice):
        """Links are metadata; membership is driven by actors."""
        await env.bot.create_chat_invite_link(chat_id=team.id, member_limit=0)

        await alice.in_(team).join()

        assert team.member(alice.user.id).is_present
