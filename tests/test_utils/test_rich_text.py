import pytest

from aiogram.types import (
    Animation,
    Audio,
    Location,
    PhotoSize,
    RichBlockAnchor,
    RichBlockAnimation,
    RichBlockAudio,
    RichBlockBlockQuotation,
    RichBlockCaption,
    RichBlockCollage,
    RichBlockDetails,
    RichBlockDivider,
    RichBlockFooter,
    RichBlockList,
    RichBlockListItem,
    RichBlockMap,
    RichBlockMathematicalExpression,
    RichBlockParagraph,
    RichBlockPhoto,
    RichBlockPreformatted,
    RichBlockPullQuotation,
    RichBlockSectionHeading,
    RichBlockSlideshow,
    RichBlockTable,
    RichBlockTableCell,
    RichBlockThinking,
    RichBlockVideo,
    RichBlockVoiceNote,
    RichMessage,
    RichTextAnchor,
    RichTextAnchorLink,
    RichTextBankCardNumber,
    RichTextBold,
    RichTextBotCommand,
    RichTextCashtag,
    RichTextCode,
    RichTextCustomEmoji,
    RichTextDateTime,
    RichTextEmailAddress,
    RichTextHashtag,
    RichTextItalic,
    RichTextMarked,
    RichTextMathematicalExpression,
    RichTextMention,
    RichTextPhoneNumber,
    RichTextReference,
    RichTextReferenceLink,
    RichTextSpoiler,
    RichTextStrikethrough,
    RichTextSubscript,
    RichTextSuperscript,
    RichTextTextMention,
    RichTextUnderline,
    RichTextUrl,
    User,
    Video,
    Voice,
)
from aiogram.utils.rich_text import rich_message_to_html, rich_message_to_markdown


def render_html(blocks):
    return rich_message_to_html(RichMessage(blocks=blocks))


def render_md(blocks):
    return rich_message_to_markdown(RichMessage(blocks=blocks))


def _html_style_for_tests():
    from aiogram.utils.rich_text import _html_style  # noqa: PLC2701

    return _html_style


