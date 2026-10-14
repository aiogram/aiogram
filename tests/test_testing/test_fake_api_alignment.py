"""
Regression tests for the places the fake Bot API disagreed with the
Bot API: each test reproduces one finding of the audit that led to the
`align-fake-api-with-bot-api` change.
"""

import copy
import io

import pytest

from aiogram.enums import ChatMemberStatus, ChatType, DiceEmoji, StickerType
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import GetUserProfilePhotos
from aiogram.test import Blueprint, BotTestEnvironment, WorldLookupError
from aiogram.test.synthesis import SynthesisContext, annotation_accepts, synthesize
from aiogram.test.world import World
from aiogram.types import (
    BufferedInputFile,
    Chat,
    ChatPermissions,
    EphemeralMessageParameters,
    Giveaway,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputChecklist,
    InputChecklistTask,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaVoiceNote,
    InputRichBlockPhoto,
    InputRichBlockVoiceNote,
    InputRichMessage,
    LabeledPrice,
    MessageEntity,
    MessageOriginUser,
    PaidMediaInfo,
    Poll,
    PollOption,
    ReplyParameters,
    RichTextBold,
    Sticker,
    Story,
    TextQuote,
    TransactionPartnerUser,
    User,
)
from aiogram.types.rich_text_union import RichTextUnion

KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="K", callback_data="k")]],
)


@pytest.fixture
def blueprint():
    blueprint = Blueprint()
    alice = blueprint.add_user("Alice")
    bob = blueprint.add_user("Bob")
    blueprint.add_private_chat(alice)
    blueprint.add_private_chat(bob)
    team = blueprint.add_supergroup(
        "Team",
        members={alice: ChatMemberStatus.MEMBER, bob: ChatMemberStatus.MEMBER},
    )
    forum = blueprint.add_supergroup("Forum", members={alice: ChatMemberStatus.MEMBER})
    blueprint.add_topic(forum, "Support")
    blueprint.add_business_connection(alice)
    blueprint.set_member(team, blueprint.bot, status=ChatMemberStatus.ADMINISTRATOR)
    return blueprint


@pytest.fixture
def alice(blueprint):
    return blueprint.users[0]


@pytest.fixture
def bob(blueprint):
    return blueprint.users[1]


@pytest.fixture
def private(env, blueprint):
    return env.chat(blueprint.chats[0])


@pytest.fixture
def bobs(env, blueprint):
    return env.chat(blueprint.chats[1])


@pytest.fixture
def team(env, blueprint):
    return env.chat(blueprint.chats[2])


@pytest.fixture
def forum(env, blueprint):
    return env.chat(blueprint.chats[3])


@pytest.fixture
def topic(blueprint):
    return blueprint.topics[0]


@pytest.fixture
def connection(blueprint):
    return blueprint.business_connections[0]


class TestMediaGroups:
    async def test_an_album_keeps_each_items_media_and_caption(self, env, private):
        bold = MessageEntity(type="bold", offset=0, length=3)
        messages = await env.bot.send_media_group(
            chat_id=private.id,
            media=[
                InputMediaPhoto(media="first", caption="One", caption_entities=[bold]),
                InputMediaPhoto(media="second", caption="Two", has_spoiler=True),
            ],
        )

        assert private.messages == messages
        assert [message.photo[-1].file_id for message in messages] == ["first", "second"]
        assert [message.caption for message in messages] == ["One", "Two"]
        assert messages[0].caption_entities[0].model_dump() == bold.model_dump()
        assert messages[1].has_media_spoiler is True
        assert messages[0].media_group_id is not None
        assert messages[0].media_group_id == messages[1].media_group_id

    async def test_a_document_is_grouped_only_with_documents(self, env, private):
        with pytest.raises(TelegramBadRequest, match="same type"):
            await env.bot.send_media_group(
                chat_id=private.id,
                media=[InputMediaPhoto(media="photo"), InputMediaDocument(media="document")],
            )

        assert private.messages == []

    async def test_a_single_photo_keeps_its_spoiler_and_caption_placement(self, env, private):
        """A single send stores the flags an album item stores."""
        message = await env.bot.send_photo(
            chat_id=private.id,
            photo="photo",
            caption="c",
            has_spoiler=True,
            show_caption_above_media=True,
        )

        assert message.has_media_spoiler is True
        assert message.show_caption_above_media is True

    async def test_new_media_brings_its_own_flags(self, env, private):
        """Editing the media replaces the spoiler and caption placement too."""
        sent = await env.bot.send_photo(
            chat_id=private.id,
            photo="photo",
            caption="c",
            has_spoiler=True,
            show_caption_above_media=True,
        )

        edited = await env.bot.edit_message_media(
            chat_id=private.id,
            message_id=sent.message_id,
            media=InputMediaPhoto(media="other", caption="d"),
        )

        assert edited.has_media_spoiler is None
        assert edited.show_caption_above_media is None

    @pytest.mark.parametrize("size", [1, 11])
    async def test_an_album_of_the_wrong_size_is_refused(self, env, private, size):
        with pytest.raises(TelegramBadRequest, match="2-10 items"):
            await env.bot.send_media_group(
                chat_id=private.id,
                media=[InputMediaPhoto(media=f"p{index}") for index in range(size)],
            )

        assert private.messages == []

    async def test_a_refused_album_registers_no_file(self, env, private):
        with pytest.raises(TelegramBadRequest, match="message to be replied not found"):
            await env.bot.send_media_group(
                chat_id=private.id,
                media=[
                    InputMediaPhoto(media=BufferedInputFile(b"a", filename="a.jpg")),
                    InputMediaPhoto(media=BufferedInputFile(b"b", filename="b.jpg")),
                ],
                reply_parameters=ReplyParameters(message_id=999),
            )

        assert env.world.files == {}
        assert env.world.last_file_number == 0


class TestStoredContent:
    async def test_a_venue_is_where_the_request_put_it(self, env, private):
        message = await env.bot.send_venue(
            chat_id=private.id,
            latitude=55.75,
            longitude=37.62,
            title="Square",
            address="Centre",
        )

        assert (message.venue.location.latitude, message.venue.location.longitude) == (
            55.75,
            37.62,
        )

    async def test_an_invoice_totals_its_prices(self, env, private):
        message = await env.bot.send_invoice(
            chat_id=private.id,
            title="Pack",
            description="Two items",
            payload="pack",
            currency="XTR",
            prices=[LabeledPrice(label="a", amount=30), LabeledPrice(label="b", amount=20)],
        )

        assert message.invoice.total_amount == 50


