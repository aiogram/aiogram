from collections.abc import Iterator
from typing import Annotated, Any, get_args, get_origin

import pytest
from pydantic import BaseModel
from typing_extensions import TypeAliasType

from aiogram.test import WorldLookupError, rich
from aiogram.test.rich import (
    counterpart,
    materialize_rich_message,
)
from aiogram.test.synthesis import SynthesisContext, list_item, synthesize
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMedia,
    InputMediaPhoto,
    InputRichBlockButtons,
    InputRichBlockDetails,
    InputRichBlockList,
    InputRichBlockListItem,
    InputRichBlockMap,
    InputRichBlockParagraph,
    InputRichBlockPhoto,
    InputRichBlockTable,
    InputRichMessage,
    Location,
    RichBlockButtons,
    RichBlockDetails,
    RichBlockList,
    RichBlockMap,
    RichBlockParagraph,
    RichBlockPhoto,
    RichBlockTable,
    RichBlockTableCell,
    RichMessageButton,
    RichTextBold,
    RichTextButton,
)


def models_in(annotation: Any) -> Iterator[type[BaseModel]]:
    """Every model class an annotation can hold, through containers."""
    if isinstance(annotation, TypeAliasType):
        yield from models_in(annotation.__value__)
        return
    # Python 3.10 reports `list[X]` as a type, so ask for the origin.
    if isinstance(annotation, type) and get_origin(annotation) is None:
        if issubclass(annotation, BaseModel):
            yield annotation
        return
    if get_origin(annotation) is Annotated:
        yield from models_in(get_args(annotation)[0])
        return
    for argument in get_args(annotation):
        yield from models_in(argument)


def button_block(callback_data="go", url=None):
    return InputRichBlockButtons(
        buttons=[RichMessageButton(text="Go", callback_data=callback_data, url=url)],
    )


def nested_button(callback_data):
    return InputRichBlockParagraph(
        text=[
            "press ",
            RichTextBold(
                text=RichTextButton(
                    button=RichMessageButton(text="here", callback_data=callback_data),
                ),
            ),
        ],
    )


class TestInputNamingConvention:
    """The conversion relies on it, so a bump that breaks it must fail here."""

    def reachable(self):
        seen, stack = set(), [InputRichMessage]
        while stack:
            model = stack.pop()
            if model in seen:
                continue
            seen.add(model)
            for info in model.model_fields.values():
                stack.extend(models_in(info.annotation))
        return seen

    def test_every_input_rich_model_has_a_stored_counterpart(self):
        rich = [m for m in self.reachable() if m.__name__.startswith("InputRich")]

        assert rich
        assert [m.__name__ for m in rich if counterpart(m) is None] == ["InputRichMessageMedia"]

    def test_every_input_media_field_maps_to_a_synthesizable_field(self):
        context = SynthesisContext()
        for model in self.reachable():
            target = counterpart(model)
            if target is None:
                continue
            for name, info in model.model_fields.items():
                if any(issubclass(m, InputMedia) for m in models_in(info.annotation)):
                    synthesize(target.model_fields[name].annotation, context, name=name)

    def test_a_model_without_counterpart_is_reported(self):
        class InputRichNothing(BaseModel):
            pass

        assert counterpart(InputRichNothing) is None
        assert counterpart(InputMediaPhoto) is None


