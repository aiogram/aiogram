import datetime

import pytest

from aiogram.enums import ChatMemberStatus, ContentType
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import (
    GetUserProfilePhotos,
    SendInvoice,
    SendMessage,
    SendRichMessage,
    VerifyUser,
)
from aiogram.test import WorldLookupError
from aiogram.test.modeling import MEDIA_FIELDS
from aiogram.test.world import BASE_DATE
from aiogram.types import (
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberMember,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputChecklist,
    InputChecklistTask,
    InputMediaPhoto,
    InputPaidMediaPhoto,
    InputRichBlockParagraph,
    InputRichMessage,
    LabeledPrice,
    Message,
    MessageId,
    ReplyKeyboardMarkup,
    ReplyParameters,
)

#: Methods whose request payload is not simply ``{<message field>: "file-id"}``.
SEND_PAYLOADS = {
    "SendLocation": {"latitude": 1.0, "longitude": 2.0},
    "SendVenue": {"latitude": 1.0, "longitude": 2.0, "title": "t", "address": "a"},
    "SendContact": {"phone_number": "+100", "first_name": "Alice"},
    "SendDice": {},
    "SendGame": {"game_short_name": "tetris"},
    "SendInvoice": {
        "title": "Sub",
        "description": "A subscription",
        "payload": "sub-1",
        "currency": "XTR",
        "prices": [LabeledPrice(label="Month", amount=100)],
    },
    "SendPaidMedia": {
        "star_count": 5,
        "media": [InputPaidMediaPhoto(media="file-id")],
    },
    "SendChecklist": {
        "checklist": InputChecklist(
            title="Groceries",
            tasks=[InputChecklistTask(id=1, text="Milk")],
        ),
    },
    "SendLivePhoto": {"live_photo": "file-id", "photo": "file-id"},
    "SendRichMessage": {
        "rich_message": InputRichMessage(blocks=[InputRichBlockParagraph(text="hi")]),
    },
}


def send_payload(method_type, field, connection):
    """Request arguments for a send method, defaulting to a single file id."""
    payload = dict(SEND_PAYLOADS.get(method_type.__name__, {field: "file-id"}))
    if (
        "business_connection_id" in method_type.model_fields
        and method_type.model_fields["business_connection_id"].is_required()
    ):
        payload["business_connection_id"] = connection.id
    return payload