class TestReplies:
    async def test_a_reply_to_a_missing_message_fails(self, env, private):
        with pytest.raises(TelegramBadRequest, match="message to be replied not found"):
            await env.bot.send_message(
                chat_id=private.id,
                text="answer",
                reply_parameters=ReplyParameters(message_id=999),
            )

        assert private.messages == []

    async def test_sending_without_the_reply_is_allowed_when_asked(self, env, private):
        message = await env.bot.send_message(
            chat_id=private.id,
            text="answer",
            reply_parameters=ReplyParameters(message_id=999, allow_sending_without_reply=True),
        )

        assert message.reply_to_message is None

    async def test_a_reply_in_another_chat_is_looked_up_there(self, env, private, bobs):
        target = await env.bot.send_message(chat_id=bobs.id, text="Bob's")
        await env.bot.send_message(chat_id=private.id, text="filler")

        message = await env.bot.send_message(
            chat_id=private.id,
            text="answer",
            reply_parameters=ReplyParameters(message_id=target.message_id, chat_id=bobs.id),
        )

        assert message.reply_to_message is None
        reply = message.external_reply
        assert reply.origin.sender_user.id == env.bot.id
        # A private chat is not named, as ExternalReplyInfo documents.
        assert (reply.chat, reply.message_id) == (None, None)

    async def test_a_reply_to_a_supergroup_names_the_message(self, env, alice, private, team):
        await env.user(alice).in_(team).send("question")
        target = team.messages[-1]

        message = await env.bot.send_message(
            chat_id=private.id,
            text="answer",
            reply_parameters=ReplyParameters(message_id=target.message_id, chat_id=team.id),
        )

        reply = message.external_reply
        assert reply.origin.sender_user.id == alice.id
        assert (reply.chat.id, reply.message_id) == (team.id, target.message_id)
        assert private.find_message(message.message_id).external_reply == reply

    async def test_a_missing_reply_in_another_chat_always_fails(self, env, private, bobs):
        with pytest.raises(TelegramBadRequest, match="message to be replied not found"):
            await env.bot.send_message(
                chat_id=private.id,
                text="answer",
                reply_parameters=ReplyParameters(
                    message_id=999,
                    chat_id=bobs.id,
                    allow_sending_without_reply=True,
                ),
            )

    async def test_a_missing_reply_in_a_topic_always_fails(self, env, forum, topic):
        with pytest.raises(TelegramBadRequest, match="message to be replied not found"):
            await env.bot.send_message(
                chat_id=forum.id,
                message_thread_id=topic.message_thread_id,
                text="answer",
                reply_parameters=ReplyParameters(message_id=999, allow_sending_without_reply=True),
            )

    async def test_a_missing_reply_in_an_ephemeral_message_always_fails(self, env, team, alice):
        with pytest.raises(TelegramBadRequest, match="message to be replied not found"):
            await env.bot.send_message(
                chat_id=team.id,
                text="answer",
                ephemeral_message_parameters=EphemeralMessageParameters(
                    receiver_user_id=alice.id,
                ),
                reply_parameters=ReplyParameters(message_id=999, allow_sending_without_reply=True),
            )

    async def test_a_missing_reply_on_behalf_of_a_business_is_dropped(
        self,
        env,
        private,
        connection,
    ):
        message = await env.bot.send_message(
            business_connection_id=connection.id,
            chat_id=private.id,
            text="answer",
            reply_parameters=ReplyParameters(message_id=999),
        )

        assert message.reply_to_message is None

    async def test_an_ephemeral_message_cannot_reply_in_another_chat(
        self,
        env,
        team,
        private,
        alice,
    ):
        target = await env.bot.send_message(chat_id=private.id, text="elsewhere")

        with pytest.raises(TelegramBadRequest, match="another chat is not supported"):
            await env.bot.send_message(
                chat_id=team.id,
                text="answer",
                ephemeral_message_parameters=EphemeralMessageParameters(
                    receiver_user_id=alice.id,
                ),
                reply_parameters=ReplyParameters(message_id=target.message_id, chat_id=private.id),
            )

        assert team.ephemeral_messages(alice) == []

    async def test_a_business_message_cannot_reply_in_another_chat(
        self,
        env,
        private,
        bobs,
        connection,
    ):
        target = await env.bot.send_message(chat_id=bobs.id, text="elsewhere")

        with pytest.raises(TelegramBadRequest, match="another chat is not supported"):
            await env.bot.send_message(
                business_connection_id=connection.id,
                chat_id=private.id,
                text="answer",
                reply_parameters=ReplyParameters(message_id=target.message_id, chat_id=bobs.id),
            )

    async def test_the_deprecated_reply_id_still_replies(self, env, private):
        target = await env.bot.send_message(chat_id=private.id, text="question")

        message = await env.bot.send_message(
            chat_id=private.id,
            text="answer",
            reply_to_message_id=target.message_id,
        )

        assert message.reply_to_message == target

    async def test_the_deprecated_reply_id_to_a_missing_message_fails(self, env, private):
        with pytest.raises(TelegramBadRequest, match="message to be replied not found"):
            await env.bot.send_message(chat_id=private.id, text="answer", reply_to_message_id=999)

        message = await env.bot.send_message(
            chat_id=private.id,
            text="answer",
            reply_to_message_id=999,
            allow_sending_without_reply=True,
        )
        assert message.reply_to_message is None