class TestRichTextEntities:
    @pytest.mark.parametrize(
        "text_node,expected_html,expected_md",
        [
            [
                RichTextBold(text="test"),
                "<b>test</b>",
                "**test**",
            ],
            [
                RichTextItalic(text="test"),
                "<i>test</i>",
                "*test*",
            ],
            [
                RichTextUnderline(text="test"),
                "<u>test</u>",
                "<u>test</u>",
            ],
            [
                RichTextStrikethrough(text="test"),
                "<s>test</s>",
                "~~test~~",
            ],
            [
                RichTextSpoiler(text="test"),
                "<tg-spoiler>test</tg-spoiler>",
                "||test||",
            ],
            [
                RichTextMarked(text="test"),
                "<mark>test</mark>",
                "==test==",
            ],
            [
                RichTextSubscript(text="test"),
                "<sub>test</sub>",
                "<sub>test</sub>",
            ],
            [
                RichTextSuperscript(text="test"),
                "<sup>test</sup>",
                "<sup>test</sup>",
            ],
            [
                RichTextCode(text="test"),
                "<code>test</code>",
                "`test`",
            ],
            [
                RichTextCustomEmoji(custom_emoji_id="id", alternative_text=":emoji:"),
                '<tg-emoji emoji-id="id">:emoji:</tg-emoji>',
                "![:emoji:](tg://emoji?id=id)",
            ],
            [
                RichTextDateTime(text="tomorrow", unix_time=1700000000, date_time_format="%H:%M"),
                '<tg-time unix="1700000000" format="%H:%M">tomorrow</tg-time>',
                "![tomorrow](tg://time?unix=1700000000&format=%25H%3A%25M)",
            ],
            [
                RichTextMathematicalExpression(expression="x^2"),
                "<tg-math>x^2</tg-math>",
                "$x^2$",
            ],
            [
                RichTextUrl(text="link", url="https://example.com"),
                '<a href="https://example.com">link</a>',
                "[link](https://example.com)",
            ],
            [
                RichTextEmailAddress(text="a@b.c", email_address="a@b.c"),
                '<a href="mailto:a@b.c">a@b.c</a>',
                "[a@b\\.c](mailto:a@b.c)",
            ],
            [
                RichTextPhoneNumber(text="+123", phone_number="+123"),
                '<a href="tel:+123">+123</a>',
                "[\\+123](tel:+123)",
            ],
            [
                RichTextMention(text="@dev", username="dev"),
                '<a href="https://t.me/dev">@dev</a>',
                "[@dev](https://t.me/dev)",
            ],
            [
                RichTextTextMention(
                    text="User", user=User(id=42, is_bot=False, first_name="Test")
                ),
                '<a href="tg://user?id=42">User</a>',
                "[User](tg://user?id=42)",
            ],
            [
                RichTextHashtag(text="#tag", hashtag="#tag"),
                "#tag",
                "\\#tag",
            ],
            [
                RichTextCashtag(text="$USD", cashtag="$USD"),
                "$USD",
                "$USD",
            ],
            [
                RichTextBotCommand(text="/start", bot_command="/start"),
                "/start",
                "/start",
            ],
            [
                RichTextBankCardNumber(text="1234", bank_card_number="1234"),
                "1234",
                "1234",
            ],
            [
                RichTextAnchor(name="chapter-1"),
                '<a name="chapter-1"></a>',
                '<a name="chapter-1"></a>',
            ],
            [
                RichTextAnchorLink(text="go", anchor_name="chapter-1"),
                '<a href="#chapter-1">go</a>',
                '<a href="#chapter-1">go</a>',
            ],
            [
                RichTextReference(text="ref", name="note-1"),
                '<tg-reference name="note-1">ref</tg-reference>',
                "[^note-1]: ref",
            ],
            [
                RichTextReferenceLink(text="use", reference_name="note-1"),
                '<a href="#note-1">use</a>',
                "use[^note-1]",
            ],
        ],
    )
    def test_text_entity(self, text_node, expected_html, expected_md):
        blocks = [RichBlockParagraph(text=text_node)]
        assert render_html(blocks) == f"<p>{expected_html}</p>"
        assert render_md(blocks) == expected_md

    def test_nested_entities(self):
        node = RichTextBold(
            text=[RichTextItalic(text="both")],
        )
        assert render_html([RichBlockParagraph(text=node)]) == "<p><b><i>both</i></b></p>"
        assert render_md([RichBlockParagraph(text=node)]) == "***both***"

    def test_plain_text_list(self):
        node = [RichTextBold(text="a"), RichTextItalic(text="b")]
        assert render_html([RichBlockParagraph(text=node)]) == "<p><b>a</b><i>b</i></p>"

    def test_html_escaping(self):
        node = RichTextBold(text='<b>&</b>"')
        assert (
            render_html([RichBlockParagraph(text=node)])
            == '<p><b>&lt;b&gt;&amp;&lt;/b&gt;"</b></p>'
        )

    def test_code_not_escaped(self):
        node = RichTextCode(text="<b>&")
        assert render_html([RichBlockParagraph(text=node)]) == "<p><code><b>&</code></p>"


