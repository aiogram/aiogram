"""
What each Bot API method does to the fake world.

One handler per method, registered with :func:`models`, found by
:meth:`aiogram.test.BotTestEnvironment.handle_call` and handed ``(env, method)``. A handler
returns what the call returns; anything it does not model falls through to
:func:`~aiogram.test.synthesis.synthesize_result`.

**The copy boundary — read this before adding a handler.** Objects cross between the code
under test and the world in both directions, and each direction has exactly one rule:

*In: already done for you.* ``handle_call`` hands every handler a
:func:`~aiogram.test.mounting.detached_copy` of the method, made after the call log has
recorded the caller's own object. So whatever a handler reads off ``method`` — a
``reply_markup``, a ``ChatPermissions`` constant, a list of ``BotCommand`` — is already the
world's to keep, and storing it directly is correct. There is nothing to copy in a handler,
and the eight hand-written copies that used to sit in this module are gone: one copy at the
choke point does what all of them did, and cannot be forgotten by the next handler.

*Out: messages by identity, value objects by copy.* A :class:`~aiogram.types.Message` the
world stores is handed back **as it is**, so ``chat.messages[-1] is returned_message`` holds
and an edit through either lands on both — that identity is a feature tests rely on.
Everything else the world stores is a *value* a test compares against a declared constant
(``chat.permissions == DECLARED``), and a result gets mounted to the calling bot on its way
out — so handing out the stored instance would bind the world's own state and leave that
comparison failing with two identical-looking sides. Those are copied out explicitly, at the
handler that returns them.

**Refusing a call.** Raise :class:`~aiogram.test.errors.ApiRejection` with Telegram's own
wording for something the real API would refuse; ``handle_call`` turns it into a
:class:`~aiogram.exceptions.TelegramBadRequest`. Raise
:class:`~aiogram.test.WorldLookupError` for a gap in the test's own setup or a limit of the
fake — that one propagates and fails the test instead of arriving as an error the bot might
catch.
"""

from __future__ import annotations

import datetime
import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, get_args

from pydantic import BaseModel

from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.methods import (
    AddStickerToSet,
    AnswerCallbackQuery,
    AnswerChatJoinRequestQuery,
    AnswerGuestQuery,
    AnswerInlineQuery,
    AnswerPreCheckoutQuery,
    AnswerShippingQuery,
    AnswerWebAppQuery,
    ApproveChatJoinRequest,
    ApproveSuggestedPost,
    BanChatMember,
    BanChatSenderChat,
    Close,
    CloseForumTopic,
    CloseGeneralForumTopic,
    ConvertGiftToStars,
    CopyMessage,
    CopyMessages,
    CreateChatInviteLink,
    CreateChatSubscriptionInviteLink,
    CreateForumTopic,
    CreateInvoiceLink,
    CreateNewStickerSet,
    DeclineChatJoinRequest,
    DeclineSuggestedPost,
    DeleteAllMessageReactions,
    DeleteBusinessMessages,
    DeleteChatPhoto,
    DeleteChatStickerSet,
    DeleteEphemeralMessage,
    DeleteForumTopic,
    DeleteMessage,
    DeleteMessageReaction,
    DeleteMessages,
    DeleteMyCommands,
    DeleteStickerFromSet,
    DeleteStickerSet,
    DeleteWebhook,
    EditChatInviteLink,
    EditChatSubscriptionInviteLink,
    EditEphemeralMessageCaption,
    EditEphemeralMessageMedia,
    EditEphemeralMessageReplyMarkup,
    EditEphemeralMessageText,
    EditForumTopic,
    EditGeneralForumTopic,
    EditMessageCaption,
    EditMessageChecklist,
    EditMessageLiveLocation,
    EditMessageMedia,
    EditMessageReplyMarkup,
    EditMessageText,
    EditUserStarSubscription,
    ExportChatInviteLink,
    ForwardMessage,
    ForwardMessages,
    GetAvailableGifts,
    GetBusinessAccountGifts,
    GetBusinessAccountStarBalance,
    GetBusinessConnection,
    GetChat,
    GetChatAdministrators,
    GetChatGifts,
    GetChatMember,
    GetChatMemberCount,
    GetChatMenuButton,
    GetCustomEmojiStickers,
    GetFile,
    GetForumTopicIconStickers,
    GetGameHighScores,
    GetManagedBotAccessSettings,
    GetManagedBotToken,
    GetMe,
    GetMyCommands,
    GetMyDefaultAdministratorRights,
    GetMyDescription,
    GetMyName,
    GetMyShortDescription,
    GetMyStarBalance,
    GetStarTransactions,
    GetStickerSet,
    GetUpdates,
    GetUserChatBoosts,
    GetUserGifts,
    GetUserPersonalChatMessages,
    GetUserProfileAudios,
    GetUserProfilePhotos,
    GetWebhookInfo,
    GiftPremiumSubscription,
    HideGeneralForumTopic,
    LeaveChat,
    LogOut,
    PinChatMessage,
    PromoteChatMember,
    ReadBusinessMessage,
    RefundStarPayment,
    RemoveChatVerification,
    RemoveMyProfilePhoto,
    RemoveUserVerification,
    ReopenForumTopic,
    ReopenGeneralForumTopic,
    ReplaceManagedBotToken,
    ReplaceStickerInSet,
    RestrictChatMember,
    RevokeChatInviteLink,
    SavePreparedInlineMessage,
    SavePreparedKeyboardButton,
    SendAnimation,
    SendAudio,
    SendChatAction,
    SendChatJoinRequestWebApp,
    SendChecklist,
    SendContact,
    SendDice,
    SendDocument,
    SendGame,
    SendGift,
    SendInvoice,
    SendLivePhoto,
    SendLocation,
    SendMediaGroup,
    SendMessage,
    SendMessageDraft,
    SendPaidMedia,
    SendPhoto,
    SendPoll,
    SendRichMessage,
    SendRichMessageDraft,
    SendSticker,
    SendVenue,
    SendVideo,
    SendVideoNote,
    SendVoice,
    SetChatAdministratorCustomTitle,
    SetChatDescription,
    SetChatMemberTag,
    SetChatMenuButton,
    SetChatPermissions,
    SetChatPhoto,
    SetChatStickerSet,
    SetChatTitle,
    SetCustomEmojiStickerSetThumbnail,
    SetGameScore,
    SetManagedBotAccessSettings,
    SetMessageReaction,
    SetMyCommands,
    SetMyDefaultAdministratorRights,
    SetMyDescription,
    SetMyName,
    SetMyProfilePhoto,
    SetMyShortDescription,
    SetPassportDataErrors,
    SetStickerEmojiList,
    SetStickerKeywords,
    SetStickerMaskPosition,
    SetStickerPositionInSet,
    SetStickerSetThumbnail,
    SetStickerSetTitle,
    SetUserEmojiStatus,
    SetWebhook,
    StopMessageLiveLocation,
    StopPoll,
    TelegramMethod,
    TransferBusinessAccountStars,
    TransferGift,
    UnbanChatMember,
    UnbanChatSenderChat,
    UnhideGeneralForumTopic,
    UnpinAllChatMessages,
    UnpinAllForumTopicMessages,
    UnpinAllGeneralForumTopicMessages,
    UnpinChatMessage,
    UpgradeGift,
    UploadStickerFile,
    VerifyChat,
    VerifyUser,
)
from aiogram.types import (
    BotCommand,
    BotDescription,
    BotName,
    BotShortDescription,
    BufferedInputFile,
    BusinessConnection,
    ChatAdministratorRights,
    ChatFullInfo,
    ChatInviteLink,
    ChatPermissions,
    File,
    ForumTopic,
    ForumTopicClosed,
    ForumTopicEdited,
    ForumTopicReopened,
    GeneralForumTopicHidden,
    GeneralForumTopicUnhidden,
    Gift,
    Gifts,
    InlineKeyboardMarkup,
    InputRichMessage,
    InputSticker,
    Location,
    MenuButtonDefault,
    Message,
    MessageId,
    MessageOriginChannel,
    MessageOriginUser,
    OwnedGiftRegular,
    OwnedGifts,
    OwnedGiftUnique,
    Poll,
    StarAmount,
    StarTransactions,
    Sticker,
    StickerSet,
    UniqueGift,
    Update,
    User,
)

from .errors import ApiRejection
from .mounting import detached_copy
from .rich import materialize_rich_message
from .synthesis import annotation_accepts, nonempty, synthesize
from .world import (
    DEFAULT_TOPIC_ICON_COLOR,
    ChatState,
    InviteLinkState,
    MemberState,
    OwnedGiftState,
    PollState,
    QueryKind,
    StickerSetState,
    TopicState,
    UserState,
    WorldLookupError,
    create_topic,
    mask,
    no_administrator_rights,
    scope_key,
)

if TYPE_CHECKING:
    from .environment import BotTestEnvironment

MethodHandler = Callable[["BotTestEnvironment", Any], Any]

REGISTRY: dict[type[TelegramMethod[Any]], MethodHandler] = {}

#: Method class -> the ``Message`` field the resulting message carries.
MEDIA_FIELDS: dict[type[TelegramMethod[Any]], str] = {
    SendPhoto: "photo",
    SendAudio: "audio",
    SendDocument: "document",
    SendVideo: "video",
    SendAnimation: "animation",
    SendVoice: "voice",
    SendVideoNote: "video_note",
    SendSticker: "sticker",
    SendDice: "dice",
    SendLocation: "location",
    SendVenue: "venue",
    SendContact: "contact",
    SendInvoice: "invoice",
    SendGame: "game",
    SendPaidMedia: "paid_media",
    SendChecklist: "checklist",
    SendLivePhoto: "live_photo",
    SendRichMessage: "rich_message",
}

#: Message fields an ``editMessageMedia`` call can replace, derived from the method's own
#: media union so the set follows the Bot API rather than a hand-kept list.
EDITABLE_MEDIA_FIELDS: tuple[str, ...] = tuple(
    re.sub(r"(?<!^)(?=[A-Z])", "_", member.__name__.removeprefix("InputMedia")).lower()
    for member in get_args(EditMessageMedia.model_fields["media"].annotation)
)

