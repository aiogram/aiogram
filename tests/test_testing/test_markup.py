"""
Parse modes, applied the way the Bot API server applies them.

A world message used to keep ``<b>`` literally, which hid every
escaping bug a bot had. The parsers are TDLib's, so the errors are
Telegram's words, and aiogram's own renderers are the oracle: what
``html_decoration`` or ``markdown_decoration`` writes from a text and
its entities must parse back into the same text and entities.
"""

import datetime

import pytest

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import AnswerInlineQuery, SendMessage
from aiogram.test import ApiRejection, BotTestEnvironment
from aiogram.test.markup import apply_parse_modes, parse_entities
from aiogram.types import (
    BufferedInputFile,
    InlineQueryResultArticle,
    InputMediaPhoto,
    InputPollOption,
    InputTextMessageContent,
    MessageEntity,
    User,
)
from aiogram.utils.text_decorations import html_decoration, markdown_decoration


def parsed(text, mode="HTML", find_user=lambda user_id: None):
    plain, entities = parse_entities(text, mode, find_user)
    return plain, [entity.model_dump(exclude_none=True) for entity in entities]


def refused(text, mode="HTML"):
    with pytest.raises(ApiRejection) as failure:
        parse_entities(text, mode)
    return str(failure.value)


def entity(kind, offset, length, **fields):
    return {"type": kind, "offset": offset, "length": length, **fields}


def dumped(entities):
    """Entities as data: stored ones are bound to the bot."""
    return [item.model_dump(exclude_none=True) for item in entities or []]


