import pytest

from aiogram.enums import ChatMemberStatus, ChatType
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

    async def test_startapp_link_is_rejected(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/test_bot?startapp=abc")

        with pytest.raises(WorldLookupError, match="startapp"):
            await alice.in_(team).follow_deep_link("https://t.me/test_bot?startapp=abc")

    async def test_startchannel_link_is_rejected(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/test_bot?startchannel=abc")

        with pytest.raises(WorldLookupError, match="startchannel"):
            await alice.in_(team).follow_deep_link("https://t.me/test_bot?startchannel=abc")

    async def test_startattach_link_is_rejected(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/test_bot?startattach=abc")

        with pytest.raises(WorldLookupError, match="startattach"):
            await alice.in_(team).follow_deep_link("https://t.me/test_bot?startattach=abc")

    async def test_attach_link_is_rejected(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/test_bot?attach=abc")

        with pytest.raises(WorldLookupError, match="attach"):
            await alice.in_(team).follow_deep_link("https://t.me/test_bot?attach=abc")

    async def test_mini_app_button_is_not_silently_followed_as_plain_start(self, env, team, alice):
        """
        A Mini App button must never be replayed as a bare `/start` — a tapping user's
        client opens the Mini App, it never sends `/start` at all. The automatic scan
        (no explicit target) must surface this button and reject it rather than either
        skipping it or misreading it as a start deep link.
        """
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(message.text),
            CommandStart(deep_link=True),
        )
        await _post_deep_link(env, team, "https://t.me/test_bot?startapp=abc")

        with pytest.raises(WorldLookupError, match="startapp"):
            await alice.in_(team).follow_deep_link()

        assert seen == []

    async def test_scan_looks_past_an_unfollowable_button_to_find_the_start_link(
        self, env, team, alice
    ):
        """
        A keyboard mixing a `startapp` button with a real `start` button must not let the
        unfollowable one shadow the followable one — the automatic scan matches on
        followability, not merely on which button targets this bot first.
        """
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(command.args),
            CommandStart(deep_link=True),
        )
        await env.bot.send_message(
            chat_id=team.id,
            text="Choose one",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Mini App", url="https://t.me/test_bot?startapp=abc"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="Start", url="https://t.me/test_bot?start=team-1"
                        ),
                    ],
                ],
            ),
        )

        await alice.in_(team).follow_deep_link()

        assert seen == ["team-1"]

    async def test_scan_with_only_unfollowable_candidates_names_each_and_why(
        self, env, team, alice
    ):
        await env.bot.send_message(
            chat_id=team.id,
            text="Choose one",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Mini App", url="https://t.me/test_bot?startapp=abc"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="Group", url="https://t.me/test_bot?startgroup=abc"
                        ),
                    ],
                ],
            ),
        )

        with pytest.raises(WorldLookupError, match="startapp") as exc_info:
            await alice.in_(team).follow_deep_link()

        assert "startgroup" in str(exc_info.value)

    async def test_scan_skips_buttons_that_link_to_another_bot(self, env, team, alice):
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(command.args),
            CommandStart(deep_link=True),
        )
        await env.bot.send_message(
            chat_id=team.id,
            text="Pick",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="Other bot", url="https://t.me/other_bot?start=nope"
                        ),
                        InlineKeyboardButton(text="Ours", url="https://t.me/test_bot?start=ours"),
                    ],
                ],
            ),
        )

        await alice.in_(team).follow_deep_link()

        assert seen == ["ours"]

    async def test_explicit_message_with_only_unfollowable_candidates_names_it(
        self, env, team, alice
    ):
        await env.bot.send_message(
            chat_id=team.id,
            text="App only",
            reply_markup=_join_button("https://t.me/test_bot?startapp=abc", text="Mini App"),
        )

        with pytest.raises(WorldLookupError, match="startapp") as exc_info:
            await alice.in_(team).follow_deep_link(
                message=env.chat(team.id).messages[-1],
            )

        assert str(env.chat(team.id).messages[-1].message_id) in str(exc_info.value)

    async def test_message_link_is_rejected(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/test_bot/42")

        with pytest.raises(WorldLookupError, match="extra path segments"):
            await alice.in_(team).follow_deep_link("https://t.me/test_bot/42")

    async def test_extra_path_link_is_rejected(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/test_bot/shop")

        with pytest.raises(WorldLookupError, match="extra path segments"):
            await alice.in_(team).follow_deep_link("https://t.me/test_bot/shop")

    async def test_invite_hash_link_is_rejected(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/+AbCdEfGhIj")

        with pytest.raises(WorldLookupError, match="chat invite link"):
            await alice.in_(team).follow_deep_link("https://t.me/+AbCdEfGhIj")

    async def test_joinchat_link_is_rejected(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/joinchat/AbCdEfGhIj")

        with pytest.raises(WorldLookupError, match="chat invite link"):
            await alice.in_(team).follow_deep_link("https://t.me/joinchat/AbCdEfGhIj")

    async def test_message_scopes_the_search_to_that_message(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/test_bot?start=only-here", text="Invite")
        other = await env.bot.send_message(chat_id=team.id, text="No button here")

        with pytest.raises(WorldLookupError, match=f"Message {other.message_id}"):
            await alice.in_(team).follow_deep_link(message=other)

    async def test_no_matching_button_raises_a_scan_error(self, env, team, alice):
        with pytest.raises(WorldLookupError, match="deep-link button"):
            await alice.in_(team).follow_deep_link()

    async def test_an_undeclared_private_chat_is_opened_by_the_tap(self, dp):
        """Opening the private chat is exactly what tapping a start link does."""
        blueprint = Blueprint()
        bob = blueprint.add_user("Bob", username="bob")
        team = blueprint.add_supergroup("Team", members={bob: ChatMemberStatus.MEMBER})
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        seen = []
        environment.dispatcher.message.register(
            lambda message, command: seen.append((message.chat.id, command.args)),
            CommandStart(deep_link=True),
        )
        try:
            bob_actor = environment.user(bob).in_(team)
            await environment.bot.send_message(
                chat_id=team.id,
                text="Join us!",
                reply_markup=_join_button("https://t.me/test_bot?start=x"),
            )

            await bob_actor.follow_deep_link()

            private = environment.chat(bob.id)
            assert seen == [(bob.id, "x")]
            assert private.type == ChatType.PRIVATE
            assert private.username == "bob"
            assert private.messages[-1].text == "/start x"
            # Opened the way a declared chat is, so what it holds is usable as usual.
            assert private.messages[-1].bot is environment.bot
        finally:
            environment.dispose_sync()

    async def test_an_unbound_send_also_opens_the_actor_s_own_private_chat(self, dp):
        """
        A plain `send()` from an unbound actor names no chat, but it is still the same
        user tapping their own client open — so it opens the private chat exactly like
        `follow_deep_link` does, rather than the two triggers disagreeing on whether an
        undeclared private chat may be invented.
        """
        blueprint = Blueprint()
        bob = blueprint.add_user("Bob", username="bob")
        blueprint.add_supergroup("Team", members={bob: ChatMemberStatus.MEMBER})
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        seen = []
        environment.dispatcher.message.register(
            lambda message: seen.append(message.chat.id),
            Command("start"),
        )
        try:
            await environment.user(bob).send("/start")

            private = environment.chat(bob.id)
            assert seen == [bob.id]
            assert private.type == ChatType.PRIVATE
            assert private.username == "bob"
            assert private.messages[-1].text == "/start"
        finally:
            environment.dispose_sync()


class TestUrlsThatAreNotDeepLinks:
    """A button url that is not a bot deep link is rejected, saying what was expected."""

    @pytest.mark.parametrize(
        "url",
        [
            pytest.param("https://example.com/promo", id="another-host"),
            pytest.param("https://t.me/", id="no-username"),
            pytest.param("tg://join?invite=abc", id="tg-but-not-resolve"),
            pytest.param("tg://resolve?domain=", id="tg-resolve-without-domain"),
            pytest.param("ftp://t.me/test_bot", id="another-scheme"),
        ],
    )
    async def test_it_is_not_followable(self, env, team, alice, url):
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match="not a Telegram deep-link url"):
            await alice.in_(team).follow_deep_link(url)

    async def test_a_button_without_a_url_is_skipped_by_the_scan(self, env, team, alice):
        """The scan walks back from the newest message, past buttons that carry no url."""
        await _post_deep_link(env, team, "https://t.me/test_bot?start=found")
        await env.bot.send_message(
            chat_id=team.id,
            text="Menu",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
            ),
        )
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(command.args),
            CommandStart(deep_link=True),
        )

        await alice.in_(team).follow_deep_link()

        assert seen == ["found"]

    async def test_a_named_url_missing_from_a_named_message_says_which(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/test_bot?start=here")
        other = await env.bot.send_message(chat_id=team.id, text="No button here")

        with pytest.raises(WorldLookupError, match=f"Message {other.message_id} does not carry"):
            await alice.in_(team).follow_deep_link(
                "https://t.me/test_bot?start=here",
                message=other,
            )