class TestCopiesAndForwards:
    async def test_a_quiz_with_an_unknown_answer_cannot_be_copied(self, env, alice, team, bobs):
        quiz = Poll(
            id="users-quiz",
            question="2 + 2?",
            options=[
                PollOption(persistent_id="0", text="4", voter_count=0),
                PollOption(persistent_id="1", text="5", voter_count=0),
            ],
            total_voter_count=0,
            is_closed=False,
            is_anonymous=True,
            type="quiz",
            allows_multiple_answers=False,
            allows_revoting=False,
            members_only=False,
        )
        await env.user(alice).in_(team).send(fields={"poll": quiz})
        users = team.messages[-1]

        with pytest.raises(TelegramBadRequest, match="can't be copied"):
            await env.bot.copy_message(
                chat_id=bobs.id,
                from_chat_id=team.id,
                message_id=users.message_id,
            )
        assert (
            await env.bot.copy_messages(
                chat_id=bobs.id,
                from_chat_id=team.id,
                message_ids=[users.message_id],
            )
            == []
        )

    async def test_a_quiz_the_bot_sent_can_be_copied(self, env, team, bobs):
        sent = await env.bot.send_poll(
            chat_id=team.id,
            question="2 + 2?",
            options=["4", "5"],
            type="quiz",
            correct_option_ids=[0],
        )

        copied = await env.bot.copy_message(
            chat_id=bobs.id,
            from_chat_id=team.id,
            message_id=sent.message_id,
        )

        assert bobs.find_message(copied.message_id).poll.correct_option_ids == [0]

    async def test_a_single_copy_or_forward_of_an_album_item_stands_alone(
        self,
        env,
        private,
        bobs,
    ):
        album = await env.bot.send_media_group(
            chat_id=private.id,
            media=[InputMediaPhoto(media="one"), InputMediaPhoto(media="two")],
        )

        copied = await env.bot.copy_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=album[0].message_id,
        )
        forwarded = await env.bot.forward_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=album[1].message_id,
        )

        assert bobs.find_message(copied.message_id).media_group_id is None
        assert bobs.find_message(forwarded.message_id).media_group_id is None

    @pytest.mark.parametrize("method", ["copy_messages", "forward_messages"])
    async def test_a_batch_keeps_an_album_together_under_a_new_id(
        self,
        env,
        private,
        bobs,
        method,
    ):
        album = await env.bot.send_media_group(
            chat_id=private.id,
            media=[InputMediaPhoto(media="one"), InputMediaPhoto(media="two")],
        )
        alone = await env.bot.send_message(chat_id=private.id, text="alone")

        sent = await getattr(env.bot, method)(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_ids=[*(message.message_id for message in album), alone.message_id],
        )

        groups = [bobs.find_message(item.message_id).media_group_id for item in sent]
        assert groups[0] is not None
        assert groups[0] == groups[1]
        assert groups[0] != album[0].media_group_id
        assert groups[2] is None

    async def test_a_copy_into_a_topic_lands_in_it(self, env, forum, topic, private):
        source = await env.bot.send_message(chat_id=private.id, text="hi")

        copied = await env.bot.copy_message(
            chat_id=forum.id,
            from_chat_id=private.id,
            message_id=source.message_id,
            message_thread_id=topic.message_thread_id,
        )

        stored = forum.find_message(copied.message_id)
        assert stored.message_thread_id == topic.message_thread_id
        assert stored.is_topic_message is True

    async def test_a_copy_out_of_a_topic_carries_no_thread(self, env, forum, topic, private):
        source = await env.bot.send_message(
            chat_id=forum.id,
            message_thread_id=topic.message_thread_id,
            text="hi",
        )

        copied = await env.bot.copy_message(
            chat_id=private.id,
            from_chat_id=forum.id,
            message_id=source.message_id,
            message_thread_id=topic.message_thread_id,
        )

        stored = private.find_message(copied.message_id)
        assert stored.message_thread_id is None
        assert stored.is_topic_message is None

    async def test_a_forward_into_a_topic_lands_in_it(self, env, forum, topic, private):
        source = await env.bot.send_message(chat_id=private.id, text="hi")

        forwarded = await env.bot.forward_message(
            chat_id=forum.id,
            from_chat_id=private.id,
            message_id=source.message_id,
            message_thread_id=topic.message_thread_id,
        )

        assert forwarded.message_thread_id == topic.message_thread_id

    async def test_a_channel_post_moved_by_the_bot_is_not_posted_as_the_channel(self, dp):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        private_spec = blueprint.add_private_chat(alice)
        news = blueprint.add_channel("News", members={alice: ChatMemberStatus.CREATOR})
        environment = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            channel = environment.chat(news)
            target = environment.chat(private_spec)
            await environment.user(alice).in_(news).send("post")
            post = channel.messages[-1]

            forwarded = await environment.bot.forward_message(
                chat_id=target.id,
                from_chat_id=channel.id,
                message_id=post.message_id,
            )
            copied = await environment.bot.copy_message(
                chat_id=target.id,
                from_chat_id=channel.id,
                message_id=post.message_id,
            )

            assert forwarded.forward_origin.chat.id == channel.id
            for moved in (forwarded, target.find_message(copied.message_id)):
                assert moved.sender_chat is None
                assert moved.author_signature is None
        finally:
            environment.dispose_sync()

    async def test_a_new_caption_brings_its_own_entities(self, env, private, bobs):
        bold = MessageEntity(type="bold", offset=6, length=5)
        source = await env.bot.send_photo(
            chat_id=private.id,
            photo="photo",
            caption="hello world",
            caption_entities=[bold],
        )

        renamed = await env.bot.copy_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=source.message_id,
            caption="hi",
        )
        kept = await env.bot.copy_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=source.message_id,
        )

        assert bobs.find_message(renamed.message_id).caption == "hi"
        assert bobs.find_message(renamed.message_id).caption_entities is None
        assert bobs.find_message(kept.message_id).caption == "hello world"
        assert (
            bobs.find_message(kept.message_id).caption_entities[0].model_dump()
            == bold.model_dump()
        )

    async def test_a_copy_without_media_takes_no_caption(self, env, private, bobs):
        source = await env.bot.send_message(chat_id=private.id, text="hello")

        copied = await env.bot.copy_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=source.message_id,
            caption="ignored",
        )

        stored = bobs.find_message(copied.message_id)
        assert stored.text == "hello"
        assert stored.caption is None

    async def test_a_copy_stores_the_requests_keyboard(self, env, private, bobs):
        source = await env.bot.send_message(chat_id=private.id, text="hi")

        copied = await env.bot.copy_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=source.message_id,
            reply_markup=KEYBOARD,
        )

        assert (
            bobs.find_message(copied.message_id).reply_markup.model_dump() == KEYBOARD.model_dump()
        )

    async def test_copies_can_drop_their_captions(self, env, private, bobs):
        source = await env.bot.send_photo(chat_id=private.id, photo="photo", caption="hi")

        copied = await env.bot.copy_messages(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_ids=[source.message_id],
            remove_caption=True,
        )

        assert bobs.find_message(copied[0].message_id).caption is None

    async def test_a_protected_message_cannot_be_forwarded(self, env, private, bobs):
        source = await env.bot.send_message(chat_id=private.id, text="hi", protect_content=True)

        with pytest.raises(TelegramBadRequest, match="can't be forwarded"):
            await env.bot.forward_message(
                chat_id=bobs.id,
                from_chat_id=private.id,
                message_id=source.message_id,
            )
        forwarded = await env.bot.forward_messages(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_ids=[source.message_id],
        )

        assert forwarded == []
        assert bobs.messages == []

    async def test_a_service_message_cannot_be_copied_or_forwarded(self, env, team, private):
        await env.bot.set_chat_title(chat_id=team.id, title="Renamed")
        service = team.messages[-1]
        text = await env.bot.send_message(chat_id=team.id, text="hi")

        with pytest.raises(TelegramBadRequest, match="can't be copied"):
            await env.bot.copy_message(
                chat_id=private.id,
                from_chat_id=team.id,
                message_id=service.message_id,
            )
        with pytest.raises(TelegramBadRequest, match="can't be forwarded"):
            await env.bot.forward_message(
                chat_id=private.id,
                from_chat_id=team.id,
                message_id=service.message_id,
            )
        copied = await env.bot.copy_messages(
            chat_id=private.id,
            from_chat_id=team.id,
            message_ids=[service.message_id, text.message_id],
        )

        assert len(copied) == 1
        assert private.find_message(copied[0].message_id).text == "hi"

    async def test_a_forwarded_story_can_be_forwarded_and_copied(self, env, alice, private, bobs):
        story = Story(chat=Chat(id=-100500, type=ChatType.CHANNEL), id=5)
        await env.user(alice).send(fields={"story": story})
        source = private.messages[-1]

        forwarded = await env.bot.forward_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=source.message_id,
        )
        copied = await env.bot.copy_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=source.message_id,
        )

        assert forwarded.story is not None
        assert bobs.find_message(copied.message_id).story is not None

    async def test_a_forward_of_a_forward_keeps_the_first_origin(self, env, alice, private, bobs):
        origin = MessageOriginUser(
            date=env.now,
            sender_user=User(id=-7, is_bot=False, first_name="Carol"),
        )
        await env.user(alice).send("passed on", fields={"forward_origin": origin})

        forwarded = await env.bot.forward_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=private.messages[-1].message_id,
        )

        assert forwarded.forward_origin.sender_user.first_name == "Carol"

    async def test_a_forwarded_channel_post_names_its_signature(self, dp):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        private_spec = blueprint.add_private_chat(alice)
        channel_spec = blueprint.add_channel(
            "News",
            members={alice: ChatMemberStatus.ADMINISTRATOR},
        )
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            channel = env.chat(channel_spec)
            await env.user(alice).in_(channel).send("post")
            post = channel.messages[-1]

            forwarded = await env.bot.forward_message(
                chat_id=private_spec.id,
                from_chat_id=channel.id,
                message_id=post.message_id,
            )
        finally:
            env.dispose_sync()

        assert forwarded.author_signature is None
        assert forwarded.forward_origin.author_signature == post.author_signature == "Alice"

    async def test_a_copy_leaves_the_originals_quote_and_guest_query(self, env, alice, team, bobs):
        quote = TextQuote(text="hi", position=0)
        await env.user(alice).in_(team).guest_message("question", fields={"quote": quote})
        source = team.messages[-1]
        assert source.guest_query_id is not None

        copied = await env.bot.copy_message(
            chat_id=bobs.id,
            from_chat_id=team.id,
            message_id=source.message_id,
        )

        stored = bobs.find_message(copied.message_id)
        assert stored.quote is None
        assert stored.guest_query_id is None

    async def test_an_empty_caption_removes_the_original(self, env, private, bobs):
        source = await env.bot.send_photo(chat_id=private.id, photo="photo", caption="hi")

        copied = await env.bot.copy_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=source.message_id,
            caption="",
        )

        assert bobs.find_message(copied.message_id).caption is None

    async def test_an_invoice_cannot_be_copied(self, env, private, bobs):
        invoice = await env.bot.send_invoice(
            chat_id=private.id,
            title="Stars",
            description="Some",
            payload="p",
            currency="XTR",
            prices=[LabeledPrice(label="Stars", amount=1)],
        )

        with pytest.raises(TelegramBadRequest, match="can't be copied"):
            await env.bot.copy_message(
                chat_id=bobs.id,
                from_chat_id=private.id,
                message_id=invoice.message_id,
            )

    async def test_a_copy_or_forward_is_a_new_message(self, env, private, bobs):
        first = await env.bot.send_message(chat_id=private.id, text="first")
        source = await env.bot.send_message(
            chat_id=private.id,
            text="second",
            reply_parameters=ReplyParameters(message_id=first.message_id),
            protect_content=True,
        )
        await env.bot.edit_message_text(
            chat_id=private.id, message_id=source.message_id, text="edited"
        )
        unprotected = private.find_message(source.message_id).model_copy(
            update={"has_protected_content": None},
        )
        private.replace_message(unprotected)

        copied = await env.bot.copy_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=source.message_id,
        )
        forwarded = await env.bot.forward_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=source.message_id,
            protect_content=True,
        )

        copy = bobs.find_message(copied.message_id)
        assert copy.reply_to_message is None
        assert copy.edit_date is None
        assert copy.has_protected_content is None
        assert forwarded.reply_to_message is None
        assert forwarded.has_protected_content is True

    async def test_a_copy_replies_in_its_own_chat(self, env, private, bobs):
        target = await env.bot.send_message(chat_id=bobs.id, text="target")
        source = await env.bot.send_message(chat_id=private.id, text="hi")

        copied = await env.bot.copy_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=source.message_id,
            reply_parameters=ReplyParameters(message_id=target.message_id),
        )

        assert bobs.find_message(copied.message_id).reply_to_message == target
        with pytest.raises(TelegramBadRequest, match="not found"):
            await env.bot.copy_message(
                chat_id=bobs.id,
                from_chat_id=private.id,
                message_id=source.message_id,
                reply_parameters=ReplyParameters(message_id=999),
            )