class TestHtml:
    def test_tags_become_entities(self):
        assert parsed("<b>bold</b> <i>it</i> <u>u</u> <s>s</s>") == (
            "bold it u s",
            [
                entity("bold", 0, 4),
                entity("italic", 5, 2),
                entity("underline", 8, 1),
                entity("strikethrough", 10, 1),
            ],
        )

    @pytest.mark.parametrize(
        ("tag", "kind"),
        [
            ("strong", "bold"),
            ("em", "italic"),
            ("ins", "underline"),
            ("strike", "strikethrough"),
            ("del", "strikethrough"),
            ("tg-spoiler", "spoiler"),
            ("B", "bold"),
        ],
    )
    def test_every_spelling_of_a_tag(self, tag, kind):
        assert parsed(f"<{tag}>x</{tag}>") == ("x", [entity(kind, 0, 1)])

    def test_offsets_count_utf16_units(self):
        """An emoji outside the BMP is two units, as Telegram counts."""
        assert parsed("😀 <b>ё</b>") == ("😀 ё", [entity("bold", 3, 1)])

    def test_nested_tags_are_ordered_outermost_first(self):
        assert parsed("<i><b>x</b></i>") == (
            "x",
            [entity("bold", 0, 1), entity("italic", 0, 1)],
        )
        assert parsed("<b>a <i>b</i></b>") == (
            "a b",
            [entity("bold", 0, 3), entity("italic", 2, 1)],
        )

    def test_character_references_are_decoded(self):
        assert parsed("&lt;&gt;&amp;&quot; &#65;&#x42 &nbsp; &#0; &#x110000;") == (
            '<>&" AB &nbsp; &#0; &#x110000;',
            [],
        )

    def test_an_overlong_or_surrogate_reference_stays_text(self):
        assert parsed("&#0000000065; &#xD800; &#99999999;") == (
            "&#0000000065; &#xD800; &#99999999;",
            [],
        )

    def test_an_empty_tag_makes_no_entity(self):
        assert parsed("a<b></b>b") == ("ab", [])

    def test_a_link(self):
        assert parsed('<a href="https://example.com/x?y=1">x</a>') == (
            "x",
            [entity("text_link", 0, 1, url="https://example.com/x?y=1")],
        )

    def test_a_link_is_stored_as_telegram_normalizes_it(self):
        assert parsed("<a href='Example.COM'>x</a>")[1] == [
            entity("text_link", 0, 1, url="http://example.com/"),
        ]
        assert parsed('<a href="https://t.me?start=1">x</a>')[1] == [
            entity("text_link", 0, 1, url="https://t.me/?start=1"),
        ]
        assert parsed('<a href="tg://resolve?domain=bot">x</a>')[1] == [
            entity("text_link", 0, 1, url="tg://resolve?domain=bot"),
        ]
        assert parsed('<a href="tg://Resolve/?domain=bot">x</a>')[1] == [
            entity("text_link", 0, 1, url="tg://resolve?domain=bot"),
        ]

    def test_a_link_without_href_links_its_text(self):
        assert parsed("<a>https://t.me/x</a>")[1] == [
            entity("text_link", 0, 14, url="https://t.me/x"),
        ]

    @pytest.mark.parametrize(
        "href",
        [
            "ftp://example.com",
            "https://localhost",
            "https://user@example.com",
            "https://example.com:port",
            "with space.com",
            "tg://bad!host",
            "tg://",
            "ton://a.b",
            "",
        ],
    )
    def test_a_bad_link_makes_no_entity(self, href):
        assert parsed(f'<a href="{href}">x</a>') == ("x", [])

    def test_a_ton_link_passes(self):
        assert parsed('<a href="ton://site">x</a>')[1] == [
            entity("text_link", 0, 1, url="ton://site"),
        ]

    def test_a_user_link_mentions_a_known_user(self):
        alice = User(id=1, is_bot=False, first_name="Alice")

        text, [mention] = parse_entities(
            '<a href="tg://user?id=1">Alice</a>',
            "HTML",
            lambda user_id: alice if user_id == 1 else None,
        )

        assert text == "Alice"
        assert mention.type == "text_mention"
        assert mention.user == alice

    @pytest.mark.parametrize(
        "href",
        ["tg://user?id=2", "tg:user/?id=2#x", "TG://USER?x=1&id=2"],
    )
    def test_an_unknown_user_gets_no_mention(self, href):
        assert parsed(f'<a href="{href}">x</a>') == ("x", [])

    @pytest.mark.parametrize(
        "href",
        ["tg://user?id=x", "tg://user?x=1", "tg://user", "tg://users?id=1"],
    )
    def test_a_malformed_user_link_is_a_plain_tg_link(self, href):
        [link] = parsed(f'<a href="{href}">x</a>')[1]
        assert link["type"] == "text_link"

    def test_pre_with_a_language(self):
        expected = ("x", [entity("pre", 0, 1, language="python")])

        assert parsed('<pre><code class="language-python">x</code></pre>') == expected
        assert parsed('<code class="language-python"><pre>x</pre></code>') == expected

    def test_pre_and_code_without_a_language(self):
        assert parsed("<pre>x</pre> <code>y</code>") == (
            "x y",
            [entity("pre", 0, 1), entity("code", 2, 1)],
        )
        assert parsed('<code class="language-python">x</code>') == ("x", [entity("code", 0, 1)])
        assert parsed('<pre><code class="other">x</code></pre>') == ("x", [entity("pre", 0, 1)])

    def test_nothing_nests_in_code(self):
        assert parsed("<code><b>x</b> y</code> <b>z</b>") == (
            "x y z",
            [entity("code", 0, 3), entity("bold", 4, 1)],
        )

    def test_a_spoiler_span(self):
        assert parsed('<span class="tg-spoiler">x</span>') == ("x", [entity("spoiler", 0, 1)])

    def test_blockquotes(self):
        assert parsed("<blockquote>a</blockquote><blockquote expandable>b</blockquote>") == (
            "ab",
            [entity("blockquote", 0, 1), entity("expandable_blockquote", 1, 1)],
        )

    def test_a_custom_emoji(self):
        assert parsed('<tg-emoji emoji-id="5368324170671202286">👍</tg-emoji>') == (
            "👍",
            [entity("custom_emoji", 0, 2, custom_emoji_id="5368324170671202286")],
        )

    def test_a_date_and_time(self):
        assert parsed('<tg-time unix="1647531900" format="wDT">then</tg-time>') == (
            "then",
            [entity("date_time", 0, 4, unix_time=1647531900, date_time_format="wDT")],
        )
        assert parsed("<tg-time unix=1647531900>then</tg-time>")[1] == [
            entity("date_time", 0, 4, unix_time=1647531900),
        ]

    def test_attribute_values_take_every_form(self):
        assert parsed("<a href = 'https://t.me/a?b&amp;c' title=x.y-z >x</a>")[1] == [
            entity("text_link", 0, 1, url="https://t.me/a?b&c"),
        ]
        assert parsed('<a href="https://t.me/&nbsp;">x</a>')[1] == [
            entity("text_link", 0, 1, url="https://t.me/&nbsp;"),
        ]

    def test_an_unclosed_quote_runs_to_the_end(self):
        assert "Unclosed start tag at byte offset 0" in refused('<a href="x>y')

    @pytest.mark.parametrize(
        ("text", "error"),
        [
            ("a < b", 'Unsupported start tag "" at byte offset 2'),
            ("ё<br>", 'Unsupported start tag "br" at byte offset 2'),
            ("<b", "Unclosed start tag at byte offset 0"),
            ("<a href=", 'Unclosed start tag "a" at byte offset 0'),
            ("<a href=x", "Unclosed start tag at byte offset 0"),
            ("<a =x>", 'Empty attribute name in the tag "a" at byte offset 0'),
            (
                "<a href>",
                'Expected equal sign in declaration of an attribute of the tag "a" '
                "at byte offset 0",
            ),
            ("<a href=x:y>", "Unexpected end of name token at byte offset 8"),
            ("<span>x</span>", 'Tag "span" must have class "tg-spoiler" at byte offset 0'),
            ("x</b>", "Unexpected end tag at byte offset 1"),
            ("<b>x</b", "Unclosed end tag at byte offset 4"),
            (
                "<b>x</i>",
                'Unmatched end tag at byte offset 4, expected "</b>", found "</i>"',
            ),
            ("<b><i>x</i>", 'Can\'t find end tag corresponding to start tag "b"'),
            ("<tg-emoji>x</tg-emoji>", "Invalid custom emoji identifier specified"),
            ('<tg-emoji emoji-id="0">x</tg-emoji>', "Invalid custom emoji identifier specified"),
            (
                '<tg-emoji emoji-id="9223372036854775808">x</tg-emoji>',
                "Invalid custom emoji identifier specified",
            ),
            ("<tg-time>x</tg-time>", "Invalid Unix time specified"),
            ('<tg-time unix="-1">x</tg-time>', "Invalid Unix time specified"),
            (
                '<tg-time unix="1" format="x">x</tg-time>',
                "Invalid date and time format specified",
            ),
        ],
    )
    def test_broken_markup_gets_telegrams_words(self, text, error):
        assert refused(text) == f"can't parse entities: {error}"

    def test_an_empty_end_tag_closes_the_innermost(self):
        assert parsed("<b>x</>") == ("x", [entity("bold", 0, 1)])
        assert parsed("<b>x</b >") == ("x", [entity("bold", 0, 1)])


