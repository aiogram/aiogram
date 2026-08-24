from __future__ import annotations

import datetime
import re
from collections.abc import Callable
from types import UnionType
from typing import TYPE_CHECKING, Any, Union, get_args, get_origin

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
    User,
)

from .mounting import detached_copy
from .synthesis import annotation_accepts, synthesize
from .world import (
    BASE_DATE,
    DEFAULT_TOPIC_ICON_COLOR,
    ChatState,
    InviteLinkState,
    MemberState,
    OwnedGiftState,
    PollState,
    QueryKind,
    StickerSetState,
    TopicState,
    WorldLookupError,
    create_topic,
    mask,
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
        # Ephemeral previews. Telegram does not persist these either, so there is no
        # state a test could read back.
        DeleteEphemeralMessage,
        EditEphemeralMessageCaption,
        EditEphemeralMessageMedia,
        EditEphemeralMessageReplyMarkup,
        EditEphemeralMessageText,
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


def _supplied(value: Any) -> Any:
    """
    A copy of something the caller passed in, for the world to keep.

    A request's ``reply_markup``, entities, permissions, commands or menu button belong to
    the code under test — a module-level constant as often as not. Storing the very object
    would put it *in* the world, where it is bound to the bot the moment any result carries
    it back out: the test's own constant would then hold a reference to an environment long
    after it was disposed, and would no longer compare equal to its unbound twin, since
    pydantic counts the binding in ``__eq__`` while hiding it from ``__repr__``. What the
    world keeps is a copy, exactly as what it hands out is.
    """
    return detached_copy(value)


def resolve_chat(env: BotTestEnvironment, chat_id: Any) -> ChatState:
    """Resolve a ``chat_id`` (numeric or ``@username``) against the world."""
    if isinstance(chat_id, int):
        chat = env.world.chats.get(chat_id)
        if chat is not None:
            return chat
    if isinstance(chat_id, str):
        wanted = chat_id.lstrip("@")
        for chat in env.world.chats.values():
            if chat.username == wanted:
                return chat
    msg = "chat not found"
    raise WorldLookupError(msg)


def _nonempty(annotation: Any, env: BotTestEnvironment, name: str) -> Any:
    """Synthesize a value, making a list annotation carry one element."""
    members = annotation
    if get_origin(annotation) in {UnionType, Union}:
        members = next(
            (arg for arg in get_args(annotation) if arg is not type(None)),
            annotation,
        )
    if get_origin(members) is list:
        (item_type,) = get_args(members)
        return [synthesize(item_type, env.synthesis_context(), name=name)]
    return synthesize(members, env.synthesis_context(), name=name)


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
    values: dict[str, Any] = {
        "message_id": chat.allocate_message_id(),
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
            values[name] = _supplied(value)

    reply_markup = getattr(method, "reply_markup", None)
    if isinstance(reply_markup, InlineKeyboardMarkup):
        values["reply_markup"] = _supplied(reply_markup)
    if getattr(method, "protect_content", None):
        values["has_protected_content"] = True
    if thread_id is not None and chat.is_forum:
        values["is_topic_message"] = True

    reply_parameters = getattr(method, "reply_parameters", None)
    if reply_parameters is not None and reply_parameters.message_id is not None:
        replied = chat.find_message(reply_parameters.message_id)
        if replied is not None:
            values["reply_to_message"] = replied

    if media_field is not None:
        values[media_field] = _carry_request_values(
            method,
            _nonempty(Message.model_fields[media_field].annotation, env, media_field),
        )
        _register_uploaded_content(env, method, media_field, values[media_field])

    message = Message(**values)
    return chat.add_message(message)


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
        name: _supplied(value)
        for name, info in type(payload).model_fields.items()
        if (value := getattr(method, name, None)) is not None
        and annotation_accepts(info.annotation, type(value))
    }
    return payload.model_copy(update=carried) if carried else payload


def _as_datetime(value: Any) -> datetime.datetime | None:
    """Bot API ``until_date`` accepts a datetime, a timedelta or a unix timestamp."""
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.timedelta):
        return BASE_DATE + value
    if isinstance(value, int):
        return datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)
    return None


def _edit_target(env: BotTestEnvironment, method: TelegramMethod[Any]) -> tuple[ChatState, int]:
    if getattr(method, "inline_message_id", None) is not None:
        msg = "inline messages are not modeled by the test environment"
        raise WorldLookupError(msg)
    chat = resolve_chat(env, getattr(method, "chat_id", None))
    message_id: int | None = getattr(method, "message_id", None)
    if message_id is None or chat.find_message(message_id) is None:
        msg = "message to edit not found"
        raise WorldLookupError(msg)
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
        raise WorldLookupError("message to forward not found")
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
        raise WorldLookupError("message to copy not found")
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