class TestSending:
    async def test_send_message_appends_to_the_chat(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hello")

        assert isinstance(message, Message)
        assert private.messages[-1] is message
        assert message.from_user.id == env.blueprint.bot.id
        assert message.chat.id == private.id

    async def test_message_ids_are_sequential(self, env, private):
        first = await env.bot.send_message(chat_id=private.id, text="a")
        second = await env.bot.send_message(chat_id=private.id, text="b")

        assert second.message_id == first.message_id + 1

    @pytest.mark.parametrize(
        "method_type",
        list(MEDIA_FIELDS),
        ids=lambda item: item.__name__,
    )
    async def test_media_sends_produce_a_typed_message(
        self,
        env,
        private,
        connection,
        method_type,
    ):
        field = MEDIA_FIELDS[method_type]
        payload = {"chat_id": private.id, **send_payload(method_type, field, connection)}

        message = await env.bot(method_type(**payload))

        assert getattr(message, field) is not None
        assert message.content_type != ContentType.UNKNOWN

    @pytest.mark.parametrize(
        "method_type",
        list(MEDIA_FIELDS),
        ids=lambda item: item.__name__,
    )
    async def test_every_send_stores_the_message_it_returns(
        self,
        env,
        private,
        connection,
        method_type,
    ):
        field = MEDIA_FIELDS[method_type]
        payload = {"chat_id": private.id, **send_payload(method_type, field, connection)}

        first = await env.bot(method_type(**payload))
        second = await env.bot(method_type(**payload))

        assert private.messages[-2] is first
        assert private.messages[-1] is second
        assert second.message_id == first.message_id + 1

    @pytest.mark.parametrize(
        "method_type",
        [SendInvoice, SendRichMessage],
        ids=lambda item: item.__name__,
    )
    async def test_a_button_on_any_sent_message_is_clickable(
        self,
        env,
        private,
        alice,
        connection,
        method_type,
    ):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Pay", callback_data="pay")]],
        )
        payload = send_payload(method_type, MEDIA_FIELDS[method_type], connection)
        await env.bot(method_type(chat_id=private.id, reply_markup=markup, **payload))

        seen = []
        env.dispatcher.callback_query.register(lambda query: seen.append(query.data))
        await alice.click("pay")

        assert seen == ["pay"]

    async def test_inline_keyboard_is_stored(self, env, private):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )

        message = await env.bot.send_message(chat_id=private.id, text="hi", reply_markup=markup)

        # Results come back mounted to the bot, so they compare by content, not by
        # instance — exactly as they would after a real response was parsed.
        assert message.reply_markup.model_dump() == markup.model_dump()

    async def test_reply_keyboard_is_not_stored_on_the_message(self, env, private):
        markup = ReplyKeyboardMarkup(keyboard=[[{"text": "Go"}]])

        message = await env.bot.send_message(chat_id=private.id, text="hi", reply_markup=markup)

        assert message.reply_markup is None

    async def test_protect_content(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi", protect_content=True)

        assert message.has_protected_content is True

    async def test_reply_parameters_link_the_original(self, env, private, alice):
        await alice.send("question")
        original = private.messages[-1]

        answer = await env.bot.send_message(
            chat_id=private.id,
            text="answer",
            reply_parameters=ReplyParameters(message_id=original.message_id),
        )

        assert answer.reply_to_message.message_id == original.message_id

    async def test_reply_parameters_to_a_missing_message_are_ignored(self, env, private):
        message = await env.bot.send_message(
            chat_id=private.id,
            text="answer",
            reply_parameters=ReplyParameters(message_id=999),
        )

        assert message.reply_to_message is None

    async def test_media_group(self, env, private):
        messages = await env.bot.send_media_group(
            chat_id=private.id,
            media=[InputMediaPhoto(media="a"), InputMediaPhoto(media="b")],
        )

        assert len(messages) == 2
        assert len(private.messages) == 2

    async def test_chat_can_be_addressed_by_username(self, env, private):
        message = await env.bot.send_message(chat_id="@alice", text="hi")

        assert message.chat.id == private.id

    async def test_unknown_chat(self, env):
        with pytest.raises(TelegramBadRequest, match="chat not found"):
            await env.bot.send_message(chat_id=-1, text="hi")


class TestMovingMessages:
    async def test_forward(self, env, private, team, alice):
        await alice.send("original")
        original = private.messages[-1]

        forwarded = await env.bot.forward_message(
            chat_id=team.id,
            from_chat_id=private.id,
            message_id=original.message_id,
        )

        assert forwarded.text == "original"
        assert forwarded.chat.id == team.id
        assert team.messages[-1] is forwarded

    async def test_forward_missing_message(self, env, private, team):
        with pytest.raises(TelegramBadRequest, match="message to forward not found"):
            await env.bot.forward_message(
                chat_id=team.id,
                from_chat_id=private.id,
                message_id=404,
            )

    async def test_copy(self, env, private, team, alice):
        await alice.send("original")
        original = private.messages[-1]

        copied = await env.bot.copy_message(
            chat_id=team.id,
            from_chat_id=private.id,
            message_id=original.message_id,
        )

        assert isinstance(copied, MessageId)
        assert team.messages[-1].message_id == copied.message_id

    async def test_copy_replaces_the_caption(self, env, private, team):
        await env.bot.send_photo(chat_id=private.id, photo="file", caption="before")
        original = private.messages[-1]

        await env.bot.copy_message(
            chat_id=team.id,
            from_chat_id=private.id,
            message_id=original.message_id,
            caption="after",
        )

        assert team.messages[-1].caption == "after"

    async def test_copy_missing_message(self, env, private, team):
        with pytest.raises(TelegramBadRequest, match="message to copy not found"):
            await env.bot.copy_message(chat_id=team.id, from_chat_id=private.id, message_id=404)


class TestEditing:
    async def test_edit_text_mutates_in_place(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="before")

        edited = await env.bot.edit_message_text(
            chat_id=private.id,
            message_id=message.message_id,
            text="after",
        )

        assert edited.text == "after"
        assert len(private.messages) == 1
        assert private.messages[-1].text == "after"

    async def test_edit_caption(self, env, private):
        message = await env.bot.send_photo(chat_id=private.id, photo="file", caption="before")

        edited = await env.bot.edit_message_caption(
            chat_id=private.id,
            message_id=message.message_id,
            caption="after",
        )

        assert edited.caption == "after"

    async def test_edit_reply_markup(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )

        edited = await env.bot.edit_message_reply_markup(
            chat_id=private.id,
            message_id=message.message_id,
            reply_markup=markup,
        )

        assert edited.reply_markup.model_dump() == markup.model_dump()

    async def test_edit_missing_message(self, env, private):
        with pytest.raises(TelegramBadRequest, match="message to edit not found"):
            await env.bot.edit_message_text(chat_id=private.id, message_id=404, text="x")

    async def test_edit_deleted_message(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")
        await env.bot.delete_message(chat_id=private.id, message_id=message.message_id)

        with pytest.raises(TelegramBadRequest, match="message to edit not found"):
            await env.bot.edit_message_text(
                chat_id=private.id,
                message_id=message.message_id,
                text="x",
            )

    async def test_inline_messages_are_not_modeled(self, env):
        with pytest.raises(WorldLookupError, match="inline messages are not modeled"):
            await env.bot.edit_message_text(inline_message_id="abc", text="x")


class TestDeleting:
    async def test_delete(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        assert await env.bot.delete_message(chat_id=private.id, message_id=message.message_id)
        assert private.messages == []

    async def test_delete_missing_message(self, env, private):
        with pytest.raises(TelegramBadRequest, match="message to delete not found"):
            await env.bot.delete_message(chat_id=private.id, message_id=404)

    async def test_delete_many_ignores_missing_ids(self, env, private):
        first = await env.bot.send_message(chat_id=private.id, text="a")

        assert await env.bot.delete_messages(
            chat_id=private.id,
            message_ids=[first.message_id, 404],
        )
        assert private.messages == []


class TestPinning:
    async def test_pin_and_unpin(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        await env.bot.pin_chat_message(chat_id=private.id, message_id=message.message_id)
        assert private.pinned_message_ids == [message.message_id]

        await env.bot.pin_chat_message(chat_id=private.id, message_id=message.message_id)
        assert private.pinned_message_ids == [message.message_id]

        await env.bot.unpin_chat_message(chat_id=private.id, message_id=message.message_id)
        assert private.pinned_message_ids == []

    async def test_unpin_all_by_omitting_the_id(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")
        await env.bot.pin_chat_message(chat_id=private.id, message_id=message.message_id)

        await env.bot.unpin_chat_message(chat_id=private.id)

        assert private.pinned_message_ids == []

    async def test_unpin_an_unpinned_message(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        assert await env.bot.unpin_chat_message(
            chat_id=private.id,
            message_id=message.message_id,
        )

    async def test_pin_missing_message(self, env, private):
        with pytest.raises(TelegramBadRequest, match="message to pin not found"):
            await env.bot.pin_chat_message(chat_id=private.id, message_id=404)


class TestMembership:
    async def test_ban(self, env, team, blueprint):
        alice_id = blueprint.users[0].id
        until = BASE_DATE + datetime.timedelta(days=1)

        await env.bot.ban_chat_member(chat_id=team.id, user_id=alice_id, until_date=until)

        member = team.member(alice_id)
        assert member.status == ChatMemberStatus.KICKED
        assert member.until_date == until

    async def test_ban_accepts_a_timedelta(self, env, team, blueprint):
        alice_id = blueprint.users[0].id

        await env.bot.ban_chat_member(
            chat_id=team.id,
            user_id=alice_id,
            until_date=datetime.timedelta(days=1),
        )

        assert team.member(alice_id).until_date == BASE_DATE + datetime.timedelta(days=1)

    async def test_ban_accepts_a_timestamp(self, env, team, blueprint):
        alice_id = blueprint.users[0].id

        await env.bot.ban_chat_member(chat_id=team.id, user_id=alice_id, until_date=0)

        assert team.member(alice_id).until_date.year == 1970

    async def test_unban(self, env, team, blueprint):
        alice_id = blueprint.users[0].id
        await env.bot.ban_chat_member(chat_id=team.id, user_id=alice_id)

        await env.bot.unban_chat_member(chat_id=team.id, user_id=alice_id)

        assert team.member(alice_id).status == ChatMemberStatus.LEFT

    async def test_promote_and_demote(self, env, team, blueprint):
        alice_id = blueprint.users[0].id

        await env.bot.promote_chat_member(
            chat_id=team.id,
            user_id=alice_id,
            can_delete_messages=True,
        )
        assert team.member(alice_id).status == ChatMemberStatus.ADMINISTRATOR

        await env.bot.promote_chat_member(chat_id=team.id, user_id=alice_id)
        assert team.member(alice_id).status == ChatMemberStatus.MEMBER

    async def test_restrict(self, env, team, blueprint):
        alice_id = blueprint.users[0].id

        await env.bot.restrict_chat_member(
            chat_id=team.id,
            user_id=alice_id,
            permissions=ChatPermissions(can_send_messages=False),
        )

        assert team.member(alice_id).status == ChatMemberStatus.RESTRICTED

    async def test_leave(self, env, team):
        await env.bot.leave_chat(chat_id=team.id)

        assert team.member(env.blueprint.bot.id).status == ChatMemberStatus.LEFT

    async def test_get_chat_member_reflects_state(self, env, team, blueprint):
        alice_id = blueprint.users[0].id

        member = await env.bot.get_chat_member(chat_id=team.id, user_id=alice_id)
        assert isinstance(member, ChatMemberAdministrator)

        await env.bot.ban_chat_member(chat_id=team.id, user_id=alice_id)
        member = await env.bot.get_chat_member(chat_id=team.id, user_id=alice_id)
        assert isinstance(member, ChatMemberBanned)

    async def test_get_chat_member_for_the_bot(self, env, team):
        member = await env.bot.get_chat_member(chat_id=team.id, user_id=env.blueprint.bot.id)

        assert isinstance(member, ChatMemberMember)

    async def test_get_chat(self, env, team):
        chat = await env.bot.get_chat(chat_id=team.id)

        assert chat.id == team.id
        assert chat.title == "Team"
        assert chat.type == team.type


class TestFallback:
    async def test_unmodeled_method_is_synthesized_and_recorded(self, env, blueprint):
        result = await env.bot.get_user_profile_photos(user_id=blueprint.users[0].id)

        assert result is not None
        assert env.calls.count(GetUserProfilePhotos) == 1

    async def test_unmodeled_boolean_method(self, env, alice):
        assert await env.bot.verify_user(user_id=alice.user.id) is True
        assert env.calls.count(VerifyUser) == 1

    async def test_answer_callback_query_is_acknowledged(self, env, private, alice):
        markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Go", callback_data="go")]],
        )
        await env.bot.send_message(chat_id=private.id, text="hi", reply_markup=markup)
        answered = []
        env.dispatcher.callback_query.register(
            lambda query: answered.append(query.answer("ok")),
        )

        await alice.click("go")

        assert await answered[0] is True

    async def test_calls_are_recorded_with_resolved_defaults(self, env, private):
        await env.bot.send_message(chat_id=private.id, text="hi")

        recorded = env.calls.last(SendMessage)
        assert recorded.chat_id == private.id
        assert not isinstance(recorded.parse_mode, object.__class__)


class TestStoredMessagesAreUsable:
    """
    A message the world stores carries the bot, whoever put it there.

    Service messages are the case no result covers: nothing hands one back, so if binding
    happened only on the way out of a call they would be the one kind of message a test
    could read but not act on.
    """

    async def test_a_topic_creation_message_is_bound(self, env, team):
        await env.bot.create_forum_topic(chat_id=team.id, name="Support")

        service = team.messages[-1]
        assert service.forum_topic_created is not None
        assert service.bot is env.bot
        assert service.forum_topic_created.bot is env.bot

        await service.answer("welcome")

        assert team.messages[-1].text == "welcome"

    async def test_an_edited_message_keeps_the_worlds_bot(self, env, private):
        message = await env.bot.send_message(chat_id=private.id, text="hi")

        await env.bot.edit_message_text(
            chat_id=private.id,
            message_id=message.message_id,
            text="bye",
        )

        assert private.messages[-1].bot is env.bot