class TestRichBlocks:
    def test_paragraph(self):
        assert render_html([RichBlockParagraph(text="hello")]) == "<p>hello</p>"
        assert render_md([RichBlockParagraph(text="hello")]) == "hello"

    def test_section_heading(self):
        block = RichBlockSectionHeading(text="Title", size=2)
        assert render_html([block]) == "<h2>Title</h2>"
        assert render_md([block]) == "## Title"

    def test_preformatted(self):
        block = RichBlockPreformatted(text="print('hi')", language="python")
        assert (
            render_html([block]) == "<pre><code class=\"language-python\">print('hi')</code></pre>"
        )
        assert render_md([block]) == "```python\nprint('hi')\n```"

    def test_preformatted_without_language(self):
        block = RichBlockPreformatted(text="plain")
        assert render_html([block]) == "<pre>plain</pre>"
        assert render_md([block]) == "```\nplain\n```"

    def test_footer(self):
        block = RichBlockFooter(text="foot")
        assert render_html([block]) == "<footer>foot</footer>"
        assert render_md([block]) == "foot"

    def test_divider(self):
        assert render_html([RichBlockDivider()]) == "<hr/>"
        assert render_md([RichBlockDivider()]) == "---"

    def test_mathematical_expression(self):
        block = RichBlockMathematicalExpression(expression="E = mc^2")
        assert render_html([block]) == "<tg-math-block>E = mc^2</tg-math-block>"
        assert render_md([block]) == "$$E = mc^2$$"

    def test_anchor(self):
        block = RichBlockAnchor(name="top")
        assert render_html([block]) == '<a name="top"></a>'
        assert render_md([block]) == '<a name="top"></a>'

    def test_unordered_list(self):
        block = RichBlockList(
            items=[
                RichBlockListItem(label="one", blocks=[RichBlockParagraph(text="one")]),
                RichBlockListItem(label="two", blocks=[RichBlockParagraph(text="two")]),
            ]
        )
        assert render_html([block]) == "<ul><li><p>one</p></li><li><p>two</p></li></ul>"
        assert render_md([block]) == "- one\n- two"

    def test_checkbox_list(self):
        block = RichBlockList(
            items=[
                RichBlockListItem(
                    label="a",
                    blocks=[RichBlockParagraph(text="a")],
                    has_checkbox=True,
                    is_checked=True,
                ),
                RichBlockListItem(
                    label="b",
                    blocks=[RichBlockParagraph(text="b")],
                    has_checkbox=True,
                    is_checked=False,
                ),
            ]
        )
        assert (
            render_html([block])
            == '<ul><li><input type="checkbox" checked><p>a</p></li><li><input type="checkbox"><p>b</p></li></ul>'
        )
        assert render_md([block]) == "- [x] a\n- [ ] b"

    def test_ordered_list(self):
        block = RichBlockList(
            items=[
                RichBlockListItem(label="a", blocks=[RichBlockParagraph(text="a")], value=3),
                RichBlockListItem(label="b", blocks=[RichBlockParagraph(text="b")]),
            ]
        )
        assert (
            render_html([block])
            == '<ol start="3"><li value="3"><p>a</p></li><li><p>b</p></li></ol>'
        )
        assert render_md([block]) == "3. a\n4. b"

    def test_block_quotation(self):
        block = RichBlockBlockQuotation(
            blocks=[RichBlockParagraph(text="quoted")],
            credit="Author",
        )
        assert render_html([block]) == "<blockquote><p>quoted</p><cite>Author</cite></blockquote>"
        assert render_md([block]) == "> quoted\n> Author"

    def test_block_quotation_without_credit(self):
        block = RichBlockBlockQuotation(blocks=[RichBlockParagraph(text="quoted")])
        assert render_html([block]) == "<blockquote><p>quoted</p></blockquote>"
        assert render_md([block]) == "> quoted"

    def test_pull_quotation(self):
        block = RichBlockPullQuotation(text="pull", credit="Me")
        assert render_html([block]) == "<aside>pull<cite>Me</cite></aside>"
        assert render_md([block]) == "<aside>pull<cite>Me</cite></aside>"

    def test_details(self):
        block = RichBlockDetails(
            summary="More",
            blocks=[RichBlockParagraph(text="hidden")],
            is_open=True,
        )
        assert (
            render_html([block]) == "<details open><summary>More</summary><p>hidden</p></details>"
        )
        assert render_md([block]) == "<details open><summary>More</summary>\n\nhidden\n</details>"

    def test_table(self):
        block = RichBlockTable(
            cells=[
                [
                    RichBlockTableCell(text="H1", align="left", valign="top", is_header=True),
                    RichBlockTableCell(text="H2", align="center", valign="top", is_header=True),
                ],
                [
                    RichBlockTableCell(text="a", align="left", valign="top"),
                    RichBlockTableCell(text="b", align="right", valign="top"),
                ],
            ],
            is_bordered=True,
        )
        assert (
            render_html([block]) == '<table bordered><tr><th align="left" valign="top">H1</th>'
            '<th align="center" valign="top">H2</th></tr>'
            '<tr><td align="left" valign="top">a</td>'
            '<td align="right" valign="top">b</td></tr></table>'
        )
        assert render_md([block]) == "| H1 | H2 |\n| :--- | :---: |\n| a | b |"

    def test_table_caption(self):
        block = RichBlockTable(
            cells=[
                [
                    RichBlockTableCell(text="H", align="left", valign="top", is_header=True),
                ]
            ],
            caption="Table caption",
        )
        assert (
            render_html([block])
            == '<table><caption>Table caption</caption><tr><th align="left" valign="top">H</th></tr></table>'
        )
        assert render_md([block]) == "| H |\n| :--- |\nTable caption"

    def test_map(self):
        block = RichBlockMap(
            location=Location(latitude=41.9, longitude=12.5),
            zoom=14,
            width=600,
            height=400,
        )
        assert render_html([block]) == '<tg-map lat="41.9" long="12.5" zoom="14"/>'
        assert render_md([block]) == '<tg-map lat="41.9" long="12.5" zoom="14"/>'

    def test_thinking(self):
        block = RichBlockThinking(text="reasoning")
        assert render_html([block]) == "<tg-thinking>reasoning</tg-thinking>"
        assert render_md([block]) == "reasoning"

    def test_collage(self):
        block = RichBlockCollage(blocks=[RichBlockParagraph(text="a")])
        assert render_html([block]) == "<tg-collage><p>a</p></tg-collage>"
        assert render_md([block]) == "<tg-collage>a</tg-collage>"

    def test_slideshow(self):
        block = RichBlockSlideshow(blocks=[RichBlockParagraph(text="a")])
        assert render_html([block]) == "<tg-slideshow><p>a</p></tg-slideshow>"
        assert render_md([block]) == "<tg-slideshow>a</tg-slideshow>"

    @pytest.mark.parametrize(
        "media_block",
        [
            RichBlockAnimation(
                animation=Animation(file_id="f", file_unique_id="u", width=1, height=1, duration=1)
            ),
            RichBlockAudio(audio=Audio(file_id="f", file_unique_id="u", duration=1)),
            RichBlockPhoto(photo=[PhotoSize(file_id="f", file_unique_id="u", width=1, height=1)]),
            RichBlockVideo(
                video=Video(file_id="f", file_unique_id="u", width=1, height=1, duration=1)
            ),
            RichBlockVoiceNote(voice_note=Voice(file_id="f", file_unique_id="u", duration=1)),
        ],
    )
    def test_media_blocks_without_caption(self, media_block):
        assert render_html([media_block]) == ""
        assert render_md([media_block]) == ""

    def test_media_blocks_with_caption(self):
        block = RichBlockPhoto(
            photo=[PhotoSize(file_id="f", file_unique_id="u", width=1, height=1)],
            caption=RichBlockCaption(text="Caption"),
        )
        assert render_html([block]) == "<figcaption>Caption</figcaption>"
        assert render_md([block]) == "Caption"

    def test_unsupported_block_type(self):
        from aiogram.utils.rich_text import _render_block  # noqa: PLC2701

        class UnknownBlock:
            pass

        with pytest.raises(TypeError, match="Unsupported rich block"):
            _render_block(UnknownBlock(), _html_style_for_tests())

    def test_unsupported_text_type(self):
        from aiogram.utils.rich_text import _render_text  # noqa: PLC2701

        class UnknownText:
            pass

        with pytest.raises(TypeError, match="Unsupported rich text node"):
            _render_text(UnknownText(), _html_style_for_tests())


class TestNesting:
    def test_max_depth(self):
        node = RichTextBold(text="deep")
        for _ in range(17):
            node = RichTextBold(text=[node])
        with pytest.raises(ValueError, match="nesting exceeds the maximum of 16"):
            render_html([RichBlockParagraph(text=node)])


class TestRichMessageHelper:
    def test_rich_message_to_html(self):
        msg = RichMessage(blocks=[RichBlockParagraph(text="hi")])
        assert rich_message_to_html(msg) == "<p>hi</p>"

    def test_rich_message_to_markdown(self):
        msg = RichMessage(blocks=[RichBlockParagraph(text="hi")])
        assert rich_message_to_markdown(msg) == "hi"
