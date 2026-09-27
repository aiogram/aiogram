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

    async def test_tg_resolve_without_start_is_a_plain_start_like_the_bare_link(
        self, env, team, alice
    ):
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(message.text),
            Command("start"),
        )
        await _post_deep_link(env, team, "tg://resolve?domain=test_bot")

        await alice.in_(team).follow_deep_link()

        assert seen == ["/start"]

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

    async def test_start_with_extra_harmless_params_is_still_followable(self, env, team, alice):
        """
        A real Telegram client reads only the `start` parameter and ignores the rest of
        the query, so an explicit `start` alongside tracking params such as `utm_source`
        must stay a plain followable start, not fall into `unknown_query`.
        """
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(command.args),
            CommandStart(deep_link=True),
        )
        await _post_deep_link(
            env, team, "https://t.me/test_bot?utm_source=newsletter&start=team-9"
        )

        await alice.in_(team).follow_deep_link()

        assert seen == ["team-9"]

    @pytest.mark.parametrize(
        "url",
        [
            "https://t.me/test_bot?start=team-9&startapp=abc",
            "https://t.me/test_bot?startapp=abc&start=team-9",
            "https://t.me/test_bot?startgroup=g&start=team-9&startchannel=c",
            "tg://resolve?domain=test_bot&startapp=abc&start=team-9",
        ],
    )
    async def test_an_explicit_start_wins_over_a_start_ish_param(self, env, team, alice, url):
        """
        Regression: classification iterated the policy table, where `start` comes last.

        So `?start=x&startapp=y` was read as the `startapp` the table happens to list
        earlier and refused — a link a real client opens the bot with, and one Telegram
        itself hands out, since a Mini App button carries both for clients that cannot open
        the app. The docstring already promised that `start` wins whenever it is present;
        the code now agrees, in either query order.
        """
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(command.args),
            CommandStart(deep_link=True),
        )
        await _post_deep_link(env, team, url)

        await alice.in_(team).follow_deep_link()

        assert seen == ["team-9"]

    async def test_a_start_ish_param_alone_is_still_refused(self, env, team, alice):
        """The precedence only applies when a real `start` is there to take it."""
        await _post_deep_link(env, team, "https://t.me/test_bot?startapp=abc")

        with pytest.raises(WorldLookupError, match="startapp"):
            await alice.in_(team).follow_deep_link()

    async def test_startgroup_without_start_still_classifies_as_startgroup(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/test_bot?startgroup=true")

        with pytest.raises(WorldLookupError, match="startgroup"):
            await alice.in_(team).follow_deep_link()

    async def test_unrecognized_query_param_link_is_rejected(self, env, team, alice):
        """
        A query Telegram does not define is not a `start` link and must not be silently
        replayed as a bare `/start` — the toolkit does not know what a real Telegram
        client would do with it, so it refuses to guess and quotes the query back.
        """
        url = "https://t.me/test_bot?utm_source=newsletter"
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match="utm_source=newsletter"):
            await alice.in_(team).follow_deep_link(url)

    async def test_unrecognized_query_params_with_start_still_reject_only_start_is_missing(
        self, env, team, alice
    ):
        """A junk param alongside `start` still resolves as `start` — see above — but a
        junk param on its own, with no `start` in sight, is rejected."""
        url = "https://t.me/test_bot?utm_source=x&fbclid=abc"
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match="utm_source=x&fbclid=abc"):
            await alice.in_(team).follow_deep_link(url)

    async def test_unrecognized_query_param_button_is_not_silently_followed_as_plain_start(
        self, env, team, alice
    ):
        """
        The automatic scan (no explicit target) must surface an unrecognized-query
        button and reject it rather than misreading it as a bare start link — mirrors
        `test_mini_app_button_is_not_silently_followed_as_plain_start` for `startapp`.
        """
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(message.text),
            CommandStart(deep_link=True),
        )
        await _post_deep_link(env, team, "https://t.me/test_bot?utm_source=x")

        with pytest.raises(WorldLookupError, match="utm_source=x"):
            await alice.in_(team).follow_deep_link()

        assert seen == []

    async def test_scan_skips_a_button_with_unrecognized_query_params(self, env, team, alice):
        """A keyboard mixing an unrecognized-query button with a real `start` button must
        still find the `start` link — the unfollowable one never shadows it."""
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
                            text="Promo", url="https://t.me/test_bot?utm_source=x"
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
        url = "https://t.me/somechat?attach=test_bot"
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match="is a `attach` link"):
            await alice.in_(team).follow_deep_link(url)

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

        with pytest.raises(WorldLookupError, match="a message link"):
            await alice.in_(team).follow_deep_link("https://t.me/test_bot/42")

    async def test_unrecognized_path_shape_is_rejected(self, env, team, alice):
        """The bucket left for paths matching none of Telegram's documented formats."""
        await _post_deep_link(env, team, "https://t.me/test_bot/shop/cart")

        with pytest.raises(WorldLookupError, match="extra path segments"):
            await alice.in_(team).follow_deep_link("https://t.me/test_bot/shop/cart")

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
            pytest.param("tg://resolve?domain=", id="tg-resolve-without-domain"),
            pytest.param("tg://resolve?phone=", id="tg-resolve-without-phone"),
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

    async def test_a_button_to_another_site_is_skipped_by_the_scan(self, env, team, alice):
        """A plain web button is not a deep link of anyone's, so it is neither followed
        nor listed as an unfollowable candidate of this bot's."""
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
                    [InlineKeyboardButton(text="Docs", url="https://example.com/promo")],
                    [InlineKeyboardButton(text="Start", url="https://t.me/test_bot?start=here")],
                ],
            ),
        )

        await alice.in_(team).follow_deep_link()

        assert seen == ["here"]

    async def test_a_named_url_missing_from_a_named_message_says_which(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/test_bot?start=here")
        other = await env.bot.send_message(chat_id=team.id, text="No button here")

        with pytest.raises(WorldLookupError, match=f"Message {other.message_id} does not carry"):
            await alice.in_(team).follow_deep_link(
                "https://t.me/test_bot?start=here",
                message=other,
            )


class TestLinkFormatsFromTheSpec:
    """
    Every documented link format is refused as the format it actually is.

    The classification and the wording follow https://core.telegram.org/api/links: what a
    real Telegram client does with the url is the whole content of the refusal, so a test
    that put the wrong kind of link on a button is told which kind it put there — not
    that it is "a link with extra path segments" or "a query Telegram does not define".
    """

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            pytest.param(
                "https://t.me/test_bot/shop",
                "opens one of the bot's Mini Apps directly",
                id="direct-mini-app",
            ),
            pytest.param(
                "tg://resolve?domain=test_bot&appname=shop&startapp=ref",
                "opens one of the bot's Mini Apps directly",
                id="direct-mini-app-tg",
            ),
            pytest.param("https://t.me/test_bot/42", "a message link", id="message"),
            pytest.param("https://t.me/test_bot/9/42", "a message link", id="message-in-topic"),
            pytest.param("https://t.me/c/1234567/42", "a message link", id="message-private"),
            pytest.param(
                "tg://privatepost?channel=1234567&post=42",
                "a message link",
                id="message-private-tg",
            ),
            pytest.param("https://t.me/durov/s/5", "a story link", id="story"),
            pytest.param("https://t.me/share?url=https%3A%2F%2Fexample.com", "a share link"),
            pytest.param("https://t.me/share/url?url=x&text=hi", "a share link", id="share-url"),
            pytest.param("https://t.me/msg/url?url=x", "a share link", id="share-msg"),
            pytest.param("tg://msg_url?url=x&text=hi", "a share link", id="share-tg"),
            pytest.param("https://t.me/$AbCdEfGhIj", "an invoice link", id="invoice-dollar"),
            pytest.param("https://t.me/invoice/AbCdEfGhIj", "an invoice link", id="invoice-path"),
            pytest.param("tg://invoice?slug=AbCdEfGhIj", "an invoice link", id="invoice-tg"),
            pytest.param("https://t.me/boost/durov", "a boost link", id="boost-path"),
            pytest.param("https://t.me/test_bot?boost", "a boost link", id="boost-query"),
            pytest.param("https://t.me/boost?c=1234567", "a boost link", id="boost-private"),
            pytest.param("tg://boost?domain=durov", "a boost link", id="boost-tg"),
            pytest.param("https://t.me/durov?videochat", "a video-chat link", id="videochat"),
            pytest.param("https://t.me/durov?livestream", "a video-chat link", id="livestream"),
            pytest.param(
                "https://t.me/durov?voicechat=hash",
                "a video-chat link",
                id="voicechat-legacy",
            ),
            pytest.param("https://t.me/m/AbCdEfGhIj", "a business chat link", id="business"),
            pytest.param("tg://message?slug=AbCdEfGhIj", "a business chat link", id="business-tg"),
            pytest.param(
                "https://t.me/addstickers/AnimatedEmojies",
                "a sticker- or emoji-set link",
                id="stickers",
            ),
            pytest.param(
                "https://t.me/addemoji/CustomPack",
                "a sticker- or emoji-set link",
                id="emoji-set",
            ),
            pytest.param(
                "tg://addstickers?set=AnimatedEmojies",
                "a sticker- or emoji-set link",
                id="stickers-tg",
            ),
            pytest.param(
                "https://t.me/test_bot?game=chess",
                "share the bot's `chess` game",
                id="game",
            ),
            pytest.param(
                "https://t.me/test_bot?text=hi%20there",
                "waiting as an unsent draft",
                id="prefilled-draft",
            ),
            pytest.param(
                "https://t.me/test_bot?ref=affiliate-7",
                "crediting `affiliate-7`",
                id="affiliate",
            ),
            pytest.param(
                "https://t.me/test_bot?profile",
                "opens the profile page rather than the chat view",
                id="profile",
            ),
            pytest.param(
                "https://t.me/proxy?server=1.2.3.4&port=443&secret=ee",
                "a Telegram service link",
                id="proxy",
            ),
            pytest.param(
                "https://t.me/setlanguage/klingon",
                "a Telegram service link",
                id="language-pack",
            ),
            pytest.param("https://t.me/login/12345", "a Telegram service link", id="login-code"),
            pytest.param(
                "https://t.me/addlist/AbCdEfGhIj",
                "a Telegram service link",
                id="chat-folder",
            ),
        ],
    )
    async def test_it_is_refused_as_what_it_is(self, env, team, alice, url, expected):
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match=expected):
            await alice.in_(team).follow_deep_link(url)

    async def test_a_draft_link_names_the_text_and_points_at_send(self, env, team, alice):
        """
        `?text=` fills a draft the user still has to send, so the bot receives nothing —
        the one thing a test must not conclude is that the text was delivered.
        """
        url = "https://t.me/test_bot?text=hi%20there"
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError) as exc_info:
            await alice.in_(team).follow_deep_link(url)

        message = str(exc_info.value)
        assert "'hi there'" in message
        assert "send('hi there')" in message

    async def test_an_invoice_link_points_at_the_payment_triggers(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/$AbCdEfGhIj")

        with pytest.raises(WorldLookupError, match="use `pay..` to complete a payment"):
            await alice.in_(team).follow_deep_link("https://t.me/$AbCdEfGhIj")

    async def test_a_boost_link_points_at_the_boost_trigger(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/boost/durov")

        with pytest.raises(WorldLookupError, match="use `boost..` to deliver"):
            await alice.in_(team).follow_deep_link("https://t.me/boost/durov")

    async def test_a_direct_mini_app_button_is_surfaced_by_the_scan_as_this_bot_s(
        self, env, team, alice
    ):
        """
        `t.me/<bot>/<short_name>` is the one path form that does name a bot, so the scan
        reports it as an unfollowable button of this bot's rather than ignoring it the
        way it ignores links addressed to a chat.
        """
        await _post_deep_link(env, team, "https://t.me/test_bot/shop")

        with pytest.raises(WorldLookupError, match="only unfollowable ones") as exc_info:
            await alice.in_(team).follow_deep_link()

        assert "Mini Apps" in str(exc_info.value)

    async def test_the_scan_ignores_links_that_address_a_chat_rather_than_the_bot(
        self, env, team, alice
    ):
        """
        A boost or video-chat button names a channel and can never name this bot, so the
        scan does not list it as an unfollowable candidate "to @test_bot" — it reports
        the plain absence of a deep-link button instead.
        """
        await _post_deep_link(env, team, "https://t.me/durov?videochat")

        with pytest.raises(WorldLookupError, match="carries a deep-link button") as exc_info:
            await alice.in_(team).follow_deep_link()

        assert "unfollowable" not in str(exc_info.value)


class TestPhoneLinksAreNotInviteLinks:
    """
    `t.me/+<digits>` addresses a phone number, `t.me/+<hash>` a private chat.

    Telegram's own clients tell the two apart by the all-digit tail, and calling a phone
    link an invite link would send a test looking for a chat that was never in the link.
    """

    @pytest.mark.parametrize(
        "url",
        [
            pytest.param("https://t.me/+15551234567", id="t-me"),
            pytest.param("tg://resolve?phone=15551234567", id="tg-resolve"),
        ],
    )
    async def test_a_phone_link_is_refused_as_a_phone_link(self, env, team, alice, url):
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match="a phone-number link") as exc_info:
            await alice.in_(team).follow_deep_link(url)

        assert "invite" not in str(exc_info.value)

    async def test_an_invite_hash_is_still_an_invite_link(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/+AbCdEfGhIj")

        with pytest.raises(WorldLookupError, match="a chat invite link") as exc_info:
            await alice.in_(team).follow_deep_link("https://t.me/+AbCdEfGhIj")

        assert "phone" not in str(exc_info.value)


class TestTgSchemeVariants:
    """
    A `tg://` url other than `tg://resolve` is still a Telegram link.

    Refusing it as "not a Telegram deep-link url" was a lie about the url; each known
    host is classified like its `t.me` twin, and the rest are honestly described as app
    screens rather than as something the toolkit failed to recognize.
    """

    async def test_tg_join_is_an_invite_link_like_its_t_me_twin(self, env, team, alice):
        await _post_deep_link(env, team, "tg://join?invite=AbCdEfGhIj")

        with pytest.raises(WorldLookupError, match="a chat invite link"):
            await alice.in_(team).follow_deep_link("tg://join?invite=AbCdEfGhIj")

    async def test_tg_user_is_named_as_the_bot_api_abstraction_it_is(self, env, team, alice):
        await _post_deep_link(env, team, "tg://user?id=42")

        with pytest.raises(WorldLookupError, match="entity reference"):
            await alice.in_(team).follow_deep_link("tg://user?id=42")

    @pytest.mark.parametrize(
        "url",
        [
            pytest.param("tg://settings/privacy", id="settings"),
            pytest.param("tg://proxy?server=1.2.3.4&port=443&secret=ee", id="proxy"),
            pytest.param("tg://stars", id="a-host-the-toolkit-does-not-enumerate"),
        ],
    )
    async def test_an_app_screen_is_refused_as_a_service_link(self, env, team, alice, url):
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match="a Telegram service link"):
            await alice.in_(team).follow_deep_link(url)


class TestStartPayloadValidation:
    """
    A `start` payload Telegram would not deliver is refused, naming the rule.

    Bot API deep linking allows 1-64 characters of `A-Z`, `a-z`, `0-9`, `_` and `-`, so a
    real client tapping a button with anything else never sends `/start` at all. Feeding
    the handler such a payload would let a test pass on a button the bot built wrong.
    """

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param("a" * 64, id="64-characters"),
            pytest.param("a-b_c", id="dash-and-underscore"),
            pytest.param("MjAyNS0wMS0wMQ", id="base64url"),
        ],
    )
    async def test_a_valid_payload_is_followed(self, env, team, alice, payload):
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(command.args),
            CommandStart(deep_link=True),
        )
        await _post_deep_link(env, team, f"https://t.me/test_bot?start={payload}")

        await alice.in_(team).follow_deep_link()

        assert seen == [payload]

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            pytest.param(
                f"https://t.me/test_bot?start={'a' * 65}",
                "1-64 characters",
                id="65-characters",
            ),
            pytest.param(
                "https://t.me/test_bot?start=team%2042",
                "'team 42'",
                id="percent-encoded-space",
            ),
            pytest.param(
                "https://t.me/test_bot?start=привет",
                "'привет'",
                id="non-latin",
            ),
            pytest.param(
                "tg://resolve?domain=test_bot&start=a+b",
                "'a b'",
                id="tg-resolve-form",
            ),
        ],
    )
    async def test_an_invalid_payload_is_refused(self, env, team, alice, url, expected):
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(command.args),
            CommandStart(deep_link=True),
        )
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match=expected):
            await alice.in_(team).follow_deep_link(url)

        assert seen == []

    async def test_the_scan_refuses_it_too_rather_than_looking_past_it(self, env, team, alice):
        """The link is a `start` link — it is simply broken, and saying so is the point."""
        await _post_deep_link(env, team, "https://t.me/test_bot?start=team%2042")

        with pytest.raises(WorldLookupError, match="Telegram would not deliver"):
            await alice.in_(team).follow_deep_link()