class TestMarkdownV2:
    def test_marks_become_entities(self):
        assert parsed("*b* _i_ __u__ ~s~ ||p|| `c`", "MarkdownV2") == (
            "b i u s p c",
            [
                entity("bold", 0, 1),
                entity("italic", 2, 1),
                entity("underline", 4, 1),
                entity("strikethrough", 6, 1),
                entity("spoiler", 8, 1),
                entity("code", 10, 1),
            ],
        )

    def test_escaping(self):
        assert parsed(r"1\.5 \* \\ \a \ё", "MarkdownV2") == (r"1.5 * \ a \ё", [])

    @pytest.mark.parametrize("character", list("]()>#+-=|{}.!"))
    def test_a_reserved_character_must_be_escaped(self, character):
        assert refused(f"x{character}", "MarkdownV2") == (
            f"can't parse entities: Character '{character}' is reserved and must be "
            f"escaped with the preceding '\\'"
        )

    @pytest.mark.parametrize(
        ("text", "error"),
        [
            ("*bold", "Can't find end of Bold entity at byte offset 0"),
            ("ёё _x", "Can't find end of Italic entity at byte offset 5"),
            ("__x", "Can't find end of Underline entity at byte offset 0"),
            ("||x", "Can't find end of Spoiler entity at byte offset 0"),
            ("`x", "Can't find end of Code entity at byte offset 0"),
            ("```x", "Can't find end of Pre entity at byte offset 0"),
            ("```py\nx", "Can't find end of PreCode entity at byte offset 0"),
            ("[x", "Can't find end of TextUrl entity at byte offset 0"),
            ("![x", "Can't find end of CustomEmoji entity at byte offset 0"),
            ("[x](https://t.me", "Can't find end of a URL at byte offset 4"),
            ("![x]", "Custom emoji entity must contain a tg://emoji URL"),
            ("![x](tg://emoji?id=1", "Can't find end of a custom emoji URL at byte offset 5"),
            ("![x](https://t.me)", "Custom emoji URL must have scheme tg"),
            ("![x](tg://emojis?id=1)", 'Custom emoji URL must have host "emoji"'),
            ("![x](tg://emoji)", "Custom emoji URL must have an emoji identifier"),
            ("![x](tg://emoji?x=1)", "Custom emoji URL must have an emoji identifier"),
            ("![x](tg://emoji?id=y)", "Invalid custom emoji identifier specified"),
            ("![x](tg://time?format=t)", "Invalid Unix time specified"),
            ("|x", "Character '|' is reserved and must be escaped with the preceding '\\'"),
            ("!x", "Character '!' is reserved and must be escaped with the preceding '\\'"),
        ],
    )
    def test_broken_markup_gets_telegrams_words(self, text, error):
        assert refused(text, "MarkdownV2") == f"can't parse entities: {error}"

    def test_pre_with_and_without_a_language(self):
        assert parsed("```python\nx = 1\n```\n```\ny\n```", "MarkdownV2") == (
            "x = 1\n\ny",
            [entity("pre", 0, 6, language="python"), entity("pre", 7, 1)],
        )
        assert parsed("```\r\nx```", "MarkdownV2") == ("x", [entity("pre", 0, 1)])
        assert parsed("```x```", "MarkdownV2") == ("x", [entity("pre", 0, 1)])

    def test_only_backticks_are_reserved_in_code(self):
        assert parsed(r"`a.b*c\`` ```p\`.```", "MarkdownV2") == (
            "a.b*c` p`.",
            [entity("code", 0, 6), entity("pre", 7, 3)],
        )

    def test_links(self):
        assert parsed(r"[a](https://t.me/x\)) [https://t\.me/y]", "MarkdownV2") == (
            "a https://t.me/y",
            [
                entity("text_link", 0, 1, url="https://t.me/x)"),
                entity("text_link", 2, 14, url="https://t.me/y"),
            ],
        )

    def test_a_bad_link_makes_no_entity(self):
        assert parsed("[a](ftp://x)", "MarkdownV2") == ("a", [])

    def test_a_user_link_mentions_a_known_user(self):
        alice = User(id=1, is_bot=False, first_name="Alice")

        _, [mention] = parse_entities("[A](tg://user?id=1)", "MarkdownV2", lambda _: alice)

        assert mention.type == "text_mention"

    def test_a_custom_emoji_and_a_date(self):
        assert parsed(
            "![👍](tg://emoji?id=5368324170671202286) ![now](tg://time?unix=10&format=r)",
            "MarkdownV2",
        ) == (
            "👍 now",
            [
                entity("custom_emoji", 0, 2, custom_emoji_id="5368324170671202286"),
                entity("date_time", 3, 3, unix_time=10, date_time_format="r"),
            ],
        )

    def test_an_empty_entity_is_dropped(self):
        assert parsed("a** b", "MarkdownV2") == ("a b", [])

    def test_italic_and_underline_are_told_apart_with_a_carriage_return(self):
        """The ``\\r`` trick TDLib documents, which Telegram removes."""
        assert parsed("___iu_\r__", "MarkdownV2") == (
            "iu",
            [entity("italic", 0, 2), entity("underline", 0, 2)],
        )

    def test_a_blockquote(self):
        assert parsed(">a\n>*b*\nc", "MarkdownV2") == (
            "a\nb\nc",
            [entity("blockquote", 0, 3), entity("bold", 2, 1)],
        )

    def test_an_expandable_blockquote(self):
        assert parsed(">a\n>b||\nc", "MarkdownV2") == (
            "a\nb\nc",
            [entity("expandable_blockquote", 0, 3)],
        )

    def test_an_empty_bold_separates_two_quotes(self):
        assert parsed(">a\n**>b||", "MarkdownV2") == (
            "a\nb",
            [entity("blockquote", 0, 1), entity("expandable_blockquote", 2, 1)],
        )

    def test_a_quote_ending_the_text_keeps_no_newline(self):
        assert parsed(">a\n", "MarkdownV2") == ("a", [entity("blockquote", 0, 1)])
        assert parsed(">\n>", "MarkdownV2") == ("", [])

    def test_a_spoiler_ending_a_quoted_line_is_a_spoiler(self):
        assert parsed(">||s||", "MarkdownV2") == (
            "s",
            [entity("blockquote", 0, 1), entity("spoiler", 0, 1)],
        )

    def test_a_greater_than_sign_inside_a_line_is_reserved(self):
        assert "Character '>' is reserved" in refused("a>b", "MarkdownV2")

    def test_a_quote_marker_inside_code_is_text(self):
        assert parsed("```\n>x```", "MarkdownV2") == (">x", [entity("pre", 0, 2)])