class TestRichContentIsCarried:
    async def send(self, env, chat, **content):
        return await env.bot.send_rich_message(
            chat_id=chat.id,
            rich_message=InputRichMessage(**content),
        )

    async def test_blocks_are_stored_in_order(self, env, private):
        cell = RichBlockTableCell(align="left", valign="top", text="cell")
        message = await self.send(
            env,
            private,
            is_rtl=True,
            blocks=[
                InputRichBlockParagraph(text=["Hello ", RichTextBold(text="world")]),
                InputRichBlockList(
                    items=[InputRichBlockListItem(blocks=[InputRichBlockParagraph(text="one")])],
                ),
                InputRichBlockTable(cells=[[cell]]),
                button_block(),
            ],
        )

        stored = private.messages[-1].rich_message
        assert message.rich_message == stored
        assert stored.is_rtl is True
        paragraph, listing, table, buttons = stored.blocks
        assert isinstance(paragraph, RichBlockParagraph)
        assert paragraph.text[0] == "Hello "
        assert paragraph.text[1].text == "world"
        assert isinstance(listing, RichBlockList)
        assert listing.items[0].blocks[0].text == "one"
        assert isinstance(table, RichBlockTable)
        assert table.cells[0][0].text == "cell"
        assert isinstance(buttons, RichBlockButtons)
        assert buttons.buttons[0].callback_data == "go"

    async def test_media_in_a_block_is_synthesized_non_empty(self, env, private):
        message = await self.send(
            env,
            private,
            blocks=[InputRichBlockPhoto(photo=InputMediaPhoto(media="id", has_spoiler=True))],
        )

        (photo,) = message.rich_message.blocks
        assert isinstance(photo, RichBlockPhoto)
        assert photo.photo
        assert photo.has_spoiler is True

    async def test_a_media_caption_does_not_become_the_blocks_caption(self, env, private):
        message = await self.send(
            env,
            private,
            blocks=[InputRichBlockPhoto(photo=InputMediaPhoto(media="id", caption="hi"))],
        )

        (photo,) = message.rich_message.blocks
        assert photo.caption is None

    async def test_unset_required_fields_get_zero_values(self, env, private):
        message = await self.send(
            env,
            private,
            blocks=[
                InputRichBlockMap(location=Location(latitude=1, longitude=2)),
                InputRichBlockList(
                    items=[InputRichBlockListItem(blocks=[InputRichBlockParagraph(text="x")])],
                ),
            ],
        )

        mapped, listing = message.rich_message.blocks
        assert isinstance(mapped, RichBlockMap)
        assert (mapped.zoom, mapped.width, mapped.height) == (0, 0, 0)
        assert listing.items[0].label == ""

    async def test_stated_optional_values_are_carried(self, env, private):
        message = await self.send(
            env,
            private,
            blocks=[InputRichBlockMap(location=Location(latitude=1, longitude=2), zoom=13)],
        )

        assert message.rich_message.blocks[0].zoom == 13

    @pytest.mark.parametrize("content", [{"html": "<p>hi</p>"}, {"markdown": "*hi*"}])
    async def test_markup_only_content_stores_no_blocks(self, env, private, content):
        message = await self.send(env, private, **content)

        assert private.messages[-1] is message
        assert message.rich_message.blocks == []

    async def test_a_copy_keeps_the_rich_content(self, env, private, team):
        sent = await self.send(env, private, blocks=[button_block()])

        await env.bot.copy_message(
            chat_id=team.id,
            from_chat_id=private.id,
            message_id=sent.message_id,
        )
        await env.bot.forward_message(
            chat_id=team.id,
            from_chat_id=private.id,
            message_id=sent.message_id,
        )

        assert team.messages[-2].rich_message == sent.rich_message
        assert team.messages[-1].rich_message == sent.rich_message

    def test_the_conversion_needs_no_environment(self):
        stored = materialize_rich_message(
            InputRichMessage(blocks=[InputRichBlockParagraph(text="x")]),
            SynthesisContext(),
        )

        assert stored.blocks[0].text == "x"


class TestEditingReplacesContent:
    async def test_text_becomes_rich(self, env, private):
        sent = await env.bot.send_message(chat_id=private.id, text="plain")

        edited = await env.bot.edit_message_text(
            chat_id=private.id,
            message_id=sent.message_id,
            rich_message=InputRichMessage(blocks=[InputRichBlockParagraph(text="rich")]),
        )

        assert edited.text is None
        assert edited.rich_message.blocks[0].text == "rich"

    async def test_rich_becomes_text(self, env, private):
        sent = await env.bot.send_rich_message(
            chat_id=private.id,
            rich_message=InputRichMessage(blocks=[InputRichBlockParagraph(text="rich")]),
        )

        edited = await env.bot.edit_message_text(
            chat_id=private.id,
            message_id=sent.message_id,
            text="plain",
        )

        assert edited.text == "plain"
        assert edited.rich_message is None

    async def test_media_replaces_rich_content(self, env, private):
        sent = await env.bot.send_rich_message(
            chat_id=private.id,
            rich_message=InputRichMessage(blocks=[InputRichBlockParagraph(text="rich")]),
        )

        edited = await env.bot.edit_message_media(
            chat_id=private.id,
            message_id=sent.message_id,
            media=InputMediaPhoto(media="photo-id"),
        )

        assert edited.photo
        assert edited.rich_message is None

    async def test_a_text_edit_without_markup_removes_the_keyboard(self, env, private):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )
        sent = await env.bot.send_message(chat_id=private.id, text="a", reply_markup=markup)

        edited = await env.bot.edit_message_text(
            chat_id=private.id,
            message_id=sent.message_id,
            text="b",
        )

        assert edited.reply_markup is None

    async def test_a_markup_edit_keeps_the_rich_content(self, env, private):
        sent = await env.bot.send_rich_message(
            chat_id=private.id,
            rich_message=InputRichMessage(blocks=[InputRichBlockParagraph(text="rich")]),
        )
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )

        edited = await env.bot.edit_message_reply_markup(
            chat_id=private.id,
            message_id=sent.message_id,
            reply_markup=markup,
        )

        assert edited.rich_message == sent.rich_message
        assert edited.reply_markup.inline_keyboard[0][0].callback_data == "go"