class TestStartGroupAdminCompanion:
    """
    `admin=` only preselects the rights the chooser asks for; the kind does not change.

    Telegram documents it as a companion of `startgroup` / `startchannel`, so a link
    carrying it is still a chooser link and must be refused as one.
    """

    @pytest.mark.parametrize(
        ("url", "kind"),
        [
            pytest.param(
                "https://t.me/test_bot?startgroup=team&admin=delete_messages+ban_users",
                "startgroup",
                id="group",
            ),
            pytest.param(
                "https://t.me/test_bot?startchannel&admin=post_messages",
                "startchannel",
                id="channel",
            ),
            pytest.param(
                "tg://resolve?domain=test_bot&startgroup&admin=change_info",
                "startgroup",
                id="tg-resolve",
            ),
        ],
    )
    async def test_it_is_still_a_chooser_link(self, env, team, alice, url, kind):
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match=f"is a `{kind}` link"):
            await alice.in_(team).follow_deep_link(url)


class TestAttachmentMenuLinksNameTheBotWhereTheSpecPutsIt:
    """
    An `?attach=` link addresses the *chat*; the bot it is about is the parameter.

    https://core.telegram.org/api/links documents the attachment-menu link in two shapes:
    `t.me/<bot_username>?startattach[=<param>]` opens the menu in the current chat and
    names the bot in the username slot, while `t.me/<username>?attach=<bot_username>`
    (also `t.me/+<phone>?attach=<bot_username>`, plus their `tg:` twins) opens it in a
    named chat and names the bot in the parameter.

    Reading the username slot for both made every `attach` button of this bot's a link
    "to @somechat, not to this bot": the automatic scan skipped it as another chat's, and
    an explicit follow refused it before the kind's own message could ever fire.
    """

    @pytest.mark.parametrize(
        "url",
        [
            pytest.param("https://t.me/somechat?attach=test_bot", id="username-chat"),
            pytest.param("https://t.me/+15551234567?attach=test_bot", id="phone-chat"),
            pytest.param("tg://resolve?domain=somechat&attach=test_bot", id="tg-username-chat"),
            pytest.param("tg://resolve?phone=15551234567&attach=test_bot", id="tg-phone-chat"),
        ],
    )
    async def test_it_is_refused_as_an_attachment_menu_link_of_this_bot_s(
        self, env, team, alice, url
    ):
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match="attachment menu of @test_bot") as exc_info:
            await alice.in_(team).follow_deep_link(url)

        assert "not to this bot" not in str(exc_info.value)

    async def test_a_phone_chat_attach_link_is_not_refused_as_a_phone_link(self, env, team, alice):
        """
        The `+<digits>` is the chat the menu opens in, not a chat to open — so the path
        does not get to call the link a phone link and hide the bot in its query.
        """
        url = "https://t.me/+15551234567?attach=test_bot"
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError) as exc_info:
            await alice.in_(team).follow_deep_link(url)

        assert "a phone-number link" not in str(exc_info.value)

    async def test_the_scan_surfaces_an_attach_button_of_this_bot(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/somechat?attach=test_bot")

        with pytest.raises(WorldLookupError, match="only unfollowable ones") as exc_info:
            await alice.in_(team).follow_deep_link()

        assert "attachment menu of @test_bot" in str(exc_info.value)

    async def test_an_attach_link_naming_another_bot_is_refused_as_that_bot_s(
        self, env, team, alice
    ):
        url = "https://t.me/somechat?attach=other_bot"
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match="deep-links to @other_bot, not to this bot"):
            await alice.in_(team).follow_deep_link(url)

    async def test_the_scan_ignores_an_attach_button_of_another_bot(self, env, team, alice):
        await _post_deep_link(env, team, "https://t.me/somechat?attach=other_bot")

        with pytest.raises(WorldLookupError, match="carries a deep-link button") as exc_info:
            await alice.in_(team).follow_deep_link()

        assert "unfollowable" not in str(exc_info.value)

    async def test_attach_wins_over_the_startattach_it_carries(self, env, team, alice):
        """
        `t.me/<chat>?attach=<bot>&startattach=<param>` is the documented pair, where
        `startattach` is only the start parameter of the `attach` link — reading it as
        the `startattach` form would look for the bot in @somechat.
        """
        url = "https://t.me/somechat?attach=test_bot&startattach=promo"
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match="is a `attach` link"):
            await alice.in_(team).follow_deep_link(url)

    @pytest.mark.parametrize(
        "url",
        [
            pytest.param("https://t.me/test_bot?startattach", id="bare"),
            pytest.param("https://t.me/test_bot?startattach=promo", id="with-parameter"),
            pytest.param(
                "https://t.me/test_bot?startattach=promo&choose=users+groups",
                id="with-chooser",
            ),
            pytest.param("tg://resolve?domain=test_bot&startattach", id="tg"),
        ],
    )
    async def test_startattach_without_attach_still_names_the_bot_in_the_username_slot(
        self, env, team, alice, url
    ):
        """The other half of the duality: no `attach=`, so the username *is* the bot."""
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match="is a `startattach` link"):
            await alice.in_(team).follow_deep_link(url)

    async def test_a_startattach_link_of_another_bot_is_still_that_bot_s(self, env, team, alice):
        url = "https://t.me/other_bot?startattach=promo"
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match="deep-links to @other_bot"):
            await alice.in_(team).follow_deep_link(url)