#: Methods the environment deliberately does not model, grouped by why.
#:
#: These are decisions, not omissions: for each of them the recorded call is the whole
#: useful assertion, the surface is media the fake never processes, or it belongs to a
#: layer the toolkit does not drive. They stay on the record-and-synthesize path, and
#: `tests/test_testing/test_record_only.py` asserts they never quietly become modeled.
#:
#: This list is deliberately *not* exhaustive over unmodeled methods — see design
#: decision D1 of `specify-record-only-boundary`. Clusters whose modeling is merely
#: deferred (stories, business account profile) are absent on purpose: "not yet" is not
#: the same answer as "no".
RECORD_ONLY: frozenset[type[TelegramMethod[Any]]] = frozenset(
    {
        # Drafts are a temporary preview Telegram does not
        # persist, so there is no state a test could read back.
        SendMessageDraft,
        SendRichMessageDraft,
        # Managed bots: a second bot-identity concept, read by nothing else in the world.
        GetManagedBotAccessSettings,
        GetManagedBotToken,
        ReplaceManagedBotToken,
        SetManagedBotAccessSettings,
        # Verification badges. No field surfaces them, so nothing reads them back.
        RemoveChatVerification,
        RemoveUserVerification,
        VerifyChat,
        VerifyUser,
        # Profile and chat media. Media processing is an explicit non-goal; note that
        # *deleting* a chat photo is modeled, because that is a state transition.
        GetUserProfileAudios,
        GetUserProfilePhotos,
        RemoveMyProfilePhoto,
        SetChatPhoto,
        SetMyProfilePhoto,
        # Webhook configuration and polling. The toolkit drives `feed_update` directly
        # and never runs either transport, so there is nothing for these to configure.
        DeleteWebhook,
        GetUpdates,
        GetWebhookInfo,
        SetWebhook,
        # Suggested posts: would need a post lifecycle plus two service messages to mean
        # anything, and the two recorded calls answer today's tests.
        ApproveSuggestedPost,
        DeclineSuggestedPost,
        # Telegram Passport: a pure notification with no reader.
        SetPassportDataErrors,
        # Mini-app and web-app handoffs. The identifiers they exchange have no anchor in
        # the world, so the arguments a test passes are the whole assertion.
        AnswerChatJoinRequestQuery,
        AnswerGuestQuery,
        AnswerWebAppQuery,
        SavePreparedInlineMessage,
        SavePreparedKeyboardButton,
        SendChatJoinRequestWebApp,
        # Sender-chat bans: `getChat` never exposes them, so a ban set would be
        # write-only state.
        BanChatSenderChat,
        UnbanChatSenderChat,
        # Per-sticker attributes and thumbnails: written, never read back.
        SetCustomEmojiStickerSetThumbnail,
        SetStickerEmojiList,
        SetStickerKeywords,
        SetStickerMaskPosition,
        SetStickerPositionInSet,
        SetStickerSetThumbnail,
        # Bot-instance lifecycle. Rejecting calls after a logout is policy.
        Close,
        LogOut,
        # Game scores: a score table nothing else consults.
        GetGameHighScores,
        SetGameScore,
        # Inert reads and settings: a static catalogue, boost counts nothing mutates,
        # and an emoji status no field surfaces.
        GetForumTopicIconStickers,
        GetUserChatBoosts,
        SetUserEmojiStatus,
    },
)


_COPIED_FIELDS = (
    "text",
    "caption",
    "entities",
    "caption_entities",
    "message_thread_id",
)


def models(*method_types: type[TelegramMethod[Any]]) -> Callable[[MethodHandler], MethodHandler]:
    def decorator(handler: MethodHandler) -> MethodHandler:
        for method_type in method_types:
            REGISTRY[method_type] = handler
        return handler

    return decorator


def find_handler(method: TelegramMethod[Any]) -> MethodHandler | None:
    return REGISTRY.get(type(method))


# -- helpers ---------------------------------------------------------------------------


def resolve_chat(env: BotTestEnvironment, chat_id: Any) -> ChatState:
    """
    Resolve a ``chat_id`` (numeric or ``@username``) against the world.

    **A chat this world does not have is a gap in the test's setup, not an API rejection.**
    This is the *outbound* path — the bot calling ``sendMessage``, ``banChatMember``,
    ``getChat`` — and it deliberately does not open a private chat on demand the way the
    actor paths do. A real bot cannot write into a private chat first: it may only answer a
    user who wrote to it, so a test in which the bot's first move is a message to an
    undeclared private chat is describing something Telegram would never let happen, and
    the toolkit has no honest world state to invent for it.

    What it must not do is *look* like Telegram refusing it. Answering "chat not found" as
    a :class:`~aiogram.exceptions.TelegramBadRequest` handed the bot's own ``except``
    branch — almost always the "the user blocked me" branch — a case the test never meant
    to exercise, and the test passed while asserting on the wrong path entirely. So this
    raises :class:`~aiogram.test.WorldLookupError` like every other undeclared thing, and
    the message says which chats exist and how to declare the missing one. A test that
    genuinely wants the real API branch declares it:
    ``env.on(SendMessage).raises(TelegramBadRequest, "Bad Request: chat not found")``
    produces the rejection without pretending the world is short of a chat.
    """
    if isinstance(chat_id, int):
        chat = env.world.chats.get(chat_id)
        if chat is not None:
            return chat
    if isinstance(chat_id, str):
        wanted = chat_id.lstrip("@")
        for chat in env.world.chats.values():
            if chat.username == wanted:
                return chat
    raise WorldLookupError(_undeclared_chat_message(env, chat_id))


def _undeclared_chat_message(env: BotTestEnvironment, chat_id: Any) -> str:
    """Say what this world does have, and how to add the chat the bot asked for."""
    declared = env.world.chats.values()
    if declared:
        listing = "\n".join(f"  {chat.id} ({chat.type}){_chat_label(chat)}" for chat in declared)
        known = f"Declared chats:\n{listing}"
    else:
        known = "This world declares no chats at all."
    user = env.world.users.get(chat_id) if isinstance(chat_id, int) else None
    if user is not None:
        hint = (
            f"\nUser {user.id} is declared, but their private chat with the bot is not. A "
            f"bot cannot write into a private chat first — it may only answer a user who "
            f"wrote to it — so this path does not open one on demand the way a user actor "
            f"does. Declare it with `blueprint.add_private_chat(user)`, open it with "
            f"`env.world.ensure_private_chat({user.id})`, or have the user write first."
        )
    else:
        hint = (
            "\nDeclare it on the blueprint (`add_private_chat`, `add_group`, "
            "`add_supergroup`, `add_channel`), or register a `ChatState` in "
            "`env.world.chats`."
        )
    return (
        f"Chat {chat_id!r} is not declared in the blueprint, so this environment has no "
        f"state to answer for it. {known}{hint}\nTo test how the bot handles the real Bot "
        f"API refusing a chat, declare that refusal instead: "
        f"`env.on(<Method>).raises(TelegramBadRequest, 'Bad Request: chat not found')`."
    )


def _chat_label(chat: ChatState) -> str:
    """The readable half of a chat's identity in a listing, if it has one."""
    for value in (chat.title, chat.username and f"@{chat.username}", chat.first_name):
        if value:
            return f" {value}"
    return ""


def build_message(
    env: BotTestEnvironment,
    method: TelegramMethod[Any],
    chat: ChatState,
    media_field: str | None = None,
) -> Message:
    thread_id = getattr(method, "message_thread_id", None)
    if thread_id is not None and chat.is_forum:
        # An unknown thread id must fail rather than silently produce an untagged message.
        chat.topic(thread_id)
    receiver = _ephemeral_receiver(env, method, chat)
    values: dict[str, Any] = {
        "message_id": 0 if receiver is not None else chat.allocate_message_id(),
        "date": env.world.next_date(),
        "chat": chat.as_chat(),
        "from_user": env.world.bot_user.as_user(),
    }
    connection_id = getattr(method, "business_connection_id", None)
    if connection_id is not None:
        # Telegram sends on behalf of the business account, not the bot.
        connection = env.world.business_connection(connection_id)
        values["from_user"] = env.world.user(connection.user_id).as_user()
        values["sender_business_bot"] = env.world.bot_user.as_user()
        values["business_connection_id"] = connection_id
    for name in _COPIED_FIELDS:
        value = getattr(method, name, None)
        if value is not None:
            values[name] = value

    reply_markup = getattr(method, "reply_markup", None)
    if isinstance(reply_markup, InlineKeyboardMarkup):
        values["reply_markup"] = reply_markup
    if getattr(method, "protect_content", None):
        values["has_protected_content"] = True
    if thread_id is not None and chat.is_forum:
        values["is_topic_message"] = True

    reply_parameters = getattr(method, "reply_parameters", None)
    if reply_parameters is not None and reply_parameters.message_id is not None:
        replied = chat.find_message(reply_parameters.message_id)
        if replied is not None:
            values["reply_to_message"] = replied

    rich_message = getattr(method, "rich_message", None)
    if isinstance(rich_message, InputRichMessage):
        values["rich_message"] = materialize_rich_message(
            rich_message,
            env.synthesis_context(),
        )
    elif media_field is not None:
        values[media_field] = _carry_request_values(
            method,
            nonempty(
                Message.model_fields[media_field].annotation,
                env.synthesis_context(),
                name=media_field,
            ),
        )
        _register_uploaded_content(env, method, media_field, values[media_field])

    if receiver is not None:
        values["ephemeral_message_id"] = chat.allocate_ephemeral_message_id()
        values["receiver_user"] = receiver.as_user()
        return chat.add_ephemeral_message(Message(**values))
    message = Message(**values)
    return chat.add_message(message)


#: How long the Bot API lets an ephemeral message be replied to.
_EPHEMERAL_REPLY_WINDOW = datetime.timedelta(seconds=15)


def _ephemeral_receiver(
    env: BotTestEnvironment,
    method: TelegramMethod[Any],
    chat: ChatState,
) -> UserState | None:
    """
    Check an ephemeral send, returning its receiver, or ``None``.

    Only the rules the Bot API states are enforced. Ephemeral messages
    are group-only per the deprecated ``receiver_user_id`` text, which
    the current parameters no longer repeat; membership of the receiver
    is not a documented condition, so it is not checked.
    """
    parameters = getattr(method, "ephemeral_message_parameters", None)
    reply_parameters = getattr(method, "reply_parameters", None)
    replied_id = None if reply_parameters is None else reply_parameters.ephemeral_message_id
    if parameters is None:
        if replied_id is not None:
            msg = "a reply to an ephemeral message must itself be an ephemeral message"
            raise ApiRejection(msg)
        return None
    if chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
        msg = "ephemeral messages can be sent only to group and supergroup chats"
        raise ApiRejection(msg)
    receiver = env.world.user(parameters.receiver_user_id)
    if replied_id is not None:
        command = chat.find_ephemeral_command(replied_id)
        if command is None:
            raise ApiRejection("message to be replied not found")
        if env.world.now - command.date > _EPHEMERAL_REPLY_WINDOW:
            msg = "an ephemeral message can be replied to within 15 seconds only"
            raise ApiRejection(msg)
    if (
        parameters.replace_callback_query_message
        and parameters.callback_query_id in env.world.ephemeral_callbacks
    ):
        msg = (
            "an ephemeral message can't replace an ephemeral message; "
            "edit it with the editEphemeralMessage methods instead"
        )
        raise ApiRejection(msg)
    return receiver


def _register_uploaded_content(
    env: BotTestEnvironment,
    method: TelegramMethod[Any],
    media_field: str,
    payload: Any,
) -> None:
    """
    Make an upload that carried its own bytes downloadable again.

    Only :class:`~aiogram.types.input_file.BufferedInputFile` is read: it already holds the
    bytes. ``FSInputFile`` and ``URLInputFile`` are deliberately left alone, because a test
    environment must not touch the disk or the network — see design decision D3.
    """
    uploaded = getattr(method, media_field, None)
    if not isinstance(uploaded, BufferedInputFile):
        return
    stored = payload[0] if isinstance(payload, list) and payload else payload
    file_id = getattr(stored, "file_id", None)
    if file_id is not None:
        env.world.files[file_id] = uploaded.data


def _carry_request_values(method: TelegramMethod[Any], payload: Any) -> Any:
    """
    Overwrite a synthesized payload with the values the request actually carried.

    ``sendLocation(latitude=1.0, ...)`` must store *that* latitude, not a synthesized one —
    otherwise the world shows something the bot never did. Fields are matched by name and
    only copied when the payload's annotation accepts the value's type, so a request field
    that happens to share a name with a nested model field (``sendVideo.cover``, a file id,
    against ``Video.cover``, a ``PhotoSize``) is left alone.
    """
    if not isinstance(payload, BaseModel):
        return payload
    carried = {
        name: value
        for name, info in type(payload).model_fields.items()
        if (value := getattr(method, name, None)) is not None
        and annotation_accepts(info.annotation, type(value))
    }
    return payload.model_copy(update=carried) if carried else payload