class TestMarkdown:
    def test_marks_become_entities(self):
        assert parsed("*b* _i_ `c` [l](http://x.org) [t.me/z]", "Markdown") == (
            "b i c l t.me/z",
            [
                entity("bold", 0, 1),
                entity("italic", 2, 1),
                entity("code", 4, 1),
                entity("text_link", 6, 1, url="http://x.org/"),
                entity("text_link", 8, 6, url="http://t.me/z"),
            ],
        )

    def test_escaping_and_other_characters(self):
        assert parsed(r"\_ \* \` \[ a.b ё", "Markdown") == ("_ * ` [ a.b ё", [])

    def test_pre(self):
        assert parsed("```python\nx```", "Markdown") == (
            "x",
            [entity("pre", 0, 1, language="python")],
        )
        assert parsed("```\nx```", "Markdown") == ("x", [entity("pre", 0, 1)])

    def test_an_empty_link_leaves_its_url_as_text(self):
        assert parsed("[](http://x.org) **", "Markdown") == ("(http://x.org)", [])

    def test_a_link_without_a_closing_parenthesis(self):
        assert parsed("[a](http://x.org", "Markdown") == (
            "a",
            [entity("text_link", 0, 1, url="http://x.org/")],
        )

    def test_an_unclosed_entity(self):
        assert refused("ё *b", "Markdown") == (
            "can't parse entities: Can't find end of the entity starting at byte offset 3"
        )


