from typing import get_args

import pytest

from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import EditMessageMedia, SendChatAction
from aiogram.test import Blueprint, BotTestEnvironment
from aiogram.test.modeling import EDITABLE_MEDIA_FIELDS, media_field
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputChecklist,
    InputChecklistTask,
    InputMediaPhoto,
    InputMediaVideo,
    InputPaidMediaPhoto,
    LabeledPrice,
    Message,
)

INPUT_MEDIA_MEMBERS = get_args(EditMessageMedia.model_fields["media"].annotation)


class TestSentPayloadsCarryRequestValues:
    async def test_location_keeps_the_coordinates_it_was_sent_with(self, env, private):
        message = await env.bot.send_location(
            chat_id=private.id,
            latitude=48.85,
            longitude=2.29,
            live_period=600,
            heading=90,
        )

        assert message.location.latitude == 48.85
        assert message.location.longitude == 2.29
        assert message.location.live_period == 600
        assert message.location.heading == 90

    async def test_contact_keeps_its_details(self, env, private):
        message = await env.bot.send_contact(
            chat_id=private.id,
            phone_number="+10000000",
            first_name="Alice",
            last_name="Liddell",
        )

        assert message.contact.phone_number == "+10000000"
        assert message.contact.first_name == "Alice"
        assert message.contact.last_name == "Liddell"

    async def test_video_keeps_its_dimensions(self, env, private):
        message = await env.bot.send_video(
            chat_id=private.id,
            video="file-id",
            width=1920,
            height=1080,
            duration=42,
        )

        assert (message.video.width, message.video.height) == (1920, 1080)
        assert message.video.duration == 42

    async def test_paid_media_keeps_its_star_count(self, env, private):
        message = await env.bot.send_paid_media(
            chat_id=private.id,
            star_count=25,
            media=[InputPaidMediaPhoto(media="file-id")],
        )

        assert message.paid_media.star_count == 25

    async def test_a_same_named_field_of_a_different_type_is_left_alone(self, env, private):
        """``sendVideo.cover`` is a file id; ``Video.cover`` is a ``PhotoSize``."""
        message = await env.bot.send_video(chat_id=private.id, video="file-id", cover="cover-id")

        assert message.video.cover != "cover-id"

    async def test_a_payload_with_nothing_to_carry_is_untouched(self, env, private):
        message = await env.bot.send_document(chat_id=private.id, document="file-id")

        assert message.document is not None


class TestEditingMedia:
    async def test_editing_media_replaces_the_stored_content(self, env, private):
        original = await env.bot.send_photo(chat_id=private.id, photo="first")

        edited = await env.bot.edit_message_media(
            chat_id=private.id,
            message_id=original.message_id,
            media=InputMediaVideo(media="second", caption="a video now"),
        )

        assert edited.video is not None
        assert edited.photo is None
        assert edited.caption == "a video now"

    async def test_editing_media_does_not_add_a_message(self, env, private):
        original = await env.bot.send_photo(chat_id=private.id, photo="first")

        edited = await env.bot.edit_message_media(
            chat_id=private.id,
            message_id=original.message_id,
            media=InputMediaPhoto(media="second"),
        )

        assert private.messages == [edited]

    async def test_editing_media_keeps_the_reply_markup_when_omitted(self, env, private):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )
        original = await env.bot.send_photo(chat_id=private.id, photo="a", reply_markup=markup)

        edited = await env.bot.edit_message_media(
            chat_id=private.id,
            message_id=original.message_id,
            media=InputMediaPhoto(media="b"),
        )

        assert edited.reply_markup.model_dump() == markup.model_dump()

    @pytest.mark.parametrize(
        "member",
        INPUT_MEDIA_MEMBERS,
        ids=lambda item: item.__name__,
    )
    def test_every_input_media_member_maps_to_a_message_field(self, member):
        """Guard for design decision D2: the derived mapping must cover the whole union."""
        required = {
            name: "file-id" for name, field in member.model_fields.items() if field.is_required()
        }

        assert media_field(member(**required)) in EDITABLE_MEDIA_FIELDS

    def test_an_unmappable_input_media_is_a_loud_failure(self):
        class InputMediaHologram(InputMediaPhoto):
            pass

        with pytest.raises(Exception, match="does not map to a Message field"):
            media_field(InputMediaHologram(media="file-id"))