def resolve_date(value: Any, now: datetime.datetime) -> datetime.datetime | None:
    """
    The moment a Bot API date parameter names, as an aware datetime.

    aiogram accepts a datetime, a duration from now, or a Unix time. A
    naive datetime is read as local time, the way aiogram's own
    serializer reads it.
    """
    if isinstance(value, datetime.datetime):
        if value.tzinfo is None:
            return datetime.datetime.fromtimestamp(value.timestamp(), tz=datetime.timezone.utc)
        return value
    if isinstance(value, datetime.timedelta):
        return now + value
    if isinstance(value, int):
        return datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)
    return None


#: A restriction or ban ending sooner or later than this is "forever".
_UNTIL_RANGE = (datetime.timedelta(seconds=30), datetime.timedelta(days=366))


def normalize_until(value: Any, now: datetime.datetime) -> datetime.datetime | None:
    """
    A restriction or ban's end date, or ``None`` for forever.

    The Bot API reads an ``until_date`` less than 30 seconds or more
    than 366 days from now as forever.
    """
    moment = resolve_date(value, now)
    if moment is None:
        return None
    shortest, longest = _UNTIL_RANGE
    if not shortest <= moment - now <= longest:
        return None
    return moment


#: How long the Bot API lets a business message the bot did not send,
#: and that has no inline keyboard, be edited.
_BUSINESS_EDIT_WINDOW = datetime.timedelta(hours=48)


def _check_business_edit_window(env: BotTestEnvironment, chat: ChatState, message_id: int) -> None:
    message = chat.require_message(message_id)
    if (
        message.business_connection_id is not None
        and message.sender_business_bot is None
        and message.reply_markup is None
        and env.world.now - message.date > _BUSINESS_EDIT_WINDOW
    ):
        raise ApiRejection("message can't be edited")


def _edit_target(env: BotTestEnvironment, method: TelegramMethod[Any]) -> tuple[ChatState, int]:
    if getattr(method, "inline_message_id", None) is not None:
        msg = "inline messages are not modeled by the test environment"
        raise WorldLookupError(msg)
    chat = resolve_chat(env, getattr(method, "chat_id", None))
    message_id: int | None = getattr(method, "message_id", None)
    if message_id is None or chat.find_message(message_id) is None:
        msg = "message to edit not found"
        raise ApiRejection(msg)
    return chat, message_id


# -- sending ---------------------------------------------------------------------------


@models(SendMessage, *MEDIA_FIELDS)
def handle_send(env: BotTestEnvironment, method: TelegramMethod[Any]) -> Message:
    chat = resolve_chat(env, method.chat_id)  # type: ignore[attr-defined]
    return build_message(env, method, chat, MEDIA_FIELDS.get(type(method)))


@models(SendMediaGroup)
def handle_send_media_group(
    env: BotTestEnvironment,
    method: SendMediaGroup,
) -> list[Message]:
    chat = resolve_chat(env, method.chat_id)
    return [build_message(env, method, chat) for _ in method.media]


def forward_origin(source: ChatState, original: Message, sender: User) -> Any:
    """
    Where a forwarded message came from — what tells a forward apart from a copy.

    Every message the world stores carries a sender, so only the channel and user origins
    are reachable; the hidden-user and sender-chat origins wait for the change that makes
    anonymous senders possible.
    """
    if source.type == ChatType.CHANNEL:
        return MessageOriginChannel(
            date=original.date,
            chat=source.as_chat(),
            message_id=original.message_id,
        )
    return MessageOriginUser(date=original.date, sender_user=sender)


def forward_one(
    env: BotTestEnvironment, source: ChatState, target: ChatState, message_id: int
) -> Message:
    original = source.find_message(message_id)
    if original is None:
        raise ApiRejection("message to forward not found")
    return target.add_derived(
        original,
        message_id=target.allocate_message_id(),
        chat=target.as_chat(),
        date=env.world.next_date(),
        from_user=env.world.bot_user.as_user(),
        # Stored messages always carry a sender; the bot stands in only for typing.
        forward_origin=forward_origin(
            source,
            original,
            original.from_user or env.world.bot_user.as_user(),
        ),
    )


@models(ForwardMessage)
def handle_forward(env: BotTestEnvironment, method: ForwardMessage) -> Message:
    source = resolve_chat(env, method.from_chat_id)
    target = resolve_chat(env, method.chat_id)
    return forward_one(env, source, target, method.message_id)


@models(ForwardMessages)
def handle_forward_many(env: BotTestEnvironment, method: ForwardMessages) -> list[MessageId]:
    source = resolve_chat(env, method.from_chat_id)
    target = resolve_chat(env, method.chat_id)
    # Telegram skips what it cannot forward rather than failing the whole batch.
    forwarded = [
        forward_one(env, source, target, message_id)
        for message_id in method.message_ids
        if source.find_message(message_id) is not None
    ]
    return [MessageId(message_id=message.message_id) for message in forwarded]


def copy_one(
    env: BotTestEnvironment,
    source: ChatState,
    target: ChatState,
    message_id: int,
    caption: str | None = None,
) -> Message:
    original = source.find_message(message_id)
    if original is None:
        raise ApiRejection("message to copy not found")
    return target.add_derived(
        original,
        message_id=target.allocate_message_id(),
        chat=target.as_chat(),
        date=env.world.next_date(),
        from_user=env.world.bot_user.as_user(),
        caption=caption if caption is not None else original.caption,
        # A copy carries no trace of where it came from — that is the whole difference.
        forward_origin=None,
    )


@models(CopyMessage)
def handle_copy(env: BotTestEnvironment, method: CopyMessage) -> MessageId:
    source = resolve_chat(env, method.from_chat_id)
    target = resolve_chat(env, method.chat_id)
    copied = copy_one(env, source, target, method.message_id, method.caption)
    return MessageId(message_id=copied.message_id)


@models(CopyMessages)
def handle_copy_many(env: BotTestEnvironment, method: CopyMessages) -> list[MessageId]:
    source = resolve_chat(env, method.from_chat_id)
    target = resolve_chat(env, method.chat_id)
    copied = [
        copy_one(env, source, target, message_id)
        for message_id in method.message_ids
        if source.find_message(message_id) is not None
    ]
    return [MessageId(message_id=message.message_id) for message in copied]


# -- editing ---------------------------------------------------------------------------


def _text_changes(
    env: BotTestEnvironment,
    method: EditMessageText | EditEphemeralMessageText,
) -> dict[str, Any]:
    """
    Replace a message's content with what the request carries.

    Text and rich content are alternatives, so setting one clears the
    other. The reply markup is what the request passes, or none.
    """
    rich_message = None
    if method.rich_message is not None:
        rich_message = materialize_rich_message(
            method.rich_message,
            env.synthesis_context(),
        )
    return {
        "text": method.text,
        "entities": method.entities,
        "rich_message": rich_message,
        "reply_markup": method.reply_markup,
    }


def _caption_changes(
    method: EditMessageCaption | EditEphemeralMessageCaption,
) -> dict[str, Any]:
    return {
        "caption": method.caption,
        "caption_entities": method.caption_entities,
        "reply_markup": method.reply_markup,
    }


@models(EditMessageText)
def handle_edit_text(env: BotTestEnvironment, method: EditMessageText) -> Message:
    chat, message_id = _edit_target(env, method)
    _check_business_edit_window(env, chat, message_id)
    return chat.update_message(message_id, **_text_changes(env, method))


@models(EditMessageCaption)
def handle_edit_caption(env: BotTestEnvironment, method: EditMessageCaption) -> Message:
    chat, message_id = _edit_target(env, method)
    _check_business_edit_window(env, chat, message_id)
    return chat.update_message(message_id, **_caption_changes(method))


@models(EditMessageReplyMarkup)
def handle_edit_reply_markup(
    env: BotTestEnvironment,
    method: EditMessageReplyMarkup,
) -> Message:
    chat, message_id = _edit_target(env, method)
    _check_business_edit_window(env, chat, message_id)
    return chat.update_message(message_id, reply_markup=method.reply_markup)


def media_field(input_media: Any) -> str:
    """
    ``InputMediaLivePhoto`` -> ``live_photo``: the field the edited message will carry.

    Derived from the member's own name rather than a hand-kept table, so a future
    ``InputMedia`` variant needs no change here — see design decision D2. A variant whose
    name does not map is a build break in aiogram's CI, not a silent wrong field.
    """
    stem = type(input_media).__name__.removeprefix("InputMedia")
    field = re.sub(r"(?<!^)(?=[A-Z])", "_", stem).lower()
    if field not in Message.model_fields:
        msg = f"{type(input_media).__name__} does not map to a Message field"
        raise WorldLookupError(msg)
    return field


def _media_changes(
    env: BotTestEnvironment,
    method: EditMessageMedia | EditEphemeralMessageMedia,
) -> dict[str, Any]:
    field = media_field(method.media)
    # A message carries one kind of content: drop whatever it held before.
    changes: dict[str, Any] = dict.fromkeys(EDITABLE_MEDIA_FIELDS)
    changes["text"] = None
    changes["entities"] = None
    changes["rich_message"] = None
    changes[field] = nonempty(
        Message.model_fields[field].annotation,
        env.synthesis_context(),
        name=field,
    )
    changes["caption"] = method.media.caption
    changes["caption_entities"] = method.media.caption_entities
    if method.reply_markup is not None:
        changes["reply_markup"] = method.reply_markup
    return changes


@models(EditMessageMedia)
def handle_edit_media(env: BotTestEnvironment, method: EditMessageMedia) -> Message:
    chat, message_id = _edit_target(env, method)
    _check_business_edit_window(env, chat, message_id)
    return chat.update_message(message_id, **_media_changes(env, method))


# An ephemeral message is addressed by chat, receiver and ephemeral
# id, so these act on the chat's store of the bot's ephemeral
# messages, never on its shared history. Each returns True, as the
# Bot API declares.


@models(EditEphemeralMessageText)
def handle_edit_ephemeral_text(env: BotTestEnvironment, method: EditEphemeralMessageText) -> bool:
    chat = resolve_chat(env, method.chat_id)
    chat.update_ephemeral_message(
        method.receiver_user_id,
        method.ephemeral_message_id,
        **_text_changes(env, method),
    )
    return True


@models(EditEphemeralMessageCaption)
def handle_edit_ephemeral_caption(
    env: BotTestEnvironment,
    method: EditEphemeralMessageCaption,
) -> bool:
    chat = resolve_chat(env, method.chat_id)
    chat.update_ephemeral_message(
        method.receiver_user_id,
        method.ephemeral_message_id,
        **_caption_changes(method),
    )
    return True


@models(EditEphemeralMessageMedia)
def handle_edit_ephemeral_media(
    env: BotTestEnvironment,
    method: EditEphemeralMessageMedia,
) -> bool:
    chat = resolve_chat(env, method.chat_id)
    chat.update_ephemeral_message(
        method.receiver_user_id,
        method.ephemeral_message_id,
        **_media_changes(env, method),
    )
    return True