class TestUnpinning:
    async def test_unpinning_without_an_id_unpins_the_newest_pin(self, env, private):
        first = await env.bot.send_message(chat_id=private.id, text="one")
        second = await env.bot.send_message(chat_id=private.id, text="two")
        await env.bot.pin_chat_message(chat_id=private.id, message_id=second.message_id)
        await env.bot.pin_chat_message(chat_id=private.id, message_id=first.message_id)

        await env.bot.unpin_chat_message(chat_id=private.id)

        assert private.pinned_message_ids == [first.message_id]

    async def test_unpinning_with_nothing_pinned_does_nothing(self, env, private):
        assert await env.bot.unpin_chat_message(chat_id=private.id) is True
        assert private.pinned_message_ids == []


class TestEditsActOnTheirContent:
    async def test_the_bot_cannot_edit_a_users_message(self, env, alice, team):
        await env.user(alice).in_(team).send("mine")
        users = team.messages[-1]

        with pytest.raises(TelegramBadRequest, match="can't be edited"):
            await env.bot.edit_message_text(
                chat_id=team.id,
                message_id=users.message_id,
                text="not yours",
            )

        assert team.messages[-1].text == "mine"

    async def test_editing_text_on_a_photo_fails(self, env, private):
        photo = await env.bot.send_photo(chat_id=private.id, photo="photo", caption="c")

        with pytest.raises(TelegramBadRequest, match="no text in the message"):
            await env.bot.edit_message_text(
                chat_id=private.id,
                message_id=photo.message_id,
                text="now text",
            )

        assert private.messages == [photo]
        assert private.messages[0].text is None

    async def test_editing_a_caption_on_a_text_message_fails(self, env, private):
        text = await env.bot.send_message(chat_id=private.id, text="t")

        with pytest.raises(TelegramBadRequest, match="no caption in the message"):
            await env.bot.edit_message_caption(
                chat_id=private.id,
                message_id=text.message_id,
                caption="c",
            )

    async def test_editing_media_on_a_sticker_fails(self, env, private):
        sticker = await env.bot.send_sticker(chat_id=private.id, sticker="sticker")

        with pytest.raises(TelegramBadRequest, match="no media in the message"):
            await env.bot.edit_message_media(
                chat_id=private.id,
                message_id=sticker.message_id,
                media=InputMediaPhoto(media="photo"),
            )

        assert private.messages[0].sticker is not None

    async def test_a_text_message_can_take_media(self, env, private):
        text = await env.bot.send_message(chat_id=private.id, text="t")

        edited = await env.bot.edit_message_media(
            chat_id=private.id,
            message_id=text.message_id,
            media=InputMediaPhoto(media="photo"),
        )

        assert (edited.text, edited.photo[-1].file_id) == (None, "photo")

    async def test_an_album_item_keeps_its_albums_kind(self, env, private):
        album = await env.bot.send_media_group(
            chat_id=private.id,
            media=[InputMediaPhoto(media="one"), InputMediaPhoto(media="two")],
        )

        with pytest.raises(TelegramBadRequest, match="album item"):
            await env.bot.edit_message_media(
                chat_id=private.id,
                message_id=album[0].message_id,
                media=InputMediaDocument(media="document"),
            )
        edited = await env.bot.edit_message_media(
            chat_id=private.id,
            message_id=album[0].message_id,
            media=InputMediaVideo(media="video"),
        )

        assert edited.video is not None

    async def test_ephemeral_edits_act_on_their_content(self, env, team, alice):
        to_alice = EphemeralMessageParameters(receiver_user_id=alice.id)
        photo = await env.bot.send_photo(
            chat_id=team.id,
            photo="photo",
            ephemeral_message_parameters=to_alice,
        )
        text = await env.bot.send_message(
            chat_id=team.id,
            text="t",
            ephemeral_message_parameters=to_alice,
        )

        with pytest.raises(TelegramBadRequest, match="no text in the message"):
            await env.bot.edit_ephemeral_message_text(
                chat_id=team.id,
                receiver_user_id=alice.id,
                ephemeral_message_id=photo.ephemeral_message_id,
                text="now text",
            )
        with pytest.raises(TelegramBadRequest, match="no caption in the message"):
            await env.bot.edit_ephemeral_message_caption(
                chat_id=team.id,
                receiver_user_id=alice.id,
                ephemeral_message_id=text.ephemeral_message_id,
                caption="c",
            )

    async def test_a_caption_edit_sets_where_the_caption_shows(self, env, private):
        photo = await env.bot.send_photo(chat_id=private.id, photo="photo", caption="c")

        edited = await env.bot.edit_message_caption(
            chat_id=private.id,
            message_id=photo.message_id,
            caption="above",
            show_caption_above_media=True,
        )

        assert edited.show_caption_above_media is True
        assert private.find_message(photo.message_id).show_caption_above_media is True