class TestAfterParsing:
    def test_an_unknown_parse_mode(self):
        assert refused("x", "BBCode") == "unsupported parse_mode"

    def test_the_mode_is_case_insensitive(self):
        assert parsed("<b>x</b>", "html") == ("x", [entity("bold", 0, 1)])
        assert parsed("*x*", "MARKDOWNV2") == ("x", [entity("bold", 0, 1)])

    def test_carriage_returns_are_removed(self):
        assert parsed("a\r\n<b>b\rc</b>\r") == ("a\nbc", [entity("bold", 2, 2)])

    def test_trailing_whitespace_is_trimmed(self):
        assert parsed("<b>a </b>\n\n<i> </i>") == ("a", [entity("bold", 0, 1)])

    def test_leading_whitespace_stays(self):
        assert parsed(" <b>a</b>") == (" a", [entity("bold", 1, 1)])


ROUND_TRIPS = [
    ("plain text with <&>", []),
    ("bold", [MessageEntity(type="bold", offset=0, length=4)]),
    (
        "a b c",
        [
            MessageEntity(type="bold", offset=0, length=5),
            MessageEntity(type="italic", offset=2, length=1),
        ],
    ),
    (
        "😀 ё x",
        [
            MessageEntity(type="underline", offset=0, length=2),
            MessageEntity(type="strikethrough", offset=3, length=1),
            MessageEntity(type="spoiler", offset=5, length=1),
        ],
    ),
    ("x = 1", [MessageEntity(type="code", offset=0, length=5)]),
    ("a.b", [MessageEntity(type="pre", offset=0, length=3)]),
    (
        "go there",
        [MessageEntity(type="text_link", offset=3, length=5, url="https://t.me/x")],
    ),
    ("quote", [MessageEntity(type="blockquote", offset=0, length=5)]),
    ("more", [MessageEntity(type="expandable_blockquote", offset=0, length=4)]),
    (
        "at noon",
        [
            MessageEntity(
                type="date_time",
                offset=3,
                length=4,
                unix_time=1647531900,
                date_time_format="t",
            ),
        ],
    ),
]