@models(EditEphemeralMessageReplyMarkup)
def handle_edit_ephemeral_reply_markup(
    env: BotTestEnvironment,
    method: EditEphemeralMessageReplyMarkup,
) -> bool:
    chat = resolve_chat(env, method.chat_id)
    chat.update_ephemeral_message(
        method.receiver_user_id,
        method.ephemeral_message_id,
        reply_markup=method.reply_markup,
    )
    return True


@models(DeleteEphemeralMessage)
def handle_delete_ephemeral(env: BotTestEnvironment, method: DeleteEphemeralMessage) -> bool:
    chat = resolve_chat(env, method.chat_id)
    chat.delete_ephemeral_message(method.receiver_user_id, method.ephemeral_message_id)
    return True


def _location(method: TelegramMethod[Any], live_period: int | None) -> Location:
    return Location(
        latitude=method.latitude,  # type: ignore[attr-defined]
        longitude=method.longitude,  # type: ignore[attr-defined]
        horizontal_accuracy=getattr(method, "horizontal_accuracy", None),
        heading=getattr(method, "heading", None),
        proximity_alert_radius=getattr(method, "proximity_alert_radius", None),
        live_period=live_period,
    )


#: The live period of a location that can be updated forever.
LIVE_FOREVER = 0x7FFFFFFF
_DAY = 86400


@models(EditMessageLiveLocation)
def handle_edit_live_location(
    env: BotTestEnvironment,
    method: EditMessageLiveLocation,
) -> Message:
    chat, message_id = _edit_target(env, method)
    stored = chat.require_message(message_id)
    current = stored.location.live_period if stored.location is not None else None
    now = env.world.now
    if current is None or (
        current != LIVE_FOREVER and now >= stored.date + datetime.timedelta(seconds=current)
    ):
        # Never live, stopped, or past its period: the Bot API allows
        # edits "until its live_period expires" or it is stopped.
        raise ApiRejection("message can't be edited")
    live_period = method.live_period
    if live_period is None:
        # Omitting live_period leaves the existing one running, it does not end it.
        live_period = current
    elif live_period != LIVE_FOREVER:
        ends = stored.date + datetime.timedelta(seconds=live_period)
        if (current != LIVE_FOREVER and live_period > current + _DAY) or (
            ends > now + datetime.timedelta(days=90)
        ):
            msg = (
                "live_period must not exceed the current one by more than a day, "
                "and must end within 90 days"
            )
            raise ApiRejection(msg)
    return chat.update_message(
        message_id,
        location=_location(method, live_period),
        reply_markup=method.reply_markup,
    )


@models(StopMessageLiveLocation)
def handle_stop_live_location(
    env: BotTestEnvironment,
    method: StopMessageLiveLocation,
) -> Message:
    """
    Return the stored message with its live period cleared.

    A location with no live period is no longer live, so a later
    ``editMessageLiveLocation`` is refused, as it is in Telegram.
    """
    chat, message_id = _edit_target(env, method)
    stored = chat.require_message(message_id)
    changes: dict[str, Any] = {"reply_markup": method.reply_markup}
    if stored.location is not None:
        changes["location"] = stored.location.model_copy(update={"live_period": None})
    return chat.update_message(message_id, **changes)


@models(EditMessageChecklist)
def handle_edit_checklist(
    env: BotTestEnvironment,
    method: EditMessageChecklist,
) -> Message:
    chat, message_id = _edit_target(env, method)
    return chat.update_message(
        message_id,
        checklist=nonempty(
            Message.model_fields["checklist"].annotation,
            env.synthesis_context(),
            name="checklist",
        ),
        reply_markup=method.reply_markup,
    )


#: The Bot API's age limits on deletion: a message older than this
#: cannot be deleted, and a dice in a private chat younger than the
#: second cannot.
_DELETABLE_FOR = datetime.timedelta(hours=48)
_PRIVATE_DICE_KEPT_FOR = datetime.timedelta(hours=24)


def _deletable(env: BotTestEnvironment, chat: ChatState, message: Message) -> bool:
    age = env.world.now - message.date
    if age >= _DELETABLE_FOR:
        return False
    return not (
        message.dice is not None
        and chat.type == ChatType.PRIVATE
        and age <= _PRIVATE_DICE_KEPT_FOR
    )


@models(DeleteMessage)
def handle_delete(env: BotTestEnvironment, method: DeleteMessage) -> bool:
    chat = resolve_chat(env, method.chat_id)
    message = chat.find_message(method.message_id)
    if message is None:
        raise ApiRejection("message to delete not found")
    if not _deletable(env, chat, message):
        raise ApiRejection("message can't be deleted")
    chat.delete_message(method.message_id)
    return True


@models(DeleteMessages)
def handle_delete_many(env: BotTestEnvironment, method: DeleteMessages) -> bool:
    """
    Delete the messages that exist and may be deleted, skipping others.

    The Bot API skips messages it cannot find, and points to
    ``deleteMessage`` for the limits; skipping the protected ones too
    is the toolkit's reading of that.
    """
    chat = resolve_chat(env, method.chat_id)
    for message_id in method.message_ids:
        message = chat.find_message(message_id)
        if message is not None and _deletable(env, chat, message):
            chat.delete_message(message_id)
    return True


@models(PinChatMessage)
def handle_pin(env: BotTestEnvironment, method: PinChatMessage) -> bool:
    chat = resolve_chat(env, method.chat_id)
    if method.message_id is None or chat.find_message(method.message_id) is None:
        raise ApiRejection("message to pin not found")
    if method.message_id not in chat.pinned_message_ids:
        chat.pinned_message_ids.append(method.message_id)
    return True


@models(UnpinChatMessage)
def handle_unpin(env: BotTestEnvironment, method: UnpinChatMessage) -> bool:
    chat = resolve_chat(env, method.chat_id)
    if method.message_id is None:
        chat.pinned_message_ids.clear()
    elif method.message_id in chat.pinned_message_ids:
        chat.pinned_message_ids.remove(method.message_id)
    return True


@models(UnpinAllChatMessages)
def handle_unpin_all(env: BotTestEnvironment, method: UnpinAllChatMessages) -> bool:
    resolve_chat(env, method.chat_id).pinned_message_ids.clear()
    return True


# -- seeded answers --------------------------------------------------------------------


@models(SendChatAction)
def handle_send_chat_action(env: BotTestEnvironment, method: SendChatAction) -> bool:
    """No state to mutate, but an unknown chat is still a mistake worth catching."""
    resolve_chat(env, method.chat_id)
    return True


@models(GetFile)
def handle_get_file(env: BotTestEnvironment, method: GetFile) -> File:
    """
    Echo the requested id, and make the path the session can invert back to it.

    ``file_path`` *is* the ``file_id``: the download URL ends with the path, so this is
    what lets :meth:`FakeTelegramSession.stream_content` find the content — see design
    decision D2. This deliberately does not fail for an id with no content, because a bot
    often calls ``getFile`` for the size or path and never downloads.
    """
    synthesized: File = synthesize(File, env.synthesis_context(), name="file")
    content = env.world.files.get(method.file_id)
    return synthesized.model_copy(
        update={
            "file_id": method.file_id,
            "file_path": method.file_id,
            "file_size": len(content) if content is not None else synthesized.file_size,
        },
    )


@models(CreateInvoiceLink)
def handle_create_invoice_link(env: BotTestEnvironment, method: CreateInvoiceLink) -> str:
    return f"https://t.me/invoice/{env.world.next_query_id()}"


@models(GetUserPersonalChatMessages)
def handle_get_user_personal_chat_messages(
    env: BotTestEnvironment,
    method: GetUserPersonalChatMessages,
) -> list[Message]:
    chat = env.world.chats.get(method.user_id)
    if chat is None:
        raise ApiRejection("user has no personal chat")
    return chat.messages[-method.limit :]


# -- membership ------------------------------------------------------------------------


def _not_the_owner(chat: ChatState, user_id: int) -> MemberState:
    """
    The member, provided they are not the chat's owner.

    The one rule ``banChatMember``, ``restrictChatMember`` and ``promoteChatMember`` share:
    a chat owner's standing is not the bot's to take away, and Telegram answers all three
    with the same "can't remove chat owner". Without it the fake was *more* permissive than
    the API it stands in for, and in the direction a test cannot notice — a bot that bans or
    mutes a list of users would quietly kick the owner out here and fail only in production.
    Banning first also used to be a way *around* the promote guard: the ex-owner came back as
    ``KICKED``, which the guard no longer recognised, and could then be promoted at will.
    """
    member = chat.member(user_id)
    if member.status == ChatMemberStatus.CREATOR:
        raise ApiRejection("can't remove chat owner")
    return member


@models(BanChatMember)
def handle_ban(env: BotTestEnvironment, method: BanChatMember) -> bool:
    chat = resolve_chat(env, method.chat_id)
    member = _not_the_owner(chat, method.user_id)
    member.set_status(ChatMemberStatus.KICKED)
    # The Bot API applies `until_date` for supergroups and channels
    # only, so a ban in a basic group has no end, whatever end an
    # earlier restriction had.
    member.until_date = (
        None if chat.type == ChatType.GROUP else normalize_until(method.until_date, env.world.now)
    )
    return True


@models(UnbanChatMember)
def handle_unban(env: BotTestEnvironment, method: UnbanChatMember) -> bool:
    """
    Leave the user free to join, and outside the chat.

    By default the Bot API also removes a user who is a member, so the
    call always ends with the user absent. ``only_if_banned`` limits it
    to a banned user, leaving anyone else as they are.
    """
    chat = resolve_chat(env, method.chat_id)
    member = chat.member(method.user_id)
    if method.only_if_banned and member.status != ChatMemberStatus.KICKED:
        return True
    member.set_status(ChatMemberStatus.LEFT)
    return True


@models(PromoteChatMember)
def handle_promote(env: BotTestEnvironment, method: PromoteChatMember) -> bool:
    """
    Promote or demote a member, persisting exactly the rights the request granted.

    ``promoteChatMember`` sets the *whole* rights mask on every call, so this stores the
    whole mask: a right the request does not pass is not granted, and a later
    ``getChatMember`` reports it as not granted rather than as whatever an earlier
    promotion or a permissive default would have claimed. A request that passes only
    ``can_pin_messages`` therefore produces an administrator who can pin and nothing else.

    The Bot API documents demotion as "pass :code:`False` for all boolean parameters", and
    an omitted parameter is not granted either — so a request in which nothing comes out
    true is a demotion to a plain member. Anything true keeps the member an administrator,
    including ``is_anonymous`` alone: hiding an administrator's presence is a right like
    any other, and reading it as a demotion is what made
    ``promote_chat_member(is_anonymous=True)`` silently strip an admin here before.

    **Demotion drops the custom title with the status**, as the real API does. A title is
    an administrator's: :class:`~aiogram.types.chat_member_administrator.ChatMemberAdministrator`
    and :class:`~aiogram.types.chat_member_owner.ChatMemberOwner` carry ``custom_title`` and
    :class:`~aiogram.types.chat_member_member.ChatMemberMember` has no field for one, so a
    title outliving the status is not something ``getChatMember`` could ever report — it
    could only reappear, ungranted, on a later promotion, which is exactly what it did here.
    ``tag`` is *not* cleared alongside it, and the asymmetry is the models': ``tag`` is a
    field of ``ChatMemberMember`` (and of ``ChatMemberRestricted``) as much as of the
    administrator variants, so it belongs to the membership rather than to the
    administrator status, and a demotion is not the Bot API's way of taking one away.

    The chat's owner is neither promotable nor demotable — see :func:`_not_the_owner`.
    """
    chat = resolve_chat(env, method.chat_id)
    member = _not_the_owner(chat, method.user_id)
    granted = mask(ChatAdministratorRights, method, coerce=True)
    if not any(granted.values()):
        member.set_status(ChatMemberStatus.MEMBER)
        member.rights = None
        member.custom_title = None
        return True
    member.set_status(ChatMemberStatus.ADMINISTRATOR)
    member.rights = ChatAdministratorRights(**granted)
    return True