class TestAQueryParameterIsReadByTheFormatThatOwnsIt:
    """
    A parameter another format carries must not outrank the format carrying it.

    Classification looked the aliases up first, so `?startapp=x&text=y` came back as a
    `draft` and was refused as an unsent draft — a refusal about the wrong link entirely,
    since a tapping user gets the Mini App and no draft at all. Telegram documents each
    of `startapp`, `startattach` and `text` as a companion of another format as well as a
    format of its own, so they are the last parameters consulted.
    """

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            pytest.param(
                "https://t.me/test_bot?startapp=x&text=hi",
                "opens the bot's main Mini App",
                id="startapp-over-text",
            ),
            pytest.param(
                "https://t.me/test_bot?text=hi&startapp=x",
                "opens the bot's main Mini App",
                id="startapp-over-text-reordered",
            ),
            pytest.param(
                "https://t.me/test_bot?startattach&text=hi",
                "is a `startattach` link",
                id="startattach-over-text",
            ),
            pytest.param(
                "https://t.me/test_bot?text=hi&profile",
                "opens the profile page rather than the chat view",
                id="profile-over-text",
            ),
            pytest.param(
                "https://t.me/test_bot?startgroup=g&text=hi",
                "is a `startgroup` link",
                id="startgroup-over-text",
            ),
            pytest.param(
                "tg://resolve?domain=test_bot&appname=shop&startapp=ref",
                "opens one of the bot's Mini Apps directly",
                id="appname-over-startapp",
            ),
        ],
    )
    async def test_the_owning_format_names_the_link(self, env, team, alice, url, expected):
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match=expected):
            await alice.in_(team).follow_deep_link(url)

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            pytest.param(
                "https://t.me/test_bot?startapp=x",
                "opens the bot's main Mini App",
                id="startapp",
            ),
            pytest.param(
                "https://t.me/test_bot?startattach=x",
                "is a `startattach` link",
                id="startattach",
            ),
            pytest.param(
                "https://t.me/test_bot?text=hi",
                "waiting as an unsent draft",
                id="text",
            ),
        ],
    )
    async def test_a_companion_parameter_alone_still_names_its_own_format(
        self, env, team, alice, url, expected
    ):
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match=expected):
            await alice.in_(team).follow_deep_link(url)