#: aiogram's MarkdownV2 renders a custom emoji as
#: ``tg://emoji?emoji_id=``, a link Telegram refuses, so this one is
#: checked through HTML only.
CUSTOM_EMOJI = (
    "👍",
    [
        MessageEntity(
            type="custom_emoji",
            offset=0,
            length=2,
            custom_emoji_id="5368324170671202286",
        ),
    ],
)


class TestRoundTrip:
    """
    What aiogram renders from entities parses back into them.

    Two renderings are left out because Telegram would not read them
    either: HTML ``pre`` with a language, which aiogram writes as a
    ``language=`` attribute rather than ``class="language-..."``, and
    the MarkdownV2 custom emoji above.
    """

    @pytest.mark.parametrize(("text", "entities"), [*ROUND_TRIPS, CUSTOM_EMOJI])
    def test_through_html(self, text, entities):
        markup = html_decoration.unparse(text, entities)

        assert parse_entities(markup, "HTML") == (text, entities)

    @pytest.mark.parametrize(("text", "entities"), ROUND_TRIPS)
    def test_through_markdown_v2(self, text, entities):
        markup = markdown_decoration.unparse(text, entities)

        assert parse_entities(markup, "MarkdownV2") == (text, entities)

    def test_pre_with_a_language_through_markdown_v2(self):
        entities = [MessageEntity(type="pre", offset=0, length=5, language="py")]
        markup = markdown_decoration.unparse("x = 1", entities)

        assert parse_entities(markup, "MarkdownV2") == ("x = 1", entities)

    def test_a_mention_through_both(self):
        alice = User(id=1, is_bot=False, first_name="Alice")
        entities = [MessageEntity(type="text_mention", offset=0, length=5, user=alice)]
        for decoration, mode in ((html_decoration, "HTML"), (markdown_decoration, "MarkdownV2")):
            markup = decoration.unparse("Alice", entities)

            assert parse_entities(markup, mode, lambda _: alice) == ("Alice", entities)


class TestMethods:
    def test_a_method_without_parse_modes_is_left_alone(self):
        method = SendMessage(chat_id=1, text="<b>x</b>", parse_mode=None)

        assert apply_parse_modes(method, lambda _: None) is method

    def test_nested_items_are_parsed(self):
        method = AnswerInlineQuery(
            inline_query_id="q",
            results=[
                InlineQueryResultArticle(
                    id="1",
                    title="t",
                    input_message_content=InputTextMessageContent(
                        message_text="<b>x</b>",
                        parse_mode="HTML",
                    ),
                ),
            ],
        )

        applied = apply_parse_modes(method, lambda _: None)

        content = applied.results[0].input_message_content
        assert content.message_text == "x"
        assert content.entities == [MessageEntity(type="bold", offset=0, length=1)]
        assert content.parse_mode is None
        # The call itself is not changed.
        assert method.results[0].input_message_content.message_text == "<b>x</b>"