@models(EditMessageText)
def handle_edit_text(env: BotTestEnvironment, method: EditMessageText) -> Message:
    chat, message_id = _edit_target(env, method)
    return chat.update_message(
        message_id,
        text=method.text,
        entities=method.entities,
        reply_markup=method.reply_markup,
    )


@models(EditMessageCaption)
def handle_edit_caption(env: BotTestEnvironment, method: EditMessageCaption) -> Message:
    chat, message_id = _edit_target(env, method)
    return chat.update_message(
        message_id,
        caption=method.caption,
        caption_entities=method.caption_entities,
        reply_markup=method.reply_markup,
    )


@models(EditMessageReplyMarkup)
def handle_edit_reply_markup(
    env: BotTestEnvironment,
    method: EditMessageReplyMarkup,
) -> Message:
    chat, message_id = _edit_target(env, method)
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


@models(EditMessageMedia)
def handle_edit_media(env: BotTestEnvironment, method: EditMessageMedia) -> Message:
    chat, message_id = _edit_target(env, method)
    field = media_field(method.media)
    # A message carries one kind of content: drop whatever it held before.
    changes: dict[str, Any] = dict.fromkeys(EDITABLE_MEDIA_FIELDS)
    changes["text"] = None
    changes[field] = _nonempty(Message.model_fields[field].annotation, env, field)
    changes["caption"] = method.media.caption
    changes["caption_entities"] = method.media.caption_entities
    if method.reply_markup is not None:
        changes["reply_markup"] = method.reply_markup
    return chat.update_message(message_id, **changes)


def _location(method: TelegramMethod[Any], live_period: int | None) -> Location:
    return Location(
        latitude=method.latitude,  # type: ignore[attr-defined]
        longitude=method.longitude,  # type: ignore[attr-defined]
        horizontal_accuracy=getattr(method, "horizontal_accuracy", None),
        heading=getattr(method, "heading", None),
        proximity_alert_radius=getattr(method, "proximity_alert_radius", None),
        live_period=live_period,
    )


@models(EditMessageLiveLocation)
def handle_edit_live_location(
    env: BotTestEnvironment,
    method: EditMessageLiveLocation,
) -> Message:
    chat, message_id = _edit_target(env, method)
    stored = chat.require_message(message_id)
    live_period = method.live_period
    if live_period is None and stored.location is not None:
        # Omitting live_period leaves the existing one running, it does not end it.
        live_period = stored.location.live_period
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

    Telegram's real effect — the location stopping being live — has no other observable
    consequence in a fake with no clock, so clearing ``live_period`` is the whole model.
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
        checklist=_nonempty(Message.model_fields["checklist"].annotation, env, "checklist"),
        reply_markup=method.reply_markup,
    )


@models(DeleteMessage)
def handle_delete(env: BotTestEnvironment, method: DeleteMessage) -> bool:
    chat = resolve_chat(env, method.chat_id)
    if chat.find_message(method.message_id) is None:
        raise WorldLookupError("message to delete not found")
    chat.delete_message(method.message_id)
    return True


@models(DeleteMessages)
def handle_delete_many(env: BotTestEnvironment, method: DeleteMessages) -> bool:
    chat = resolve_chat(env, method.chat_id)
    for message_id in method.message_ids:
        if chat.find_message(message_id) is not None:
            chat.delete_message(message_id)
    return True


@models(PinChatMessage)
def handle_pin(env: BotTestEnvironment, method: PinChatMessage) -> bool:
    chat = resolve_chat(env, method.chat_id)
    if method.message_id is None or chat.find_message(method.message_id) is None:
        raise WorldLookupError("message to pin not found")
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
        raise WorldLookupError("user has no personal chat")
    return chat.messages[-method.limit :]


# -- membership ------------------------------------------------------------------------


@models(BanChatMember)
def handle_ban(env: BotTestEnvironment, method: BanChatMember) -> bool:
    chat = resolve_chat(env, method.chat_id)
    member = chat.member(method.user_id)
    member.status = ChatMemberStatus.KICKED
    member.until_date = _as_datetime(method.until_date)
    return True