#: The message kinds that ``can_send_other_messages`` and ``can_add_web_page_previews``
#: bring with them when permissions are not set independently.
_IMPLIED_MESSAGE_PERMISSIONS = (
    "can_send_messages",
    "can_send_audios",
    "can_send_documents",
    "can_send_photos",
    "can_send_videos",
    "can_send_video_notes",
    "can_send_voice_notes",
)

#: Permission -> the permissions granting it also grants, unless the request passed
#: ``use_independent_chat_permissions=True``. Stated by ``restrictChatMember`` and
#: ``setChatPermissions`` in identical words, on that very parameter.
_COUPLED_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "can_send_other_messages": _IMPLIED_MESSAGE_PERMISSIONS,
    "can_add_web_page_previews": _IMPLIED_MESSAGE_PERMISSIONS,
    "can_send_polls": ("can_send_messages",),
}

#: Permission -> the one it copies when the request leaves it unset. Unlike the couplings
#: above, these hold however permissions are set:
#: :class:`~aiogram.types.chat_permissions.ChatPermissions` states them on the fields
#: themselves rather than on the methods, so ``use_independent_chat_permissions`` does not
#: switch them off.
_PERMISSION_DEFAULTS: dict[str, str] = {
    "can_react_to_messages": "can_send_messages",
    "can_edit_tag": "can_pin_messages",
    "can_manage_topics": "can_pin_messages",
}


def granted_permissions(
    permissions: ChatPermissions,
    use_independent_chat_permissions: bool | None,
) -> ChatPermissions:
    """
    What a permissions request actually grants, once the Bot API's couplings are applied.

    ``restrictChatMember`` and ``setChatPermissions`` do not store the mask they are handed.
    Unless the request passes ``use_independent_chat_permissions=True``, granting
    ``can_send_other_messages`` or ``can_add_web_page_previews`` also grants every kind of
    message — a sticker is a message, and Telegram will not let a user send one while
    forbidding text — and granting ``can_send_polls`` grants ``can_send_messages``. A fake
    that stored the raw mask reported a member who may send stickers but not text, a state
    the real API cannot produce, and a bot gating itself on ``can_send_messages`` took the
    wrong branch against it.

    Independently of that switch, three permissions default to another when the request
    leaves them unset — ``can_react_to_messages`` to ``can_send_messages``, ``can_edit_tag``
    and ``can_manage_topics`` to ``can_pin_messages`` — because the Bot API documents those
    defaults on the fields rather than on the methods. They are filled after the couplings,
    so a permission a coupling granted is one they can inherit.

    The result is a fresh object either way, so nothing a caller still holds is mutated, and
    ``model_copy`` rather than a new instance keeps whatever a future Bot API version parked
    in the request's extra fields.
    """
    values = mask(ChatPermissions, permissions)
    if not use_independent_chat_permissions:
        for source, implied in _COUPLED_PERMISSIONS.items():
            if values[source]:
                values.update(dict.fromkeys(implied, True))
    for name, fallback in _PERMISSION_DEFAULTS.items():
        if values[name] is None:
            values[name] = values[fallback]
    return permissions.model_copy(update=values)


@models(RestrictChatMember)
def handle_restrict(env: BotTestEnvironment, method: RestrictChatMember) -> bool:
    """
    Restrict a member, persisting the permissions the request actually grants.

    Which is not always the mask it passed — see :func:`granted_permissions` for the
    couplings ``use_independent_chat_permissions`` switches off. What is stored is a fresh
    object, so nothing the caller holds is in the world. The chat's owner cannot be
    restricted — see :func:`_not_the_owner`.

    Granting every permission lifts a restriction, as the Bot API
    documents: the user becomes a member if present and left otherwise.
    On a user who is not restricted, that is a no-op.
    """
    chat = resolve_chat(env, method.chat_id)
    member = _not_the_owner(chat, method.user_id)
    granted = granted_permissions(
        method.permissions,
        method.use_independent_chat_permissions,
    )
    if all(mask(ChatPermissions, granted, coerce=True).values()):
        if member.status == ChatMemberStatus.RESTRICTED:
            member.set_status(
                ChatMemberStatus.MEMBER if member.is_present else ChatMemberStatus.LEFT,
            )
            member.permissions = None
        return True
    member.set_status(ChatMemberStatus.RESTRICTED)
    member.permissions = granted
    member.rights = None
    member.until_date = normalize_until(method.until_date, env.world.now)
    return True


@models(LeaveChat)
def handle_leave(env: BotTestEnvironment, method: LeaveChat) -> bool:
    chat = resolve_chat(env, method.chat_id)
    chat.member(env.world.bot_user.id).set_status(ChatMemberStatus.LEFT)
    return True


@models(GetChatMember)
def handle_get_chat_member(env: BotTestEnvironment, method: GetChatMember) -> Any:
    chat = resolve_chat(env, method.chat_id)
    user = env.world.user(method.user_id)
    return chat.member(method.user_id).as_chat_member(user.as_user(), chat.type)


@models(GetChat)
def handle_get_chat(env: BotTestEnvironment, method: GetChat) -> ChatFullInfo:
    """
    The chat as the Bot API reports it, carrying copies of what the world stores.

    The permissions and the photo are the chat's own objects, and a result is mounted to
    the calling bot — so handing them out directly would bind the world's state and leave
    ``chat.permissions == DECLARED`` failing with two identical-looking sides. Only value
    objects are copied; a message the world holds is deliberately shared.
    """
    chat = resolve_chat(env, method.chat_id)
    template: ChatFullInfo = synthesize(ChatFullInfo, env.synthesis_context(), name="chat")
    updated: ChatFullInfo = template.model_copy(
        update={
            "id": chat.id,
            "type": chat.type,
            "title": chat.title,
            "username": chat.username,
            "first_name": chat.first_name,
            "last_name": chat.last_name,
            "is_forum": chat.is_forum or None,
            "description": chat.description,
            "permissions": detached_copy(chat.permissions),
            "photo": detached_copy(chat.photo),
            "sticker_set_name": chat.sticker_set_name,
            "invite_link": (
                chat.primary_invite_link.invite_link
                if chat.primary_invite_link is not None
                else None
            ),
            "community": (
                env.world.community(chat.community_id).as_community()
                if chat.community_id is not None
                else None
            ),
        },
    )
    return updated


@models(GetMe)
def handle_get_me(env: BotTestEnvironment, method: GetMe) -> User:
    return env.world.bot_user.as_user()


# -- sticker sets ----------------------------------------------------------------------


def _sticker_from_input(env: BotTestEnvironment, sticker: InputSticker) -> Sticker:
    """
    Build the stored sticker for an `InputSticker`.

    A ``str`` input is a file id the caller already holds — from `uploadStickerFile`, or
    from a sticker it received — so it is used as-is. Anything else is an upload, which
    gets a minted id; no image data exists either way (design decision D4).
    """
    file_id = sticker.sticker if isinstance(sticker.sticker, str) else _next_sticker_file_id(env)
    return Sticker(
        file_id=file_id,
        file_unique_id=f"{file_id}-unique",
        type="regular",
        width=512,
        height=512,
        is_animated=False,
        is_video=False,
        emoji=sticker.emoji_list[0] if sticker.emoji_list else None,
    )


def _next_sticker_file_id(env: BotTestEnvironment) -> str:
    return f"sticker-{env.world.next_query_id()}"


@models(CreateNewStickerSet)
def handle_create_sticker_set(env: BotTestEnvironment, method: CreateNewStickerSet) -> bool:
    if method.name in env.world.sticker_sets:
        msg = f"Sticker set name {method.name!r} is already occupied"
        raise ApiRejection(msg)
    env.world.sticker_sets[method.name] = StickerSetState(
        name=method.name,
        title=method.title,
        sticker_type=method.sticker_type or "regular",
        stickers=[_sticker_from_input(env, item) for item in method.stickers],
    )
    return True


@models(GetStickerSet)
def handle_get_sticker_set(env: BotTestEnvironment, method: GetStickerSet) -> StickerSet:
    return env.world.sticker_set(method.name).as_sticker_set()


@models(AddStickerToSet)
def handle_add_sticker_to_set(env: BotTestEnvironment, method: AddStickerToSet) -> bool:
    sticker_set = env.world.sticker_set(method.name)
    sticker_set.stickers.append(_sticker_from_input(env, method.sticker))
    return True


@models(DeleteStickerFromSet)
def handle_delete_sticker_from_set(
    env: BotTestEnvironment,
    method: DeleteStickerFromSet,
) -> bool:
    """The method names no set, so the sticker has to identify one."""
    sticker_set = env.world.sticker_set_containing(method.sticker)
    del sticker_set.stickers[sticker_set.index_of(method.sticker)]
    return True


@models(ReplaceStickerInSet)
def handle_replace_sticker_in_set(env: BotTestEnvironment, method: ReplaceStickerInSet) -> bool:
    """Delete then add at the same position, which is how the Bot API describes it."""
    sticker_set = env.world.sticker_set(method.name)
    position = sticker_set.index_of(method.old_sticker)
    sticker_set.stickers[position] = _sticker_from_input(env, method.sticker)
    return True


@models(SetStickerSetTitle)
def handle_set_sticker_set_title(env: BotTestEnvironment, method: SetStickerSetTitle) -> bool:
    env.world.sticker_set(method.name).title = method.title
    return True


@models(DeleteStickerSet)
def handle_delete_sticker_set(env: BotTestEnvironment, method: DeleteStickerSet) -> bool:
    env.world.sticker_set(method.name)
    del env.world.sticker_sets[method.name]
    return True


@models(UploadStickerFile)
def handle_upload_sticker_file(env: BotTestEnvironment, method: UploadStickerFile) -> File:
    """
    Mint a stable id the set methods can reference, registering no content.

    Deliberately unlike a document upload, which *does* register its bytes: a bot uploads a
    sticker to put it in a pack and never downloads it back (design decision D4).
    """
    file_id = _next_sticker_file_id(env)
    synthesized: File = synthesize(File, env.synthesis_context(), name="file")
    return synthesized.model_copy(update={"file_id": file_id, "file_path": file_id})


@models(GetCustomEmojiStickers)
def handle_get_custom_emoji_stickers(
    env: BotTestEnvironment,
    method: GetCustomEmojiStickers,
) -> list[Sticker]:
    """One sticker per requested id, echoing it, so a lookup can be correlated."""
    return [
        Sticker(
            file_id=custom_emoji_id,
            file_unique_id=f"{custom_emoji_id}-unique",
            type="custom_emoji",
            width=100,
            height=100,
            is_animated=False,
            is_video=False,
            custom_emoji_id=custom_emoji_id,
        )
        for custom_emoji_id in method.custom_emoji_ids
    ]


# -- stars and gifts -------------------------------------------------------------------