class TestEditingLiveLocation:
    async def test_editing_moves_the_stored_message(self, env, private):
        original = await env.bot.send_location(
            chat_id=private.id,
            latitude=1.0,
            longitude=2.0,
            live_period=600,
        )

        edited = await env.bot.edit_message_live_location(
            chat_id=private.id,
            message_id=original.message_id,
            latitude=9.5,
            longitude=8.5,
        )

        assert (edited.location.latitude, edited.location.longitude) == (9.5, 8.5)
        assert private.messages == [edited]

    async def test_omitting_live_period_keeps_the_location_live(self, env, private):
        original = await env.bot.send_location(
            chat_id=private.id,
            latitude=1.0,
            longitude=2.0,
            live_period=600,
        )

        edited = await env.bot.edit_message_live_location(
            chat_id=private.id,
            message_id=original.message_id,
            latitude=3.0,
            longitude=4.0,
        )

        assert edited.location.live_period == 600

    async def test_stopping_returns_the_stored_message_with_the_period_cleared(
        self,
        env,
        private,
    ):
        original = await env.bot.send_location(
            chat_id=private.id,
            latitude=1.0,
            longitude=2.0,
            live_period=600,
        )

        stopped = await env.bot.stop_message_live_location(
            chat_id=private.id,
            message_id=original.message_id,
        )

        assert isinstance(stopped, Message)
        assert stopped.message_id == original.message_id
        assert stopped.location.live_period is None

    async def test_stopping_a_message_without_a_location(self, env, private):
        original = await env.bot.send_message(chat_id=private.id, text="hi")

        stopped = await env.bot.stop_message_live_location(
            chat_id=private.id,
            message_id=original.message_id,
        )

        assert stopped.message_id == original.message_id
        assert stopped.location is None


class TestEditingChecklist:
    async def test_editing_replaces_the_stored_checklist(self, env, private, connection):
        original = await env.bot.send_checklist(
            business_connection_id=connection.id,
            chat_id=private.id,
            checklist=InputChecklist(
                title="Groceries",
                tasks=[InputChecklistTask(id=1, text="Milk")],
            ),
        )

        edited = await env.bot.edit_message_checklist(
            business_connection_id=connection.id,
            chat_id=private.id,
            message_id=original.message_id,
            checklist=InputChecklist(
                title="Groceries",
                tasks=[InputChecklistTask(id=1, text="Oat milk")],
            ),
        )

        assert edited.checklist is not None
        assert private.messages == [edited]


class TestEditingUnknownTargets:
    @pytest.mark.parametrize(
        "call",
        [
            pytest.param(
                lambda bot, chat_id, message_id: bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=message_id,
                    media=InputMediaPhoto(media="x"),
                ),
                id="edit_message_media",
            ),
            pytest.param(
                lambda bot, chat_id, message_id: bot.edit_message_live_location(
                    chat_id=chat_id,
                    message_id=message_id,
                    latitude=1.0,
                    longitude=2.0,
                ),
                id="edit_message_live_location",
            ),
            pytest.param(
                lambda bot, chat_id, message_id: bot.stop_message_live_location(
                    chat_id=chat_id,
                    message_id=message_id,
                ),
                id="stop_message_live_location",
            ),
        ],
    )
    async def test_editing_a_deleted_message_fails(self, env, private, call):
        original = await env.bot.send_photo(chat_id=private.id, photo="a")
        await env.bot.delete_message(chat_id=private.id, message_id=original.message_id)

        with pytest.raises(TelegramBadRequest, match="message to edit not found"):
            await call(env.bot, private.id, original.message_id)

    async def test_editing_a_checklist_on_a_deleted_message_fails(
        self,
        env,
        private,
        connection,
    ):
        original = await env.bot.send_message(chat_id=private.id, text="hi")
        await env.bot.delete_message(chat_id=private.id, message_id=original.message_id)

        with pytest.raises(TelegramBadRequest, match="message to edit not found"):
            await env.bot.edit_message_checklist(
                business_connection_id=connection.id,
                chat_id=private.id,
                message_id=original.message_id,
                checklist=InputChecklist(
                    title="t",
                    tasks=[InputChecklistTask(id=1, text="x")],
                ),
            )

    async def test_inline_message_targets_fail_loudly(self, env):
        """Inline messages have no chat to live in, so the fake says so rather than guessing."""
        with pytest.raises(TelegramBadRequest, match="inline messages are not modeled"):
            await env.bot.edit_message_media(
                inline_message_id="inline-1",
                media=InputMediaPhoto(media="x"),
            )