class TestAnEmptyStartWinsOverNothing:
    """
    `start` takes precedence only with a value.

    Presence alone used to be enough, so `?start=&startapp=y` was followed as a bare
    `/start` — inventing an update no client would send, and hiding the Mini App the
    button actually opens. An empty `?start=` with nothing else to be is still the bare
    `/start` that `t.me/<bot>` already is.
    """

    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            pytest.param(
                "https://t.me/test_bot?start=&startapp=y",
                "opens the bot's main Mini App",
                id="startapp",
            ),
            pytest.param(
                "https://t.me/test_bot?startapp=y&start=",
                "opens the bot's main Mini App",
                id="startapp-reordered",
            ),
            pytest.param(
                "https://t.me/test_bot?start&startgroup=g",
                "is a `startgroup` link",
                id="valueless-start",
            ),
            pytest.param(
                "https://t.me/test_bot?start=&text=hi",
                "waiting as an unsent draft",
                id="draft",
            ),
            pytest.param(
                "tg://resolve?domain=test_bot&start=&startapp=y",
                "opens the bot's main Mini App",
                id="tg",
            ),
        ],
    )
    async def test_another_start_ish_parameter_takes_the_link(
        self, env, team, alice, url, expected
    ):
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match=expected):
            await alice.in_(team).follow_deep_link(url)

    @pytest.mark.parametrize(
        "url",
        [
            pytest.param("https://t.me/test_bot?start=", id="empty-value"),
            pytest.param("https://t.me/test_bot?start", id="no-value"),
            pytest.param("https://t.me/test_bot?start=&utm_source=x", id="alongside-junk"),
            pytest.param("tg://resolve?domain=test_bot&start=", id="tg"),
        ],
    )
    async def test_an_empty_start_alone_is_the_bare_start_the_link_already_was(
        self, env, team, alice, url
    ):
        seen = []
        env.dispatcher.message.register(
            lambda message: seen.append(message.text),
            CommandStart(),
        )
        await _post_deep_link(env, team, url)

        await alice.in_(team).follow_deep_link(url)

        assert seen == ["/start"]

    async def test_a_start_with_a_value_still_wins(self, env, team, alice):
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(command.args),
            CommandStart(deep_link=True),
        )
        await _post_deep_link(env, team, "https://t.me/test_bot?start=team-9&startapp=y")

        await alice.in_(team).follow_deep_link()

        assert seen == ["team-9"]