#: A small, fixed catalogue of gifts a test can pick from deterministically.
#:
#: Hard-coded rather than synthesized because ``gifts[0].id`` is the first thing any gift
#: test reads, and synthesis would make it differ between runs — see design decision D5.
#: These identifiers are invented; they are not real Telegram gifts.
GIFT_CATALOGUE: tuple[tuple[str, int], ...] = (
    ("gift-star", 15),
    ("gift-heart", 50),
    ("gift-cake", 100),
)


def _catalogue_sticker(gift_id: str) -> Sticker:
    return Sticker(
        file_id=f"{gift_id}-sticker",
        file_unique_id=f"{gift_id}-unique",
        type="regular",
        width=100,
        height=100,
        is_animated=False,
        is_video=False,
    )


def gift_catalogue() -> list[Gift]:
    """The gifts `getAvailableGifts` offers, stable across calls and environments."""
    return [
        Gift(id=gift_id, sticker=_catalogue_sticker(gift_id), star_count=star_count)
        for gift_id, star_count in GIFT_CATALOGUE
    ]


def _gift_cost(gift_id: str) -> int:
    for known_id, star_count in GIFT_CATALOGUE:
        if known_id == gift_id:
            return star_count
    known = ", ".join(repr(known_id) for known_id, _ in GIFT_CATALOGUE)
    msg = (
        f"Gift {gift_id!r} is not in this environment's gift catalogue. The fake offers "
        f"{known}; `getAvailableGifts` returns exactly those, so a handler that picks a "
        f"gift from it works, and a hard-coded real gift id has to be overridden with "
        f"`env.on(SendGift)`."
    )
    raise WorldLookupError(msg)


def _owned_gift_result(env: BotTestEnvironment, gift: OwnedGiftState) -> Any:
    """A stored gift as the Bot API's owned-gift union member."""
    catalogue_gift = Gift(
        id=gift.gift_id,
        sticker=_catalogue_sticker(gift.gift_id),
        star_count=gift.star_count,
    )
    # The Bot API carries `send_date` as a unix timestamp, while the world keeps datetimes.
    send_date = int(gift.send_date.timestamp())
    if gift.is_unique:
        unique: UniqueGift = synthesize(UniqueGift, env.synthesis_context(), name="gift")
        return OwnedGiftUnique(
            gift=unique.model_copy(update={"gift_id": gift.gift_id}),
            send_date=send_date,
            owned_gift_id=gift.owned_gift_id,
        )
    return OwnedGiftRegular(
        gift=catalogue_gift,
        send_date=send_date,
        owned_gift_id=gift.owned_gift_id,
        convert_star_count=gift.star_count,
    )


def _owned_gifts_result(env: BotTestEnvironment, owner_id: int) -> OwnedGifts:
    gifts = env.world.gifts_of(owner_id)
    return OwnedGifts(
        total_count=len(gifts),
        gifts=[_owned_gift_result(env, gift) for gift in gifts],
    )


def _spend(env: BotTestEnvironment, amount: int, charge_id: str | None = None) -> None:
    """
    Debit the ledger.

    Affordability is deliberately not checked: a negative balance is visible to a test,
    whereas a silent rejection is not — see design decision D6.
    """
    env.world.stars.record(
        env.world.next_query_id(),
        -amount,
        env.world.next_date(),
        charge_id=charge_id,
    )


@models(GetMyStarBalance)
def handle_get_star_balance(env: BotTestEnvironment, method: GetMyStarBalance) -> StarAmount:
    return StarAmount(amount=env.world.stars.balance)


@models(GetStarTransactions)
def handle_get_star_transactions(
    env: BotTestEnvironment,
    method: GetStarTransactions,
) -> StarTransactions:
    """Every recorded transaction; `offset` and `limit` are not modeled (design open question)."""
    return StarTransactions(
        transactions=[item.as_star_transaction() for item in env.world.stars.transactions],
    )


@models(RefundStarPayment)
def handle_refund_star_payment(env: BotTestEnvironment, method: RefundStarPayment) -> bool:
    charge = env.world.stars.charge(method.telegram_payment_charge_id)
    if charge.is_refunded:
        msg = f"Charge {charge.id!r} has already been refunded"
        raise ApiRejection(msg)
    charge.is_refunded = True
    _spend(env, charge.amount, charge_id=charge.id)
    return True


@models(EditUserStarSubscription)
def handle_edit_star_subscription(
    env: BotTestEnvironment,
    method: EditUserStarSubscription,
) -> bool:
    charge = env.world.stars.charge(method.telegram_payment_charge_id)
    charge.is_subscription_canceled = bool(method.is_canceled)
    return True


@models(GetAvailableGifts)
def handle_get_available_gifts(env: BotTestEnvironment, method: GetAvailableGifts) -> Gifts:
    return Gifts(gifts=gift_catalogue())


@models(SendGift)
def handle_send_gift(env: BotTestEnvironment, method: SendGift) -> bool:
    owner_id = method.user_id if method.user_id is not None else method.chat_id
    if owner_id is None:
        msg = "sendGift needs a user_id or a chat_id"
        raise ApiRejection(msg)
    cost = _gift_cost(method.gift_id)
    owned_gift_id = env.world.next_query_id()
    env.world.owned_gifts[owned_gift_id] = OwnedGiftState(
        owned_gift_id=owned_gift_id,
        gift_id=method.gift_id,
        owner_id=int(owner_id),
        star_count=cost,
        send_date=env.world.next_date(),
    )
    _spend(env, cost)
    return True


@models(GetUserGifts)
def handle_get_user_gifts(env: BotTestEnvironment, method: GetUserGifts) -> OwnedGifts:
    return _owned_gifts_result(env, method.user_id)


@models(GetChatGifts)
def handle_get_chat_gifts(env: BotTestEnvironment, method: GetChatGifts) -> OwnedGifts:
    return _owned_gifts_result(env, resolve_chat(env, method.chat_id).id)


@models(GetBusinessAccountGifts)
def handle_get_business_account_gifts(
    env: BotTestEnvironment,
    method: GetBusinessAccountGifts,
) -> OwnedGifts:
    connection = env.world.business_connection(method.business_connection_id)
    return _owned_gifts_result(env, connection.user_id)


@models(ConvertGiftToStars)
def handle_convert_gift_to_stars(env: BotTestEnvironment, method: ConvertGiftToStars) -> bool:
    gift = env.world.owned_gift(method.owned_gift_id)
    del env.world.owned_gifts[gift.owned_gift_id]
    env.world.stars.record(env.world.next_query_id(), gift.star_count, env.world.next_date())
    return True


@models(UpgradeGift)
def handle_upgrade_gift(env: BotTestEnvironment, method: UpgradeGift) -> bool:
    gift = env.world.owned_gift(method.owned_gift_id)
    gift.is_unique = True
    if method.star_count:
        _spend(env, method.star_count)
    return True


@models(TransferGift)
def handle_transfer_gift(env: BotTestEnvironment, method: TransferGift) -> bool:
    gift = env.world.owned_gift(method.owned_gift_id)
    gift.owner_id = method.new_owner_chat_id
    if method.star_count:
        _spend(env, method.star_count)
    return True


@models(GiftPremiumSubscription)
def handle_gift_premium_subscription(
    env: BotTestEnvironment,
    method: GiftPremiumSubscription,
) -> bool:
    _spend(env, method.star_count)
    return True


@models(GetBusinessAccountStarBalance)
def handle_business_star_balance(
    env: BotTestEnvironment,
    method: GetBusinessAccountStarBalance,
) -> StarAmount:
    env.world.business_connection(method.business_connection_id)
    return StarAmount(amount=env.world.stars.balance)


@models(TransferBusinessAccountStars)
def handle_transfer_business_stars(
    env: BotTestEnvironment,
    method: TransferBusinessAccountStars,
) -> bool:
    env.world.business_connection(method.business_connection_id)
    _spend(env, method.star_count)
    return True


# -- invite links ----------------------------------------------------------------------

#: The Bot API states this as a fixed value, not a range — see design decision D5.
SUBSCRIPTION_PERIOD = 2592000


def _as_seconds(value: Any) -> int | None:
    """A subscription period in seconds — aiogram accepts a timedelta as a convenience."""
    if isinstance(value, datetime.timedelta):
        return int(value.total_seconds())
    if isinstance(value, int):
        return value
    return None


def _next_invite_link(env: BotTestEnvironment) -> str:
    """Deterministic and unique, so a test can correlate a link across calls."""
    return f"https://t.me/+{env.world.next_query_id()}"


def _invite_link_result(env: BotTestEnvironment, link: InviteLinkState) -> ChatInviteLink:
    return link.as_chat_invite_link(env.world.user(link.creator_id).as_user())


@models(CreateChatInviteLink)
def handle_create_invite_link(
    env: BotTestEnvironment,
    method: CreateChatInviteLink,
) -> ChatInviteLink:
    chat = resolve_chat(env, method.chat_id)
    link = InviteLinkState(
        invite_link=_next_invite_link(env),
        creator_id=env.world.bot_user.id,
        name=method.name,
        expire_date=resolve_date(method.expire_date, env.world.now),
        member_limit=method.member_limit,
        creates_join_request=bool(method.creates_join_request),
    )
    chat.invite_links.append(link)
    return _invite_link_result(env, link)


@models(CreateChatSubscriptionInviteLink)
def handle_create_subscription_invite_link(
    env: BotTestEnvironment,
    method: CreateChatSubscriptionInviteLink,
) -> ChatInviteLink:
    chat = resolve_chat(env, method.chat_id)
    seconds = _as_seconds(method.subscription_period)
    if seconds != SUBSCRIPTION_PERIOD:
        msg = f"subscription period must be {SUBSCRIPTION_PERIOD}"
        raise ApiRejection(msg)
    link = InviteLinkState(
        invite_link=_next_invite_link(env),
        creator_id=env.world.bot_user.id,
        name=method.name,
        subscription_period=seconds,
        subscription_price=method.subscription_price,
        creates_join_request=False,
    )
    chat.invite_links.append(link)
    return _invite_link_result(env, link)


@models(EditChatInviteLink)
def handle_edit_invite_link(
    env: BotTestEnvironment,
    method: EditChatInviteLink,
) -> ChatInviteLink:
    """Mutates and returns the *stored* link, so a created link can be correlated."""
    link = resolve_chat(env, method.chat_id).invite_link(method.invite_link)
    link.name = method.name
    link.expire_date = resolve_date(method.expire_date, env.world.now)
    link.member_limit = method.member_limit
    link.creates_join_request = bool(method.creates_join_request)
    return _invite_link_result(env, link)


@models(EditChatSubscriptionInviteLink)
def handle_edit_subscription_invite_link(
    env: BotTestEnvironment,
    method: EditChatSubscriptionInviteLink,
) -> ChatInviteLink:
    """Only the name is editable; the subscription terms survive untouched."""
    link = resolve_chat(env, method.chat_id).invite_link(method.invite_link)
    if link.subscription_period is None:
        msg = "the link is not a subscription invite link"
        raise ApiRejection(msg)
    link.name = method.name
    return _invite_link_result(env, link)


@models(RevokeChatInviteLink)
def handle_revoke_invite_link(
    env: BotTestEnvironment,
    method: RevokeChatInviteLink,
) -> ChatInviteLink:
    chat = resolve_chat(env, method.chat_id)
    link = chat.invite_link(method.invite_link)
    was_primary = link.is_primary and not link.is_revoked
    link.is_revoked = True
    if was_primary:
        # Telegram generates a replacement when the primary link is revoked.
        chat.replace_primary_invite_link(_next_invite_link(env), env.world.bot_user.id)
    return _invite_link_result(env, link)