class TestEditableByTheBot:
    async def test_the_bot_edits_a_channel_post_it_did_not_send(self, dp):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        news = blueprint.add_channel(
            "News",
            members={alice: ChatMemberStatus.CREATOR},
            bot_status=ChatMemberStatus.ADMINISTRATOR,
        )
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            await env.user(alice).in_(news).send("draft")
            post = env.chat(news).messages[-1]

            edited = await env.bot.edit_message_text(
                chat_id=news.id, message_id=post.message_id, text="final"
            )

            assert edited.text == "final"
        finally:
            await env.dispose()


class TestEditDates:
    async def test_every_bot_edit_is_dated(self, env, private):
        sent = await env.bot.send_message(chat_id=private.id, text="hi")
        assert sent.edit_date is None
        now = int(env.now.timestamp())

        edited = await env.bot.edit_message_text(
            chat_id=private.id, message_id=sent.message_id, text="hello"
        )
        marked = await env.bot.edit_message_reply_markup(
            chat_id=private.id,
            message_id=sent.message_id,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="ok", callback_data="ok")]],
            ),
        )

        assert edited.edit_date == now
        assert marked.edit_date == now
        assert private.find_message(sent.message_id).edit_date == now


class TestPolls:
    async def test_a_copied_poll_is_a_poll_of_its_own(self, env, private, bobs):
        original = await env.bot.send_poll(chat_id=private.id, question="Q?", options=["a", "b"])
        copied = await env.bot.copy_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=original.message_id,
        )

        stopped = await env.bot.stop_poll(chat_id=bobs.id, message_id=copied.message_id)

        assert stopped.is_closed is True
        assert stopped.id != original.poll.id
        assert env.world.poll(original.poll.id).is_closed is False
        also_stopped = await env.bot.stop_poll(chat_id=private.id, message_id=original.message_id)
        assert also_stopped.is_closed is True

    async def test_a_copied_poll_the_world_never_stored_is_kept(self, env, alice, private, bobs):
        poll = synthesize(Poll, SynthesisContext())
        await env.user(alice).send(fields={"poll": poll})
        sent = private.messages[-1]

        copied = await env.bot.copy_message(
            chat_id=bobs.id,
            from_chat_id=private.id,
            message_id=sent.message_id,
        )

        stored = bobs.find_message(copied.message_id).poll
        assert (stored.id, stored.question) == (poll.id, poll.question)

    async def test_a_refused_poll_is_not_registered(self, env, private):
        with pytest.raises(TelegramBadRequest, match="message to be replied not found"):
            await env.bot.send_poll(
                chat_id=private.id,
                question="Q?",
                options=["a", "b"],
                reply_parameters=ReplyParameters(message_id=999),
            )

        assert env.world.polls == {}

    async def test_a_quiz_keeps_its_correct_answers(self, env, private):
        message = await env.bot.send_poll(
            chat_id=private.id,
            question="Q?",
            options=["a", "b", "c"],
            type="quiz",
            correct_option_ids=[0, 2],
            allows_multiple_answers=True,
        )

        assert message.poll.correct_option_ids == [0, 2]
        assert message.poll.allows_revoting is False

    async def test_a_regular_poll_allows_revoting_by_default(self, env, private):
        message = await env.bot.send_poll(chat_id=private.id, question="Q?", options=["a", "b"])

        assert message.poll.allows_revoting is True

    async def test_a_correct_option_must_be_an_option(self, env, private):
        with pytest.raises(TelegramBadRequest, match=r"\[5\] are not options"):
            await env.bot.send_poll(
                chat_id=private.id,
                question="Q?",
                options=["a", "b"],
                type="quiz",
                correct_option_ids=[5],
            )

    async def test_a_quiz_without_an_answer_is_refused(self, env, private):
        with pytest.raises(TelegramBadRequest, match="correct_option_ids"):
            await env.bot.send_poll(
                chat_id=private.id,
                question="Q?",
                options=["a", "b"],
                type="quiz",
            )

        assert private.messages == []

    async def test_stopping_a_poll_stores_its_keyboard(self, env, private):
        message = await env.bot.send_poll(chat_id=private.id, question="Q?", options=["a", "b"])

        await env.bot.stop_poll(
            chat_id=private.id,
            message_id=message.message_id,
            reply_markup=KEYBOARD,
        )

        assert (
            private.find_message(message.message_id).reply_markup.model_dump()
            == KEYBOARD.model_dump()
        )