@models(UnbanChatMember)
def handle_unban(env: BotTestEnvironment, method: UnbanChatMember) -> bool:
    chat = resolve_chat(env, method.chat_id)
    chat.member(method.user_id).status = ChatMemberStatus.LEFT
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

    The chat's owner is not promotable or demotable — their rights are not the bot's to
    change, and Telegram refuses. Without that guard the fake was *more* permissive than
    the API it stands in for, and in the one direction a test cannot notice: a bot that
    promotes a list of users would quietly turn the owner into an ordinary member here and
    fail only in production.
    """
    chat = resolve_chat(env, method.chat_id)
    member = chat.member(method.user_id)
    if member.status == ChatMemberStatus.CREATOR:
        raise WorldLookupError("can't remove chat owner")
    granted = mask(ChatAdministratorRights, method, coerce=True)
    if not any(granted.values()):
        member.status = ChatMemberStatus.MEMBER
        member.rights = None
        return True
    member.status = ChatMemberStatus.ADMINISTRATOR
    member.rights = ChatAdministratorRights(**granted)
    return True


@models(RestrictChatMember)
def handle_restrict(env: BotTestEnvironment, method: RestrictChatMember) -> bool:
    """
    Restrict a member, persisting the permissions the request set.

    The permissions are copied: they belong to the caller — a module-level constant shared
    by a whole test file, as often as not — and what the world stores must not be an object
    the test can still mutate, nor one that a later read hands back out.
    """
    chat = resolve_chat(env, method.chat_id)
    member = chat.member(method.user_id)
    member.status = ChatMemberStatus.RESTRICTED
    member.permissions = _supplied(method.permissions)
    member.rights = None
    member.until_date = _as_datetime(method.until_date)
    return True


@models(LeaveChat)
def handle_leave(env: BotTestEnvironment, method: LeaveChat) -> bool:
    chat = resolve_chat(env, method.chat_id)
    chat.member(env.world.bot_user.id).status = ChatMemberStatus.LEFT
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
        raise WorldLookupError(msg)
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
    msg = f"Gift {gift_id!r} is not in the catalogue"
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
        raise WorldLookupError(msg)
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
        raise WorldLookupError(msg)
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
        expire_date=_as_datetime(method.expire_date),
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
        raise WorldLookupError(msg)
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
    link.expire_date = _as_datetime(method.expire_date)
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
        raise WorldLookupError(msg)
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
        raise WorldLookupError(msg)
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

    Stored as a copy, for the reason :func:`handle_restrict` gives: what a later ``getChat``
    hands back — and mounts to the calling bot — must not be the caller's own object.
    """
    _administrable(env, method).permissions = _supplied(method.permissions)
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
    return sum(1 for member in chat.members.values() if member.is_present)


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
        raise WorldLookupError(complaint)
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
    env.world.profile.commands[key] = _supplied(list(method.commands))
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
        rights[scope] = _supplied(method.rights)
    return True


@models(GetMyDefaultAdministratorRights)
def handle_get_default_admin_rights(
    env: BotTestEnvironment,
    method: GetMyDefaultAdministratorRights,
) -> ChatAdministratorRights:
    stored = env.world.profile.default_admin_rights.get(bool(method.for_channels))
    if stored is not None:
        return detached_copy(stored)  # type: ignore[no-any-return]
    return ChatAdministratorRights(
        **dict.fromkeys(ChatAdministratorRights.model_fields, False),
    )


@models(SetChatMenuButton)
def handle_set_chat_menu_button(env: BotTestEnvironment, method: SetChatMenuButton) -> bool:
    if method.chat_id is not None:
        resolve_chat(env, method.chat_id)
    button = method.menu_button if method.menu_button is not None else MenuButtonDefault()
    env.world.profile.menu_buttons[method.chat_id] = _supplied(button)
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


@models(SendPoll)
def handle_send_poll(env: BotTestEnvironment, method: SendPoll) -> Message:
    chat = resolve_chat(env, method.chat_id)
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
    )
    env.world.polls[poll.id] = poll
    message = build_message(env, method, chat)
    return chat.update_message(message.message_id, poll=poll.as_poll())


@models(StopPoll)
def handle_stop_poll(env: BotTestEnvironment, method: StopPoll) -> Poll:
    chat, message_id = _edit_target(env, method)
    stored = chat.require_message(message_id)
    if stored.poll is None:
        msg = "message doesn't contain a poll"
        raise WorldLookupError(msg)
    poll = env.world.poll(stored.poll.id)
    if poll.is_closed:
        msg = "poll has already been closed"
        raise WorldLookupError(msg)
    poll.is_closed = True
    chat.update_message(message_id, poll=poll.as_poll())
    return poll.as_poll()


# -- reactions -------------------------------------------------------------------------


def _reaction_target(
    env: BotTestEnvironment, method: TelegramMethod[Any]
) -> tuple[ChatState, int]:
    chat = resolve_chat(env, method.chat_id)  # type: ignore[attr-defined]
    message_id: int = method.message_id  # type: ignore[attr-defined]
    if chat.find_message(message_id) is None:
        msg = "message to react to not found"
        raise WorldLookupError(msg)
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
        raise WorldLookupError(msg)
    chat.join_requests.discard(user_id)
    return chat


@models(ApproveChatJoinRequest)
def handle_approve_join_request(
    env: BotTestEnvironment,
    method: ApproveChatJoinRequest,
) -> bool:
    chat = _pending_request(env, method)
    chat.member(method.user_id).status = ChatMemberStatus.MEMBER
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
        raise WorldLookupError(msg)
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