@models(ExportChatInviteLink)
def handle_export_invite_link(env: BotTestEnvironment, method: ExportChatInviteLink) -> str:
    chat = resolve_chat(env, method.chat_id)
    link = chat.replace_primary_invite_link(_next_invite_link(env), env.world.bot_user.id)
    return link.invite_link


# -- chat administration ---------------------------------------------------------------


def _administrable(env: BotTestEnvironment, method: TelegramMethod[Any]) -> ChatState:
    """Resolve a chat that can be administered — a private chat cannot."""
    chat = resolve_chat(env, method.chat_id)  # type: ignore[attr-defined]
    if chat.type == ChatType.PRIVATE:
        msg = "method is available for supergroup and channel chats only"
        raise ApiRejection(msg)
    return chat


@models(SetChatTitle)
def handle_set_chat_title(env: BotTestEnvironment, method: SetChatTitle) -> bool:
    chat = _administrable(env, method)
    chat.title = method.title
    service_message(env, chat, {"new_chat_title": method.title})
    return True


@models(SetChatDescription)
def handle_set_chat_description(env: BotTestEnvironment, method: SetChatDescription) -> bool:
    _administrable(env, method).description = method.description
    return True


@models(SetChatPermissions)
def handle_set_chat_permissions(env: BotTestEnvironment, method: SetChatPermissions) -> bool:
    """
    Stored, never enforced: the fake models the shape of administration, not its policy.

    What is stored is what the request grants rather than the mask it passed — the same
    couplings ``restrictChatMember`` applies, documented on this method in identical words;
    see :func:`granted_permissions`. It is a fresh object for the reason
    :func:`handle_restrict` gives: what a later ``getChat`` hands back — and mounts to the
    calling bot — must not be the caller's own object.
    """
    _administrable(env, method).permissions = granted_permissions(
        method.permissions,
        method.use_independent_chat_permissions,
    )
    return True


@models(SetChatStickerSet)
def handle_set_chat_sticker_set(env: BotTestEnvironment, method: SetChatStickerSet) -> bool:
    _administrable(env, method).sticker_set_name = method.sticker_set_name
    return True


@models(DeleteChatStickerSet)
def handle_delete_chat_sticker_set(env: BotTestEnvironment, method: DeleteChatStickerSet) -> bool:
    _administrable(env, method).sticker_set_name = None
    return True


@models(DeleteChatPhoto)
def handle_delete_chat_photo(env: BotTestEnvironment, method: DeleteChatPhoto) -> bool:
    chat = _administrable(env, method)
    chat.photo = None
    service_message(env, chat, {"delete_chat_photo": True})
    return True


@models(GetChatMemberCount)
def handle_get_chat_member_count(env: BotTestEnvironment, method: GetChatMemberCount) -> int:
    chat = resolve_chat(env, method.chat_id)
    return len(chat.present_members())


@models(GetChatAdministrators)
def handle_get_chat_administrators(
    env: BotTestEnvironment,
    method: GetChatAdministrators,
) -> list[Any]:
    """
    The chat's administrators, creator first.

    Telegram omits bots other than the caller unless ``return_bots`` is passed — modeling
    that keeps a test with a second bot in the chat honest (design decision D6).
    """
    chat = resolve_chat(env, method.chat_id)
    admins = [
        member
        for member in chat.members.values()
        if member.status in {ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR}
    ]
    if not method.return_bots:
        admins = [
            member
            for member in admins
            if member.user_id == env.world.bot_user.id or not env.world.user(member.user_id).is_bot
        ]
    # Creator first, then a stable order, so a test indexing [0] is not flaky.
    admins.sort(key=lambda member: (member.status != ChatMemberStatus.CREATOR, member.user_id))
    return [
        member.as_chat_member(env.world.user(member.user_id).as_user(), chat.type)
        for member in admins
    ]


def _annotated_member(
    env: BotTestEnvironment,
    method: TelegramMethod[Any],
    allowed: set[str],
    complaint: str,
) -> MemberState:
    chat = resolve_chat(env, method.chat_id)  # type: ignore[attr-defined]
    user_id: int = method.user_id  # type: ignore[attr-defined]
    env.world.user(user_id)
    member = chat.member(user_id)
    if member.status not in allowed:
        raise ApiRejection(complaint)
    return member


@models(SetChatAdministratorCustomTitle)
def handle_set_custom_title(
    env: BotTestEnvironment,
    method: SetChatAdministratorCustomTitle,
) -> bool:
    member = _annotated_member(
        env,
        method,
        {ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR},
        "user is not an administrator",
    )
    member.custom_title = method.custom_title
    return True


@models(SetChatMemberTag)
def handle_set_member_tag(env: BotTestEnvironment, method: SetChatMemberTag) -> bool:
    """A tag belongs to a regular member; an administrator carries a custom title instead."""
    member = _annotated_member(
        env,
        method,
        {ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED},
        "user is not a regular member",
    )
    member.tag = method.tag
    return True


# -- the bot's own profile -------------------------------------------------------------


@models(SetMyCommands)
def handle_set_my_commands(env: BotTestEnvironment, method: SetMyCommands) -> bool:
    key = scope_key(method.scope, method.language_code)
    env.world.profile.commands[key] = list(method.commands)
    return True


@models(GetMyCommands)
def handle_get_my_commands(env: BotTestEnvironment, method: GetMyCommands) -> list[BotCommand]:
    """
    Exactly what was set for this scope and language, or nothing.

    The Bot API does not fall back to a broader scope here — see design decision D2. The
    commands come back as copies, for the reason :func:`handle_get_chat` gives.
    """
    key = scope_key(method.scope, method.language_code)
    return detached_copy(env.world.profile.commands.get(key, []))  # type: ignore[no-any-return]


@models(DeleteMyCommands)
def handle_delete_my_commands(env: BotTestEnvironment, method: DeleteMyCommands) -> bool:
    env.world.profile.commands.pop(scope_key(method.scope, method.language_code), None)
    return True


@models(SetMyName)
def handle_set_my_name(env: BotTestEnvironment, method: SetMyName) -> bool:
    profile = env.world.profile
    profile.set_localized(profile.name, method.language_code, method.name)
    return True


@models(GetMyName)
def handle_get_my_name(env: BotTestEnvironment, method: GetMyName) -> BotName:
    profile = env.world.profile
    name = profile.localized(profile.name, method.language_code)
    return BotName(name=name if name is not None else env.world.bot_user.first_name)


@models(SetMyDescription)
def handle_set_my_description(env: BotTestEnvironment, method: SetMyDescription) -> bool:
    profile = env.world.profile
    profile.set_localized(profile.description, method.language_code, method.description)
    return True


@models(GetMyDescription)
def handle_get_my_description(
    env: BotTestEnvironment,
    method: GetMyDescription,
) -> BotDescription:
    profile = env.world.profile
    return BotDescription(
        description=profile.localized(profile.description, method.language_code) or ""
    )


@models(SetMyShortDescription)
def handle_set_my_short_description(
    env: BotTestEnvironment,
    method: SetMyShortDescription,
) -> bool:
    profile = env.world.profile
    profile.set_localized(
        profile.short_description,
        method.language_code,
        method.short_description,
    )
    return True


@models(GetMyShortDescription)
def handle_get_my_short_description(
    env: BotTestEnvironment,
    method: GetMyShortDescription,
) -> BotShortDescription:
    profile = env.world.profile
    text = profile.localized(profile.short_description, method.language_code)
    return BotShortDescription(short_description=text or "")


@models(SetMyDefaultAdministratorRights)
def handle_set_default_admin_rights(
    env: BotTestEnvironment,
    method: SetMyDefaultAdministratorRights,
) -> bool:
    rights = env.world.profile.default_admin_rights
    scope = bool(method.for_channels)
    if method.rights is None:
        # Omitting the rights clears them, as the Bot API documents.
        rights.pop(scope, None)
    else:
        rights[scope] = method.rights
    return True


@models(GetMyDefaultAdministratorRights)
def handle_get_default_admin_rights(
    env: BotTestEnvironment,
    method: GetMyDefaultAdministratorRights,
) -> ChatAdministratorRights:
    stored = env.world.profile.default_admin_rights.get(bool(method.for_channels))
    if stored is not None:
        return detached_copy(stored)  # type: ignore[no-any-return]
    return no_administrator_rights()


@models(SetChatMenuButton)
def handle_set_chat_menu_button(env: BotTestEnvironment, method: SetChatMenuButton) -> bool:
    if method.chat_id is not None:
        resolve_chat(env, method.chat_id)
    button = method.menu_button if method.menu_button is not None else MenuButtonDefault()
    env.world.profile.menu_buttons[method.chat_id] = button
    return True


@models(GetChatMenuButton)
def handle_get_chat_menu_button(env: BotTestEnvironment, method: GetChatMenuButton) -> Any:
    """A chat with no dedicated button reports the default one."""
    buttons = env.world.profile.menu_buttons
    if method.chat_id is not None:
        resolve_chat(env, method.chat_id)
    stored = buttons.get(method.chat_id, buttons.get(None))
    return MenuButtonDefault() if stored is None else detached_copy(stored)


# -- polls -----------------------------------------------------------------------------


#: How far ahead a poll may be scheduled to close, in seconds.
_POLL_SCHEDULE_RANGE = (5, 2628000)


def _poll_close(env: BotTestEnvironment, method: SendPoll) -> datetime.datetime | None:
    """When a poll closes by itself, validated as the Bot API states."""
    if method.open_period is not None and method.close_date is not None:
        msg = "open_period and close_date can't be used together"
        raise ApiRejection(msg)
    now = env.world.now
    moment: datetime.datetime | None
    if method.open_period is not None:
        moment = now + datetime.timedelta(seconds=method.open_period)
    else:
        moment = resolve_date(method.close_date, now)
    if moment is None:
        return None
    shortest, longest = _POLL_SCHEDULE_RANGE
    if not shortest <= (moment - now).total_seconds() <= longest:
        msg = f"a poll must close {shortest} to {longest} seconds from now"
        raise ApiRejection(msg)
    return moment


def _close_poll(chat: ChatState, message_id: int, poll: PollState) -> Poll:
    poll.is_closed = True
    chat.update_message(message_id, poll=poll.as_poll())
    return poll.as_poll()


@models(SendPoll)
def handle_send_poll(env: BotTestEnvironment, method: SendPoll) -> Message:
    chat = resolve_chat(env, method.chat_id)
    close_at = _poll_close(env, method)
    poll = PollState(
        id=env.world.next_query_id(),
        question=method.question,
        options=[option if isinstance(option, str) else option.text for option in method.options],
        is_anonymous=True if method.is_anonymous is None else method.is_anonymous,
        type=method.type or "regular",
        allows_multiple_answers=bool(method.allows_multiple_answers),
        allows_revoting=bool(method.allows_revoting),
        members_only=bool(method.members_only),
        correct_option_id=method.correct_option_id,
        explanation=method.explanation,
        is_closed=bool(method.is_closed),
        open_period=method.open_period,
        close_date=close_at,
    )
    env.world.polls[poll.id] = poll
    message = build_message(env, method, chat)
    if close_at is not None and not poll.is_closed:
        message_id = message.message_id

        async def close() -> None:
            # A poll stopped before its moment does not close twice.
            if poll.is_closed or chat.find_message(message_id) is None:
                return
            closed = _close_poll(chat, message_id, poll)
            await env.feed(Update(update_id=env.world.next_update_id(), poll=closed))

        env.schedule(close_at, close)
    return chat.update_message(message.message_id, poll=poll.as_poll())