class TestForumTopics:
    async def test_hiding_general_closes_it_and_reopening_unhides_it(self, env, forum):
        await env.bot.hide_general_forum_topic(chat_id=forum.id)

        assert forum.general_topic.is_hidden is True
        assert forum.general_topic.is_closed is True

        await env.bot.reopen_general_forum_topic(chat_id=forum.id)

        assert forum.general_topic.is_hidden is False
        assert forum.general_topic.is_closed is False

    async def test_an_empty_name_keeps_the_name(self, env, forum, topic):
        await env.bot.edit_forum_topic(
            chat_id=forum.id,
            message_thread_id=topic.message_thread_id,
            name="",
        )

        assert forum.topics[topic.message_thread_id].name == "Support"
        assert forum.messages[-1].forum_topic_edited.name is None

    async def test_an_empty_emoji_id_removes_the_icon(self, env, forum, topic):
        thread_id = topic.message_thread_id
        await env.bot.edit_forum_topic(
            chat_id=forum.id,
            message_thread_id=thread_id,
            icon_custom_emoji_id="123",
        )
        assert forum.topics[thread_id].icon_custom_emoji_id == "123"

        await env.bot.edit_forum_topic(
            chat_id=forum.id,
            message_thread_id=thread_id,
            icon_custom_emoji_id="",
        )

        assert forum.topics[thread_id].icon_custom_emoji_id is None
        assert forum.messages[-1].forum_topic_edited.icon_custom_emoji_id == ""


class TestBusinessDeletions:
    async def test_another_chats_message_is_untouched(self, env, private, bobs, connection):
        mine = await env.bot.send_message(
            business_connection_id=connection.id,
            chat_id=private.id,
            text="mine",
        )
        theirs = await env.bot.send_message(
            business_connection_id=connection.id,
            chat_id=bobs.id,
            text="theirs",
        )
        # One account numbers its chats' messages from one sequence.
        assert mine.message_id != theirs.message_id

        await env.bot.delete_business_messages(
            business_connection_id=connection.id,
            message_ids=[mine.message_id],
        )

        assert private.messages == []
        assert bobs.messages == [theirs]

    async def test_a_customers_message_takes_the_accounts_next_id(
        self,
        env,
        bob,
        private,
        bobs,
        connection,
    ):
        sent = await env.bot.send_message(
            business_connection_id=connection.id,
            chat_id=private.id,
            text="hi",
        )

        await env.user(bob).in_(bobs, business=connection).send("hello")

        assert bobs.messages[-1].message_id > sent.message_id

    async def test_ids_from_different_chats_are_refused(self, env, private, bobs, connection):
        mine = await env.bot.send_message(
            business_connection_id=connection.id,
            chat_id=private.id,
            text="mine",
        )
        for _ in range(2):
            await env.bot.send_message(chat_id=bobs.id, text="plain")
        theirs = await env.bot.send_message(
            business_connection_id=connection.id,
            chat_id=bobs.id,
            text="theirs",
        )

        with pytest.raises(TelegramBadRequest, match="same chat"):
            await env.bot.delete_business_messages(
                business_connection_id=connection.id,
                message_ids=[mine.message_id, theirs.message_id],
            )

        assert len(private.messages) == 1
        assert len(bobs.messages) == 3

    async def test_ids_no_chat_holds_delete_nothing(self, env, private, connection):
        assert await env.bot.delete_business_messages(
            business_connection_id=connection.id,
            message_ids=[999],
        )


class TestChecklists:
    async def test_a_checklist_keeps_its_content(self, env, private, connection):
        sent = await env.bot.send_checklist(
            business_connection_id=connection.id,
            chat_id=private.id,
            checklist=InputChecklist(
                title="Groceries",
                tasks=[
                    InputChecklistTask(id=1, text="Milk"),
                    InputChecklistTask(id=2, text="Eggs"),
                ],
                others_can_add_tasks=True,
            ),
        )

        assert sent.checklist.title == "Groceries"
        assert [(task.id, task.text) for task in sent.checklist.tasks] == [
            (1, "Milk"),
            (2, "Eggs"),
        ]
        assert sent.checklist.others_can_add_tasks is True

        edited = await env.bot.edit_message_checklist(
            business_connection_id=connection.id,
            chat_id=private.id,
            message_id=sent.message_id,
            checklist=InputChecklist(
                title="Chores",
                tasks=[InputChecklistTask(id=1, text="Dishes")],
            ),
        )

        assert edited.checklist.title == "Chores"
        assert [task.text for task in edited.checklist.tasks] == ["Dishes"]