class TestRichButtonsAreClickable:
    @pytest.fixture
    def seen(self, env):
        seen = []
        env.dispatcher.callback_query.register(
            lambda query: seen.append((query.data, query.message.message_id)),
        )
        return seen

    async def send(self, env, chat, *blocks, reply_markup=None):
        return await env.bot.send_rich_message(
            chat_id=chat.id,
            rich_message=InputRichMessage(blocks=list(blocks)),
            reply_markup=reply_markup,
        )

    async def test_a_button_block(self, env, private, alice, seen):
        sent = await self.send(env, private, button_block("go"))

        await alice.click("go")

        assert seen == [("go", sent.message_id)]

    @pytest.mark.parametrize(
        "wrap",
        [
            lambda block: InputRichBlockList(items=[InputRichBlockListItem(blocks=[block])]),
            lambda block: InputRichBlockDetails(summary="more", blocks=[block]),
        ],
        ids=["list item", "details"],
    )
    async def test_a_button_nested_in_text(self, env, private, alice, seen, wrap):
        sent = await self.send(env, private, wrap(nested_button("deep")))

        await alice.click("deep")

        assert seen == [("deep", sent.message_id)]

    async def test_a_rich_button_object(self, env, private, alice, seen):
        sent = await self.send(env, private, button_block("go"))
        (block,) = sent.rich_message.blocks

        await alice.click(block.buttons[0])

        assert seen == [("go", sent.message_id)]

    async def test_the_keyboard_comes_before_the_blocks(self, env, private, alice):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="K", url="https://example.com/k")]],
        )
        sent = await self.send(
            env,
            private,
            button_block("x", url=None),
            reply_markup=markup,
        )

        buttons = [button for _, button in alice._iter_buttons([sent])]

        assert [type(button) for button in buttons] == [InlineKeyboardButton, RichMessageButton]

    async def test_a_rich_button_in_another_chat_is_named(self, env, team, alice):
        await self.send(env, team, button_block("elsewhere"))

        with pytest.raises(WorldLookupError, match=f"exists in chat {team.id}"):
            await alice.click("elsewhere")

    async def test_a_deep_link_from_a_rich_button(self, env, private, alice):
        started = []
        env.dispatcher.message.register(lambda message: started.append(message.text))
        username = env.world.bot_user.username
        link = f"https://t.me/{username}?start=promo"
        sent = await self.send(env, private, button_block(None, url=link))

        await alice.follow_deep_link()
        (block,) = sent.rich_message.blocks
        await alice.follow_deep_link(block.buttons[0])

        assert started == ["/start promo", "/start promo"]

    async def test_a_rich_button_object_without_a_url_cannot_be_followed(self, env, alice):
        with pytest.raises(WorldLookupError, match="carries no url"):
            await alice.follow_deep_link(RichMessageButton(text="x", callback_data="y"))


class TestStoredTypes:
    def test_converted_blocks_are_the_stored_types(self):
        stored = materialize_rich_message(
            InputRichMessage(
                blocks=[
                    InputRichBlockDetails(
                        summary="s",
                        blocks=[InputRichBlockParagraph(text="p")],
                    ),
                ],
            ),
            SynthesisContext(),
        )

        (details,) = stored.blocks
        assert isinstance(details, RichBlockDetails)
        assert isinstance(details.blocks[0], RichBlockParagraph)


class TestConversionFallbacks:
    """Branches today's schema does not reach, kept for future types."""

    def test_an_unset_required_model_field_is_synthesized(self):
        location = rich._zero_value(Location, "location", SynthesisContext())

        assert isinstance(location, Location)

    def test_list_items_are_found_through_optional_and_plain_annotations(self):
        assert list_item(list[int] | None) is int
        assert list_item(list[str]) is str
        assert list_item(int) is None

    def test_a_list_with_no_list_annotation_keeps_its_entries(self):
        assert rich._convert_value(["a", "b"], str, "x", SynthesisContext()) == ["a", "b"]