class TestChannelWebPreviewLinks:
    """
    `t.me/s/<username>` is a channel's web preview, not a Mini App called `s`.

    It is the one `t.me` shape https://core.telegram.org/api/links does not list — that
    page documents what clients must handle, while this one is served by t.me itself as a
    web page of the channel's posts. Parsing it as a bot's direct Mini App link claimed
    both a bot named `s` and an app named after the channel, neither of which exists.
    """

    @pytest.mark.parametrize(
        "url",
        [
            pytest.param("https://t.me/s/durov", id="channel"),
            pytest.param("https://t.me/s/durov/45", id="channel-post"),
            pytest.param("https://t.me/s", id="bare"),
        ],
    )
    async def test_it_is_refused_as_a_web_preview(self, env, team, alice, url):
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match="a channel web-preview link") as exc_info:
            await alice.in_(team).follow_deep_link(url)

        assert "Mini App" not in str(exc_info.value)

    async def test_the_scan_ignores_it_rather_than_calling_it_this_bot_s(self, env, team, alice):
        """It addresses a channel, so it is never a candidate "to @test_bot"."""
        await _post_deep_link(env, team, "https://t.me/s/durov")

        with pytest.raises(WorldLookupError, match="carries a deep-link button") as exc_info:
            await alice.in_(team).follow_deep_link()

        assert "unfollowable" not in str(exc_info.value)

    async def test_a_story_link_is_still_a_story_link(self, env, team, alice):
        """`/s/` in the *second* segment is the story form, and keeps its own kind."""
        await _post_deep_link(env, team, "https://t.me/durov/s/5")

        with pytest.raises(WorldLookupError, match="a story link"):
            await alice.in_(team).follow_deep_link("https://t.me/durov/s/5")