class TestSynthesis:
    async def test_two_uploads_stay_apart(self, env, private):
        first = await env.bot.send_document(
            chat_id=private.id,
            document=BufferedInputFile(b"first", "a.txt"),
        )
        second = await env.bot.send_document(
            chat_id=private.id,
            document=BufferedInputFile(b"second", "b.txt"),
        )

        assert first.document.file_id != second.document.file_id
        assert first.document.file_unique_id != second.document.file_unique_id
        downloaded = await env.bot.download(first.document, destination=io.BytesIO())
        assert downloaded.getvalue() == b"first"
        downloaded = await env.bot.download(second.document, destination=io.BytesIO())
        assert downloaded.getvalue() == b"second"

    async def test_a_passed_file_id_is_the_stored_one(self, env, private):
        message = await env.bot.send_document(chat_id=private.id, document="known-id")
        edited = await env.bot.edit_message_media(
            chat_id=private.id,
            message_id=(await env.bot.send_photo(chat_id=private.id, photo="a")).message_id,
            media=InputMediaPhoto(media="other-id"),
        )

        assert message.document.file_id == "known-id"
        assert edited.photo[-1].file_id == "other-id"

    async def test_a_url_is_not_a_file_id(self, env, private):
        message = await env.bot.send_photo(chat_id=private.id, photo="https://example.com/a")

        assert message.photo[-1].file_id.startswith("file-")

    async def test_a_dice_is_a_dice(self, env, alice, private):
        for _ in range(8):
            # Each update moves the counter synthesized values come from.
            await env.user(alice).send("roll")
            message = await env.bot.send_dice(chat_id=private.id)

            assert message.dice.emoji == DiceEmoji.DICE
            assert 1 <= message.dice.value <= 6

    @pytest.mark.parametrize(
        ("emoji", "faces"),
        [
            (DiceEmoji.DICE, 6),
            (DiceEmoji.DART, 6),
            (DiceEmoji.BOWLING, 6),
            (DiceEmoji.BASKETBALL, 5),
            (DiceEmoji.FOOTBALL, 5),
            (DiceEmoji.SLOT_MACHINE, 64),
        ],
    )
    async def test_a_dice_value_stays_in_its_emojis_range(self, env, private, emoji, faces):
        env.world.last_update_id = 100
        message = await env.bot.send_dice(chat_id=private.id, emoji=emoji)

        assert message.dice.emoji == emoji
        assert 1 <= message.dice.value <= faces

    async def test_a_sticker_is_a_regular_sticker(self, env, private):
        message = await env.bot.send_sticker(chat_id=private.id, sticker="sticker-id")

        assert message.sticker.type in set(StickerType)
        assert not (message.sticker.is_animated and message.sticker.is_video)

    def test_an_enumerated_string_takes_a_valid_value(self):
        chat = synthesize(Chat, SynthesisContext())

        assert chat.type in set(ChatType)
        # `sender` is an inline query's chat type, not a chat's.
        assert chat.type == ChatType.PRIVATE

    def test_a_synthesized_file_numbers_itself_without_a_world(self):
        context = SynthesisContext()

        first = synthesize(Sticker, context)
        second = synthesize(Sticker, context)

        assert first.file_id != second.file_id

    async def test_counts_of_empty_lists_are_zero(self, env, alice):
        photos = await env.bot(GetUserProfilePhotos(user_id=alice.id))

        assert photos.total_count == 0
        assert photos.photos == []

    def test_counts_that_are_not_list_lengths_stay_positive(self):
        context = SynthesisContext()

        assert synthesize(PaidMediaInfo, context).star_count > 0
        assert synthesize(Giveaway, context).winner_count > 0

    async def test_a_voice_note_block_converts(self, env, private):
        message = await env.bot.send_rich_message(
            chat_id=private.id,
            rich_message=InputRichMessage(
                blocks=[InputRichBlockVoiceNote(voice_note=InputMediaVoiceNote(media="voice"))],
            ),
        )

        assert message.rich_message.blocks[0].voice_note.file_id == "voice"

    async def test_a_rich_block_keeps_its_upload(self, env, private):
        message = await env.bot.send_rich_message(
            chat_id=private.id,
            rich_message=InputRichMessage(
                blocks=[
                    InputRichBlockPhoto(
                        photo=InputMediaPhoto(media=BufferedInputFile(b"pixels", "a.png")),
                    ),
                ],
            ),
        )

        (size,) = message.rich_message.blocks[0].photo
        downloaded = await env.bot.download(size, destination=io.BytesIO())
        assert downloaded.getvalue() == b"pixels"

    def test_aliases_and_annotated_types_are_looked_through(self):
        assert annotation_accepts(RichTextUnion, RichTextBold)
        assert not annotation_accepts(RichTextUnion, Sticker)


class TestStarTransactions:
    async def test_a_payment_and_its_refund(self, env, alice, private):
        await env.user(alice).pay(total_amount=50)
        charge = private.messages[-1].successful_payment.telegram_payment_charge_id
        await env.bot.refund_star_payment(user_id=alice.id, telegram_payment_charge_id=charge)

        payment, refund = (await env.bot.get_star_transactions()).transactions

        assert (payment.id, payment.amount) == (charge, 50)
        assert (refund.id, refund.amount) == (charge, 50)
        assert isinstance(payment.source, TransactionPartnerUser)
        assert payment.source.user.id == alice.id
        assert payment.receiver is None
        assert refund.receiver.user.id == alice.id
        assert refund.source is None

    async def test_a_refund_to_another_user_is_refused(self, env, alice, bob, private):
        await env.user(alice).pay(total_amount=50)
        charge = private.messages[-1].successful_payment.telegram_payment_charge_id

        with pytest.raises(TelegramBadRequest, match="not paid by user"):
            await env.bot.refund_star_payment(user_id=bob.id, telegram_payment_charge_id=charge)

        assert env.world.stars.charge(charge).is_refunded is False


class TestEditableAdministrators:
    async def test_a_member_the_bot_promoted_is_editable(self, env, team, bob):
        await env.bot.promote_chat_member(chat_id=team.id, user_id=bob.id, can_pin_messages=True)

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=bob.id)
        admins = await env.bot.get_chat_administrators(chat_id=team.id)

        assert member.can_be_edited is True
        assert [admin.can_be_edited for admin in admins if admin.user.id == bob.id] == [True]

    async def test_a_member_someone_else_promoted_again_is_not(self, env, team, alice, bob):
        await env.bot.promote_chat_member(chat_id=team.id, user_id=bob.id, can_pin_messages=True)
        await env.user(alice).in_(team).promote(bob, can_delete_messages=True)

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=bob.id)

        assert member.can_be_edited is False

    async def test_editing_someone_elses_administrator_keeps_it_so(self, env, team, bob):
        team.member(bob.id).set_status(ChatMemberStatus.ADMINISTRATOR)

        await env.bot.promote_chat_member(chat_id=team.id, user_id=bob.id, can_pin_messages=True)

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=bob.id)
        assert member.can_be_edited is False

    async def test_a_declared_administrator_is_not(self, env, team, blueprint):
        member = await env.bot.get_chat_member(chat_id=team.id, user_id=blueprint.bot.id)

        assert member.status == ChatMemberStatus.ADMINISTRATOR
        assert member.can_be_edited is False

    async def test_a_demoted_member_forgets_who_promoted_them(self, env, team, bob):
        await env.bot.promote_chat_member(chat_id=team.id, user_id=bob.id, can_pin_messages=True)
        await env.bot.promote_chat_member(chat_id=team.id, user_id=bob.id)
        team.member(bob.id).set_status(ChatMemberStatus.ADMINISTRATOR)

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=bob.id)

        assert member.can_be_edited is False

    async def test_the_bot_cannot_edit_or_demote_someone_elses_administrator(
        self, env, team, alice, bob
    ):
        await env.user(alice).in_(team).promote(bob, can_delete_messages=True)

        with pytest.raises(TelegramBadRequest, match="not enough rights"):
            await env.bot.promote_chat_member(
                chat_id=team.id, user_id=bob.id, can_pin_messages=True
            )
        with pytest.raises(TelegramBadRequest, match="not enough rights"):
            await env.bot.promote_chat_member(chat_id=team.id, user_id=bob.id)

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=bob.id)
        assert member.status == ChatMemberStatus.ADMINISTRATOR
        assert member.can_delete_messages is True
        assert member.can_pin_messages is False

    async def test_the_bot_cannot_title_someone_elses_administrator(self, env, team, alice, bob):
        await env.user(alice).in_(team).promote(bob, can_delete_messages=True)

        with pytest.raises(TelegramBadRequest, match="not enough rights"):
            await env.bot.set_chat_administrator_custom_title(
                chat_id=team.id, user_id=bob.id, custom_title="Boss"
            )

        assert team.member(bob.id).custom_title is None

    async def test_the_bot_titles_an_administrator_it_promoted(self, env, team, bob):
        await env.bot.promote_chat_member(chat_id=team.id, user_id=bob.id, can_pin_messages=True)

        await env.bot.set_chat_administrator_custom_title(
            chat_id=team.id, user_id=bob.id, custom_title="Boss"
        )

        assert team.member(bob.id).custom_title == "Boss"