class TestBatchForwardAndCopy:
    async def test_forwarding_a_batch(self, env, private, team, alice):
        for text in ("one", "two", "three"):
            await alice.send(text)
        source_ids = [message.message_id for message in private.messages]

        result = await env.bot.forward_messages(
            chat_id=team.id,
            from_chat_id=private.id,
            message_ids=source_ids,
        )

        assert [item.message_id for item in result] == [
            message.message_id for message in team.messages
        ]
        assert len(team.messages) == 3
        assert all(message.forward_origin is not None for message in team.messages)

    async def test_copying_a_batch_omits_the_origin(self, env, private, team, alice):
        for text in ("one", "two"):
            await alice.send(text)
        source_ids = [message.message_id for message in private.messages]

        result = await env.bot.copy_messages(
            chat_id=team.id,
            from_chat_id=private.id,
            message_ids=source_ids,
        )

        assert len(result) == 2
        assert all(message.forward_origin is None for message in team.messages)

    async def test_a_single_forward_also_carries_the_origin(self, env, private, team, alice):
        await alice.send("original")
        original = private.messages[-1]

        forwarded = await env.bot.forward_message(
            chat_id=team.id,
            from_chat_id=private.id,
            message_id=original.message_id,
        )

        assert forwarded.forward_origin.sender_user.id == alice.user.id

    async def test_missing_ids_are_skipped_rather_than_failing_the_batch(
        self,
        env,
        private,
        team,
        alice,
    ):
        await alice.send("only one")
        existing = private.messages[-1].message_id

        result = await env.bot.forward_messages(
            chat_id=team.id,
            from_chat_id=private.id,
            message_ids=[existing, 998, 999],
        )

        assert len(result) == 1

    @pytest.mark.parametrize("method_name", ["forward_messages", "copy_messages"])
    async def test_an_unknown_source_chat_fails(self, env, team, method_name):
        with pytest.raises(TelegramBadRequest, match="chat not found"):
            await getattr(env.bot, method_name)(
                chat_id=team.id,
                from_chat_id=-99,
                message_ids=[1],
            )


class TestADerivedMessageIsAFreshObject:
    """
    A forward, a copy and an edit all derive one message from another.

    ``model_copy`` carries the original's binding over, which makes ``mount`` prune the
    derived message at its root and leave everything the derivation brought along — a new
    chat, a new sender, a forward origin — unbound. The damaged message is then *stored*,
    so a bot reading it back out of the chat gets shortcuts that raise, long after the call
    that made it. All three go through one derive primitive, and this asserts it.
    """

    async def test_a_forward_binds_what_it_brought_with_it(self, env, private, team, alice):
        await alice.send("original")

        forwarded = await env.bot.forward_message(
            chat_id=team.id,
            from_chat_id=private.id,
            message_id=private.messages[-1].message_id,
        )

        assert forwarded.bot is env.bot
        assert forwarded.chat.bot is env.bot
        assert forwarded.forward_origin.bot is env.bot
        # A shortcut on the new chat is what a bot actually reaches for next.
        assert await forwarded.chat.get_member(alice.user.id)

    async def test_the_stored_forward_is_the_damaged_one_if_anything_is(
        self,
        env,
        private,
        team,
        alice,
    ):
        """The result may look fine while the message the world keeps does not."""
        await alice.send("original")

        await env.bot.forward_message(
            chat_id=team.id,
            from_chat_id=private.id,
            message_id=private.messages[-1].message_id,
        )

        stored = team.messages[-1]
        assert stored.chat.bot is env.bot
        assert stored.chat.id == team.id

    async def test_a_copy_binds_what_it_brought_with_it(self, env, private, team, alice):
        await alice.send("original")

        await env.bot.copy_message(
            chat_id=team.id,
            from_chat_id=private.id,
            message_id=private.messages[-1].message_id,
        )

        stored = team.messages[-1]
        assert stored.chat.bot is env.bot
        assert stored.from_user.bot is env.bot

    async def test_the_original_is_left_alone(self, env, private, team, alice):
        await alice.send("original")
        original = private.messages[-1]

        await env.bot.forward_message(
            chat_id=team.id,
            from_chat_id=private.id,
            message_id=original.message_id,
        )

        assert private.messages[-1] is original
        assert original.chat.id == private.id
        assert original.forward_origin is None