class TestValidatePayloadEscapeHatch:
    """
    `validate_payload=False` replays what real clients deliver, charset rule or not.

    The Bot API states the rule for what a bot should put in a link (1-64 characters of
    `A-Za-z0-9_-`) but does not promise clients enforce it, and production bots do receive
    payloads that break it. The default stays strict, so a payload the bot itself built
    wrong is still named as the bug it is.
    """

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param("MjAyNS0wMS0wMQ==", id="base64-padding"),
            pytest.param("v1.2.3", id="dots"),
            pytest.param("a" * 100, id="over-64-characters"),
        ],
    )
    async def test_an_unenforced_payload_is_replayed_as_is(self, env, team, alice, payload):
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(command.args),
            CommandStart(deep_link=True),
        )
        url = f"https://t.me/test_bot?start={payload}"
        await _post_deep_link(env, team, url)

        await alice.in_(team).follow_deep_link(url, validate_payload=False)

        assert seen == [payload]

    async def test_the_scan_form_takes_it_too(self, env, team, alice):
        seen = []
        env.dispatcher.message.register(
            lambda message, command: seen.append(command.args),
            CommandStart(deep_link=True),
        )
        await _post_deep_link(env, team, "https://t.me/test_bot?start=MjAyNS0wMS0wMQ==")

        await alice.in_(team).follow_deep_link(validate_payload=False)

        assert seen == ["MjAyNS0wMS0wMQ=="]

    async def test_the_default_still_refuses_the_same_payload(self, env, team, alice):
        url = "https://t.me/test_bot?start=MjAyNS0wMS0wMQ=="
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match="Telegram would not deliver"):
            await alice.in_(team).follow_deep_link(url)

    async def test_it_does_not_make_another_kind_followable(self, env, team, alice):
        """The escape hatch drops one check, not the classification around it."""
        url = "https://t.me/test_bot?startapp=abc"
        await _post_deep_link(env, team, url)

        with pytest.raises(WorldLookupError, match="startapp"):
            await alice.in_(team).follow_deep_link(url, validate_payload=False)