class TestMemberTags:
    async def test_a_restricted_user_outside_the_chat_cannot_be_tagged(self, env, team, bob):
        await env.user(bob).in_(team).leave()
        await env.bot.restrict_chat_member(
            chat_id=team.id,
            user_id=bob.id,
            permissions=ChatPermissions(can_send_messages=False),
        )

        with pytest.raises(TelegramBadRequest, match="not a member"):
            await env.bot.set_chat_member_tag(chat_id=team.id, user_id=bob.id, tag="muted")

        assert team.member(bob.id).tag is None


class TestDeclaredWorlds:
    async def test_a_declared_business_connection_is_dated_by_the_clock(self, env, connection):
        assert env.world.business_connections[connection.id].date == env.now

    async def test_declared_permissions_follow_their_defaults(self, dp):
        blueprint = Blueprint()
        quiet = blueprint.add_user("Quiet")
        team = blueprint.add_supergroup("Team")
        blueprint.set_member(
            team,
            quiet,
            permissions=ChatPermissions(can_send_messages=True, can_send_polls=True),
        )
        team.permissions = ChatPermissions(can_send_other_messages=True)
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            member = await env.bot.get_chat_member(chat_id=team.id, user_id=quiet.id)
            chat = await env.bot.get_chat(chat_id=team.id)

            assert member.can_react_to_messages is True
            assert chat.permissions.can_send_messages is True
            assert chat.permissions.can_react_to_messages is True
        finally:
            env.dispose_sync()

    def test_declared_topics_are_created_by_the_bot(self, blueprint, topic):
        world = blueprint.build()

        created = world.chat(topic.chat_id).find_message(topic.message_thread_id)

        assert created.forum_topic_created.name == "Support"
        assert created.from_user.id == blueprint.bot.id

    async def test_a_declared_poll_is_stored_on_a_message(self, dp):
        blueprint = Blueprint()
        alice = blueprint.add_user("Alice")
        chat = blueprint.add_private_chat(alice)
        poll = blueprint.add_poll(
            chat,
            "Lunch?",
            ["Pizza", "Sushi"],
            is_anonymous=False,
        )
        env = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            stored = env.chat(chat).find_message(poll.message_id)

            assert stored.poll.id == poll.poll_id
            assert stored.poll.question == "Lunch?"
            assert stored.poll.allows_revoting is True
            assert stored.from_user.id == blueprint.bot.id

            await env.user(alice).vote(poll.poll_id, [1])

            assert env.world.poll(poll.poll_id).vote_count(1) == 1
        finally:
            env.dispose_sync()

    def test_a_declared_quiz_keeps_its_answer(self):
        blueprint = Blueprint()
        chat = blueprint.add_private_chat(blueprint.add_user("Alice"))
        poll = blueprint.add_poll(
            chat,
            "2 + 2?",
            ["3", "4"],
            type="quiz",
            correct_option_ids=[1],
            explanation="Arithmetic",
        )

        world = blueprint.build()
        stored = world.poll(poll.poll_id)

        assert stored.correct_option_ids == [1]
        assert stored.explanation == "Arithmetic"
        assert stored.as_poll().correct_option_id == 1

    def test_a_declared_quiz_without_an_answer_is_refused(self):
        blueprint = Blueprint()
        chat = blueprint.add_private_chat(blueprint.add_user("Alice"))

        with pytest.raises(ValueError, match="correct_option_ids"):
            blueprint.add_poll(chat, "2 + 2?", ["3", "4"], type="quiz")
        with pytest.raises(ValueError, match="not options"):
            blueprint.add_poll(chat, "2 + 2?", ["3", "4"], type="quiz", correct_option_ids=[2])


class TestChatRegistryRecipe:
    async def test_the_recommended_copy_works_in_a_running_environment(self, blueprint, dp):
        team_id = blueprint.chats[2].id
        donor = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        other = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            await donor.bot.send_message(chat_id=team_id, text="hi")
            chat = donor.world.chats[team_id]
            with pytest.raises(WorldLookupError) as refused:
                other.world.chats[team_id] = chat
            assert "copy.deepcopy(chat, memo)" in str(refused.value)

            memo = {id(chat.world): None, id(chat.bound_bot): None}
            clone = copy.deepcopy(chat, memo)
            del other.world.chats[team_id]
            other.world.chats[team_id] = clone

            assert clone.world is other.world
            assert clone.messages[-1].bot is other.bot
            assert chat.world is donor.world
            assert chat.messages[-1].bot is donor.bot
        finally:
            donor.dispose_sync()
            other.dispose_sync()

    async def test_a_moved_chat_binds_its_ephemeral_messages(self, blueprint, dp):
        team_id = blueprint.chats[2].id
        receiver_id = blueprint.users[0].id
        donor = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        other = BotTestEnvironment(blueprint=blueprint, dispatcher=dp)
        try:
            await donor.bot.send_message(
                chat_id=team_id,
                text="only you",
                ephemeral_message_parameters=EphemeralMessageParameters(
                    receiver_user_id=receiver_id,
                ),
            )
            chat = donor.world.chats[team_id]
            memo = {id(chat.world): None, id(chat.bound_bot): None}
            clone = copy.deepcopy(chat, memo)
            del other.world.chats[team_id]
            other.world.chats[team_id] = clone

            assert clone.ephemeral_messages(receiver_id)[0].bot is other.bot
        finally:
            donor.dispose_sync()
            other.dispose_sync()

    def test_a_world_without_a_bot_registers_chats_as_they_are(self, blueprint):
        world: World = blueprint.build()
        chat = world.chats.pop(blueprint.chats[0].id)

        world.chats[chat.id] = chat

        assert chat.world is world