@models(StopPoll)
def handle_stop_poll(env: BotTestEnvironment, method: StopPoll) -> Poll:
    chat, message_id = _edit_target(env, method)
    stored = chat.require_message(message_id)
    if stored.poll is None:
        msg = "message doesn't contain a poll"
        raise ApiRejection(msg)
    poll = env.world.poll(stored.poll.id)
    if poll.is_closed:
        msg = "poll has already been closed"
        raise ApiRejection(msg)
    return _close_poll(chat, message_id, poll)


# -- reactions -------------------------------------------------------------------------


def _reaction_target(
    env: BotTestEnvironment, method: TelegramMethod[Any]
) -> tuple[ChatState, int]:
    chat = resolve_chat(env, method.chat_id)  # type: ignore[attr-defined]
    message_id: int = method.message_id  # type: ignore[attr-defined]
    if chat.find_message(message_id) is None:
        msg = "message to react to not found"
        raise ApiRejection(msg)
    return chat, message_id


@models(SetMessageReaction)
def handle_set_message_reaction(env: BotTestEnvironment, method: SetMessageReaction) -> bool:
    """The bot's own reactions on one message."""
    chat, message_id = _reaction_target(env, method)
    chat.set_reaction(message_id, env.world.bot_user.id, list(method.reaction or []))
    return True


@models(DeleteMessageReaction)
def handle_delete_message_reaction(
    env: BotTestEnvironment,
    method: DeleteMessageReaction,
) -> bool:
    """Moderation: one named actor's reaction off one message."""
    chat, message_id = _reaction_target(env, method)
    actor_id = method.user_id if method.user_id is not None else method.actor_chat_id
    if actor_id is not None:
        chat.set_reaction(message_id, actor_id, [])
    return True


@models(DeleteAllMessageReactions)
def handle_delete_all_message_reactions(
    env: BotTestEnvironment,
    method: DeleteAllMessageReactions,
) -> bool:
    """
    Moderation: one named actor's reactions across the whole chat.

    Note there is no ``message_id`` — despite the name, this does not clear a message.
    """
    chat = resolve_chat(env, method.chat_id)
    actor_id = method.user_id if method.user_id is not None else method.actor_chat_id
    if actor_id is not None:
        for message_id in list(chat.reactions):
            chat.set_reaction(message_id, actor_id, [])
    return True


# -- join requests ---------------------------------------------------------------------


def _pending_request(env: BotTestEnvironment, method: TelegramMethod[Any]) -> ChatState:
    chat = resolve_chat(env, method.chat_id)  # type: ignore[attr-defined]
    user_id: int = method.user_id  # type: ignore[attr-defined]
    if user_id not in chat.join_requests:
        msg = "USER_ALREADY_PARTICIPANT: no join request is pending for this user"
        raise ApiRejection(msg)
    chat.join_requests.discard(user_id)
    return chat


@models(ApproveChatJoinRequest)
def handle_approve_join_request(
    env: BotTestEnvironment,
    method: ApproveChatJoinRequest,
) -> bool:
    chat = _pending_request(env, method)
    chat.member(method.user_id).set_status(ChatMemberStatus.MEMBER)
    return True


@models(DeclineChatJoinRequest)
def handle_decline_join_request(
    env: BotTestEnvironment,
    method: DeclineChatJoinRequest,
) -> bool:
    """Clearing the request without adding the member is the whole difference."""
    _pending_request(env, method)
    return True


# -- answering queries -----------------------------------------------------------------


@models(AnswerCallbackQuery)
def handle_answer_callback_query(
    env: BotTestEnvironment,
    method: AnswerCallbackQuery,
) -> bool:
    env.world.answer_query(QueryKind.CALLBACK, method.callback_query_id)
    return True


@models(AnswerInlineQuery)
def handle_answer_inline_query(env: BotTestEnvironment, method: AnswerInlineQuery) -> bool:
    env.world.answer_query(QueryKind.INLINE, method.inline_query_id)
    return True


@models(AnswerShippingQuery)
def handle_answer_shipping_query(env: BotTestEnvironment, method: AnswerShippingQuery) -> bool:
    env.world.answer_query(QueryKind.SHIPPING, method.shipping_query_id)
    return True


@models(AnswerPreCheckoutQuery)
def handle_answer_pre_checkout_query(
    env: BotTestEnvironment,
    method: AnswerPreCheckoutQuery,
) -> bool:
    env.world.answer_query(QueryKind.PRE_CHECKOUT, method.pre_checkout_query_id)
    return True


# -- forum topics ----------------------------------------------------------------------


def service_message(
    env: BotTestEnvironment,
    chat: ChatState,
    fields: dict[str, Any],
    thread_id: int | None = None,
) -> Message:
    """Emit a service message the way Telegram posts one for an administrative action."""
    values: dict[str, Any] = {
        "message_id": chat.allocate_message_id(),
        "date": env.world.next_date(),
        "chat": chat.as_chat(),
        "from_user": env.world.bot_user.as_user(),
        **fields,
    }
    if thread_id is not None:
        values["message_thread_id"] = thread_id
        values["is_topic_message"] = True
    return chat.add_message(Message(**values))


def _topic(env: BotTestEnvironment, method: TelegramMethod[Any]) -> tuple[ChatState, TopicState]:
    chat = resolve_chat(env, method.chat_id)  # type: ignore[attr-defined]
    return chat, chat.topic(getattr(method, "message_thread_id", None))


@models(CreateForumTopic)
def handle_create_forum_topic(env: BotTestEnvironment, method: CreateForumTopic) -> ForumTopic:
    chat = resolve_chat(env, method.chat_id)
    topic = create_topic(
        chat,
        name=method.name,
        date=env.world.next_date(),
        icon_color=method.icon_color or DEFAULT_TOPIC_ICON_COLOR,
        icon_custom_emoji_id=method.icon_custom_emoji_id,
        from_user=env.world.bot_user.as_user(),
    )
    return topic.as_forum_topic()


@models(EditForumTopic)
def handle_edit_forum_topic(env: BotTestEnvironment, method: EditForumTopic) -> bool:
    chat, topic = _topic(env, method)
    if method.name is not None:
        topic.name = method.name
    if method.icon_custom_emoji_id is not None:
        topic.icon_custom_emoji_id = method.icon_custom_emoji_id
    service_message(
        env,
        chat,
        {
            "forum_topic_edited": ForumTopicEdited(
                name=method.name,
                icon_custom_emoji_id=method.icon_custom_emoji_id,
            ),
        },
        topic.message_thread_id,
    )
    return True


@models(CloseForumTopic)
def handle_close_forum_topic(env: BotTestEnvironment, method: CloseForumTopic) -> bool:
    chat, topic = _topic(env, method)
    topic.is_closed = True
    service_message(env, chat, {"forum_topic_closed": ForumTopicClosed()}, topic.message_thread_id)
    return True


@models(ReopenForumTopic)
def handle_reopen_forum_topic(env: BotTestEnvironment, method: ReopenForumTopic) -> bool:
    chat, topic = _topic(env, method)
    topic.is_closed = False
    service_message(
        env,
        chat,
        {"forum_topic_reopened": ForumTopicReopened()},
        topic.message_thread_id,
    )
    return True


@models(DeleteForumTopic)
def handle_delete_forum_topic(env: BotTestEnvironment, method: DeleteForumTopic) -> bool:
    chat, topic = _topic(env, method)
    for message in list(topic.messages):
        chat.delete_message(message.message_id)
    if topic.message_thread_id is not None:
        del chat.topics[topic.message_thread_id]
    return True


@models(UnpinAllForumTopicMessages)
def handle_unpin_all_forum_topic_messages(
    env: BotTestEnvironment,
    method: UnpinAllForumTopicMessages,
) -> bool:
    chat, topic = _topic(env, method)
    pinned = {message.message_id for message in topic.messages}
    chat.pinned_message_ids = [item for item in chat.pinned_message_ids if item not in pinned]
    return True


@models(EditGeneralForumTopic)
def handle_edit_general_forum_topic(
    env: BotTestEnvironment,
    method: EditGeneralForumTopic,
) -> bool:
    chat = resolve_chat(env, method.chat_id)
    chat.general_topic.name = method.name
    return True


@models(CloseGeneralForumTopic)
def handle_close_general_forum_topic(
    env: BotTestEnvironment,
    method: CloseGeneralForumTopic,
) -> bool:
    resolve_chat(env, method.chat_id).general_topic.is_closed = True
    return True


@models(ReopenGeneralForumTopic)
def handle_reopen_general_forum_topic(
    env: BotTestEnvironment,
    method: ReopenGeneralForumTopic,
) -> bool:
    resolve_chat(env, method.chat_id).general_topic.is_closed = False
    return True


@models(HideGeneralForumTopic)
def handle_hide_general_forum_topic(
    env: BotTestEnvironment,
    method: HideGeneralForumTopic,
) -> bool:
    chat = resolve_chat(env, method.chat_id)
    chat.general_topic.is_hidden = True
    service_message(env, chat, {"general_forum_topic_hidden": GeneralForumTopicHidden()})
    return True


@models(UnhideGeneralForumTopic)
def handle_unhide_general_forum_topic(
    env: BotTestEnvironment,
    method: UnhideGeneralForumTopic,
) -> bool:
    chat = resolve_chat(env, method.chat_id)
    chat.general_topic.is_hidden = False
    service_message(env, chat, {"general_forum_topic_unhidden": GeneralForumTopicUnhidden()})
    return True


@models(UnpinAllGeneralForumTopicMessages)
def handle_unpin_all_general_forum_topic_messages(
    env: BotTestEnvironment,
    method: UnpinAllGeneralForumTopicMessages,
) -> bool:
    chat = resolve_chat(env, method.chat_id)
    pinned = {message.message_id for message in chat.general_topic.messages}
    chat.pinned_message_ids = [item for item in chat.pinned_message_ids if item not in pinned]
    return True


# -- business connections --------------------------------------------------------------


@models(GetBusinessConnection)
def handle_get_business_connection(
    env: BotTestEnvironment,
    method: GetBusinessConnection,
) -> BusinessConnection:
    connection = env.world.business_connection(method.business_connection_id)
    owner = env.world.user(connection.user_id)
    return connection.as_business_connection(owner.as_user())


@models(ReadBusinessMessage)
def handle_read_business_message(
    env: BotTestEnvironment,
    method: ReadBusinessMessage,
) -> bool:
    env.world.business_connection(method.business_connection_id)
    chat = resolve_chat(env, method.chat_id)
    if chat.find_message(method.message_id) is None:
        msg = "message to read not found"
        raise ApiRejection(msg)
    return True


@models(DeleteBusinessMessages)
def handle_delete_business_messages(
    env: BotTestEnvironment,
    method: DeleteBusinessMessages,
) -> bool:
    connection = env.world.business_connection(method.business_connection_id)
    wanted = set(method.message_ids)
    for chat in env.world.chats.values():
        for message in list(chat.messages):
            if message.message_id in wanted and (message.business_connection_id == connection.id):
                chat.delete_message(message.message_id)
    return True
