import pytest

from aiogram.enums import ChatMemberStatus
from aiogram.filters import Command, CommandStart
from aiogram.test import Blueprint, BotTestEnvironment, WorldLookupError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def _join_button(url: str, text: str = "Join") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, url=url)]])


async def _post_deep_link(env, team, url: str, text: str = "Join us!"):
    await env.bot.send_message(chat_id=team.id, text=text, reply_markup=_join_button(url))


class TestFollowDeepLink:
    async def test_happy_path_sends_start_with_payload_in_private_chat(self, env, team, alice):
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append((message.chat.id, command.args)),
            CommandStart(deep_link=True),
        )
        await _post_deep_link(env, team, "https://t.me/test_bot?start=team-42")

        await alice.in_(team).follow_deep_link()

        assert seen == [(alice.user.id, "team-42")]

    async def test_target_none_picks_the_newest_matching_button(self, env, team, alice):
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(command.args),
            CommandStart(deep_link=True),
        )
        await _post_deep_link(env, team, "https://t.me/test_bot?start=old", text="Old invite")
        await _post_deep_link(env, team, "https://t.me/test_bot?start=new", text="New invite")

        await alice.in_(team).follow_deep_link()

        assert seen == ["new"]

    async def test_target_url_not_found_raises(self, env, team, alice):
        with pytest.raises(WorldLookupError, match="carries a button with url"):
            await alice.in_(team).follow_deep_link("https://t.me/test_bot?start=nope")

    async def test_button_without_url_cannot_be_followed(self, env, team, alice):
        button = InlineKeyboardButton(text="Go", callback_data="go")

        with pytest.raises(WorldLookupError, match="carries no url"):
            await alice.in_(team).follow_deep_link(button)

    async def test_link_to_another_bot_is_not_followable(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/other_bot?start=team-42")

        with pytest.raises(WorldLookupError, match="other_bot"):
            await alice.in_(team).follow_deep_link("https://t.me/other_bot?start=team-42")

    async def test_startgroup_link_is_rejected(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/test_bot?startgroup=team-42")

        with pytest.raises(WorldLookupError, match="startgroup"):
            await alice.in_(team).follow_deep_link("https://t.me/test_bot?startgroup=team-42")

    async def test_tg_resolve_form_works(self, env, team, alice):
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(command.args),
            CommandStart(deep_link=True),
        )
        await _post_deep_link(env, team, "tg://resolve?domain=test_bot&start=team-42")

        await alice.in_(team).follow_deep_link()

        assert seen == ["team-42"]

    async def test_empty_payload_sends_plain_start(self, env, team, alice):
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(message.text),
            Command("start"),
        )
        await _post_deep_link(env, team, "https://t.me/test_bot")

        await alice.in_(team).follow_deep_link()

        assert seen == ["/start"]

    async def test_message_scopes_the_search_to_that_message(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/test_bot?start=only-here", text="Invite")
        other = await env.bot.send_message(chat_id=team.id, text="No button here")

        with pytest.raises(WorldLookupError, match=f"Message {other.message_id}"):
            await alice.in_(team).follow_deep_link(message=other)

    async def test_no_matching_button_raises_a_scan_error(self, env, team, alice):
        with pytest.raises(WorldLookupError, match="deep-link button"):
            await alice.in_(team).follow_deep_link()

    async def test_no_private_chat_raises_a_helpful_error(self, dp):
        """Following a deep link needs a private chat to land the `/start` in."""
        blueprint = Blueprint()
        bob = blueprint.add_user("Bob")
        team = blueprint.add_supergroup("Team", members={bob: ChatMemberStatus.MEMBER})
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            bob_actor = environment.user(bob).in_(team)
            await environment.bot.send_message(
                chat_id=team.id,
                text="Join us!",
                reply_markup=_join_button("https://t.me/test_bot?start=x"),
            )

            with pytest.raises(WorldLookupError, match="no private chat"):
                await bob_actor.follow_deep_link()
        finally:
            environment.dispose_sync()