class TestUnpinningEverything:
    async def test_unpin_all_clears_the_pinned_list(self, env, private, alice):
        for text in ("one", "two"):
            await alice.send(text)
        for message in private.messages:
            await env.bot.pin_chat_message(chat_id=private.id, message_id=message.message_id)
        assert len(private.pinned_message_ids) == 2

        await env.bot.unpin_all_chat_messages(chat_id=private.id)

        assert private.pinned_message_ids == []

    async def test_unpin_all_on_an_unknown_chat_fails(self, env):
        with pytest.raises(TelegramBadRequest, match="chat not found"):
            await env.bot.unpin_all_chat_messages(chat_id=-99)


class TestSeededAnswers:
    async def test_chat_action_against_a_known_chat(self, env, private):
        assert await env.bot.send_chat_action(chat_id=private.id, action="typing") is True
        assert env.calls.last(SendChatAction).action == "typing"

    async def test_chat_action_against_an_unknown_chat_fails(self, env):
        with pytest.raises(TelegramBadRequest, match="chat not found"):
            await env.bot.send_chat_action(chat_id=-99, action="typing")

    async def test_get_file_echoes_the_requested_id(self, env, private):
        message = await env.bot.send_document(chat_id=private.id, document="file-id")

        result = await env.bot.get_file(file_id=message.document.file_id)

        assert result.file_id == message.document.file_id

    async def test_invoice_links_are_unique(self, env):
        first = await env.bot.create_invoice_link(
            title="Sub",
            description="A subscription",
            payload="sub-1",
            currency="XTR",
            prices=[LabeledPrice(label="Month", amount=100)],
        )
        second = await env.bot.create_invoice_link(
            title="Sub",
            description="A subscription",
            payload="sub-2",
            currency="XTR",
            prices=[LabeledPrice(label="Month", amount=100)],
        )

        assert first != second
        assert first.startswith("https://t.me/")

    async def test_personal_chat_messages_come_from_the_users_private_chat(
        self,
        env,
        private,
        alice,
    ):
        for text in ("one", "two", "three"):
            await alice.send(text)

        result = await env.bot.get_user_personal_chat_messages(user_id=alice.user.id, limit=2)

        assert [message.text for message in result] == ["two", "three"]

    async def test_personal_chat_messages_for_an_unknown_user_fails(self, env):
        with pytest.raises(TelegramBadRequest, match="user has no personal chat"):
            await env.bot.get_user_personal_chat_messages(user_id=424242, limit=5)


class TestForwardingFromAChannel:
    async def test_a_channel_forward_carries_a_channel_origin(self, dp):
        blueprint = Blueprint()
        channel = blueprint.add_channel("News")
        group = blueprint.add_supergroup("Team")
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            post = await env.bot.send_message(chat_id=channel.id, text="headline")

            forwarded = await env.bot.forward_message(
                chat_id=group.id,
                from_chat_id=channel.id,
                message_id=post.message_id,
            )

            assert forwarded.forward_origin.type == "channel"
            assert forwarded.forward_origin.chat.id == channel.id
            assert forwarded.forward_origin.message_id == post.message_id
        finally:
            env.dispose_sync()


class TestEditingMediaWithMarkup:
    async def test_a_new_reply_markup_replaces_the_old_one(self, env, private):
        original = await env.bot.send_photo(
            chat_id=private.id,
            photo="a",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Old", callback_data="old")]],
            ),
        )
        replacement = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="New", callback_data="new")]],
        )

        edited = await env.bot.edit_message_media(
            chat_id=private.id,
            message_id=original.message_id,
            media=InputMediaPhoto(media="b"),
            reply_markup=replacement,
        )

        assert edited.reply_markup.model_dump() == replacement.model_dump()