class TestThroughTheBot:
    async def test_a_message_is_stored_parsed(self, env, private):
        message = await env.bot.send_message(private.id, "<b>Night</b> falls", parse_mode="HTML")

        stored = private.messages[-1]
        assert stored.text == message.text == "Night falls"
        assert dumped(stored.entities) == [entity("bold", 0, 5)]
        assert stored.html_text == "<b>Night</b> falls"

    async def test_the_bots_default_parse_mode_applies(self, blueprint, dp):
        blueprint.default = DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2)
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            chat = environment.chat(blueprint.chats[0])
            await environment.bot.send_message(chat.id, "*Day*")

            assert chat.messages[-1].text == "Day"
            assert dumped(chat.messages[-1].entities) == [entity("bold", 0, 3)]
        finally:
            await environment.dispose()

    async def test_broken_markup_is_refused_in_telegrams_words(self, env, private):
        before = len(private.messages)

        with pytest.raises(TelegramBadRequest) as failure:
            await env.bot.send_message(private.id, "Score: 3 < 5", parse_mode="HTML")

        assert failure.value.message == (
            'Bad Request: can\'t parse entities: Unsupported start tag "" at byte offset 9'
        )
        assert len(private.messages) == before
        # The call is recorded as the bot made it.
        assert env.calls.last(SendMessage).parse_mode == "HTML"

    async def test_parse_mode_wins_over_explicit_entities(self, env, private):
        await env.bot.send_message(
            private.id,
            "<i>x</i>",
            parse_mode="HTML",
            entities=[MessageEntity(type="bold", offset=0, length=3)],
        )

        assert private.messages[-1].text == "x"
        assert dumped(private.messages[-1].entities) == [entity("italic", 0, 1)]

    @pytest.mark.parametrize("mode", [None, "none", "None"])
    async def test_explicit_entities_stand_without_a_parse_mode(self, env, private, mode):
        entities = [MessageEntity(type="bold", offset=0, length=3)]

        await env.bot.send_message(private.id, "<i>", parse_mode=mode, entities=entities)

        assert private.messages[-1].text == "<i>"
        assert dumped(private.messages[-1].entities) == dumped(entities)

    async def test_an_unknown_parse_mode_is_refused(self, env, private):
        with pytest.raises(TelegramBadRequest, match="Bad Request: unsupported parse_mode"):
            await env.bot.send_message(private.id, "x", parse_mode="BBCode")

    async def test_a_caption_and_its_edit(self, env, private):
        photo = BufferedInputFile(b"img", filename="p.jpg")
        sent = await env.bot.send_photo(
            private.id,
            photo,
            caption="<u>day</u> 1",
            parse_mode="HTML",
        )
        assert sent.caption == "day 1"
        assert dumped(sent.caption_entities) == [entity("underline", 0, 3)]

        edited = await env.bot.edit_message_caption(
            chat_id=private.id,
            message_id=sent.message_id,
            caption="_night_",
            parse_mode="MarkdownV2",
        )

        assert edited.caption == "night"
        assert dumped(edited.caption_entities) == [entity("italic", 0, 5)]

    async def test_an_edited_text(self, env, private):
        sent = await env.bot.send_message(private.id, "x")

        edited = await env.bot.edit_message_text(
            chat_id=private.id,
            message_id=sent.message_id,
            text="<s>x</s> y",
            parse_mode="HTML",
        )

        assert edited.text == "x y"
        assert dumped(edited.entities) == [entity("strikethrough", 0, 1)]

    async def test_a_media_groups_items(self, env, private):
        photo = BufferedInputFile(b"img", filename="p.jpg")
        await env.bot.send_media_group(
            private.id,
            [
                InputMediaPhoto(media=photo, caption="<b>a</b>", parse_mode="HTML"),
                InputMediaPhoto(media=photo, caption="*b*", parse_mode="MarkdownV2"),
            ],
        )

        assert [m.caption for m in private.messages[-2:]] == ["a", "b"]

    async def test_a_poll_question_and_options(self, env, private):
        await env.bot.send_poll(
            private.id,
            question="<b>Who?</b>",
            question_parse_mode="HTML",
            options=[
                InputPollOption(text="*Bob*", text_parse_mode="MarkdownV2"),
                InputPollOption(text="Eve"),
            ],
        )

        poll = private.messages[-1].poll
        assert poll.question == "Who?"
        assert [option.text for option in poll.options] == ["Bob", "Eve"]

    async def test_a_mention_names_the_declared_user(self, env, private, blueprint):
        alice = blueprint.users[0]

        await env.bot.send_message(
            private.id,
            f'<a href="tg://user?id={alice.id}">you</a>',
            parse_mode="HTML",
        )

        [mention] = private.messages[-1].entities
        assert mention.type == "text_mention"
        assert mention.user.id == alice.id

    async def test_the_bot_can_mention_itself(self, env, private):
        await env.bot.send_message(
            private.id,
            f'<a href="tg://user?id={env.bot.id}">me</a>',
            parse_mode="HTML",
        )

        assert private.messages[-1].entities[0].user.id == env.bot.id

    async def test_an_override_answers_before_parsing(self, env, private):
        env.on(SendMessage).returns(True)

        assert await env.bot.send_message(private.id, "<x>", parse_mode="HTML") is True

    async def test_a_date_survives_the_world(self, env, private):
        moment = int(datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc).timestamp())

        await env.bot.send_message(
            private.id,
            f'<tg-time unix="{moment}">then</tg-time>',
            parse_mode="HTML",
        )

        assert private.messages[-1].entities[0].unix_time == moment
