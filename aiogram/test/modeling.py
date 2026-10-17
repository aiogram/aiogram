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

**Refusing a call.** Raise a rejection declared in
:mod:`aiogram.test.rejections`, such as
``raise rejections.MESSAGE_CANT_BE_DELETED()``, for something the
real API would refuse. Its description is declared there, sourced or
best-effort, and ``handle_call`` turns it into the exception its error
code stands for, a :class:`~aiogram.exceptions.TelegramBadRequest` for
the usual 400. Raise :class:`~aiogram.test.WorldLookupError` for a gap
in the test's own setup or a limit of the fake. That one propagates
and fails the test instead of arriving as an error the bot might
catch.
"""

from __future__ import annotations

import dataclasses
import datetime
import functools
import re
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any, get_args

from pydantic import BaseModel

from aiogram.enums import ChatMemberStatus, ChatType, DiceEmoji, PollType
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
    BusinessConnection,
    ChatAdministratorRights,
    ChatFullInfo,
    ChatInviteLink,
    ChatPermissions,
    Checklist,
    ChecklistTask,
    Dice,
    EphemeralMessageParameters,
    ExternalReplyInfo,
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
    InputChecklist,
    InputRichMessage,
    InputSticker,
    Invoice,
    Location,
    MenuButtonDefault,
    Message,
    MessageId,
    MessageOriginChannel,
    MessageOriginChat,
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
    Venue,
)

from . import rejections
from .markup import refuse_blank_text
from .mounting import detached_copy
from .rejections import Rejection
from .rich import materialize_rich_message
from .synthesis import (
    annotation_accepts,
    nonempty,
    synthesize,
    unique_file_id,
    with_passed_file,
)
from .world import (
    CHAT_TYPE_SCOPED_RIGHTS,
    DEFAULT_TOPIC_ICON_COLOR,
    UNTIL_FOREVER,
    BusinessConnectionState,
    ChatState,
    InviteLinkState,
    MemberState,
    OwnedGiftState,
    PollState,
    QueryKind,
    StickerSetState,
    TopicState,
    UserState,
    World,
    WorldLookupError,
    administrator_rights,
    aware,
    create_topic,
    granted_permissions,
    mask,
    new_poll,
    no_administrator_rights,
    posted_by,
    scope_key,
)

if TYPE_CHECKING:
    from .environment import BotTestEnvironment

MethodHandler = Callable[["BotTestEnvironment", Any], Any]

REGISTRY: dict[type[TelegramMethod[Any]], MethodHandler] = {}

#: The methods whose handlers put a message, an album or a batch into
#: a chat, as ``models(..., sends=True)`` registers them. Those are
#: the calls the flood limits count; see
#: :meth:`~aiogram.test.BotTestEnvironment.admit_send`.
SENDING_METHODS: set[type[TelegramMethod[Any]]] = set()

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


def models(
    *method_types: type[TelegramMethod[Any]],
    sends: bool = False,
) -> Callable[[MethodHandler], MethodHandler]:
    """Register a handler; ``sends`` marks it as one that posts."""

    def decorator(handler: MethodHandler) -> MethodHandler:
        for method_type in method_types:
            REGISTRY[method_type] = handler
            if sends:
                SENDING_METHODS.add(method_type)
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
    chat = known_chat(env, chat_id)
    if chat is None:
        raise WorldLookupError(_undeclared_chat_message(env, chat_id))
    return chat


def known_chat(env: BotTestEnvironment, chat_id: Any) -> ChatState | None:
    """The chat ``chat_id`` names, or ``None`` if the world has none."""
    if isinstance(chat_id, int):
        return env.world.chats.get(chat_id)
    if isinstance(chat_id, str):
        wanted = chat_id.lstrip("@")
        for chat in env.world.chats.values():
            if chat.username == wanted:
                return chat
    return None


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


# -- the bot's own rights -----------------------------------------
#
# What the bot may do in a group, a supergroup or a channel is one
# table, BOT_RIGHTS: method type -> rule. handle_call consults it
# once, after parse modes and before the handler, so adding a method
# is adding a row. Only what depends on the call's content stays in
# the handlers: what a message carries (require_send_permission) and
# whose message is deleted (bot_may_delete).
#
# Each refusal is Telegram's wording, so it cannot carry a hint. The
# fix is to declare the bot's standing: ``bot_status=`` on
# ``Blueprint.add_group`` and its siblings, or
# ``Blueprint.set_member(chat, blueprint.bot, rights=...)`` for one
# right. ``BotTestEnvironment(enforce_bot_rights=False)`` turns the
# checks off. The texts are TDLib's, which the Bot API server relays
# with the first letter lowercased: td/telegram/DialogManager.cpp,
# ChatManager.cpp, DialogInviteLinkManager.cpp,
# DialogParticipantManager.cpp, ForumTopicManager.cpp and
# MessageContent.cpp.


_ADMINISTRATOR_STATUSES = frozenset({ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR})

#: The chat types the bot needs rights in.
_GROUP_LIKE = frozenset({ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL})

#: What an administrator declared without rights holds, built once.
_ORDINARY_RIGHTS = administrator_rights()

#: How the Bot API server names a chat type in a 403.
_CHAT_NOUNS: dict[str, str] = {
    ChatType.GROUP: "group",
    ChatType.SUPERGROUP: "supergroup",
    ChatType.CHANNEL: "channel",
}


def _member_of(chat: ChatState, user_id: int) -> MemberState | None:
    """The settled membership of ``user_id`` in ``chat``, if any."""
    if user_id not in chat.members:
        return None
    return chat.member(user_id)


def _bot_member(env: BotTestEnvironment, chat: ChatState) -> MemberState | None:
    """The bot's settled membership of ``chat``, if it has one."""
    return _member_of(chat, env.world.bot_user.id)


def holds_right(chat: ChatState, user_id: int, right: str) -> bool:
    """
    Whether ``user_id`` holds the administrator ``right`` in ``chat``.

    The owner holds every right. An administrator holds what its
    rights grant, unless the right does not exist in the chat's type,
    as :data:`~aiogram.test.world.CHAT_TYPE_SCOPED_RIGHTS` says. No
    one else holds any.
    """
    member = _member_of(chat, user_id)
    if member is None or member.status not in _ADMINISTRATOR_STATUSES:
        return False
    if member.status == ChatMemberStatus.CREATOR:
        return True
    scope = CHAT_TYPE_SCOPED_RIGHTS.get(right)
    if scope is not None and chat.type not in scope:
        return False
    declared = member.rights if member.rights is not None else _ORDINARY_RIGHTS
    return bool(getattr(declared, right))


def bot_has_right(env: BotTestEnvironment, chat: ChatState, right: str) -> bool:
    """
    Whether the bot holds the administrator ``right`` in ``chat``.

    See :func:`holds_right`. With ``enforce_bot_rights`` off, every
    right is held.
    """
    return not env.enforce_bot_rights or holds_right(chat, env.world.bot_user.id, right)


def require_standing(env: BotTestEnvironment, chat: ChatState) -> None:
    """
    Refuse a call into a chat the bot was removed from or left.

    The Bot API server answers it with a 403 before anything else
    (``check_chat_access`` in telegram-bot-api's Client.cpp). A bot
    whose membership is not declared at all counts as a member.
    """
    if chat.type == ChatType.PRIVATE or not env.enforce_bot_rights:
        return
    member = _bot_member(env, chat)
    if member is None or member.is_present:
        return
    refusal = (
        rejections.BOT_KICKED
        if member.status == ChatMemberStatus.KICKED
        else rejections.BOT_NOT_A_MEMBER
    )
    raise refusal(noun=_CHAT_NOUNS[chat.type])


#: What runs before a rule looks at the bot's rights. It may refuse,
#: as Telegram refuses some calls earlier, and returns True to let
#: the call through without the right.
Precheck = Callable[["BotTestEnvironment", ChatState, Any], bool]


@dataclasses.dataclass(frozen=True)
class RightRule:
    """
    The administrator right one kind of call takes.

    ``right`` names it, or is a function of the chat's type naming
    it. ``rejection`` is Telegram's refusal without it, and
    ``rejections`` the one a chat type gets instead. The rule holds in
    ``chat_types`` only, and ``before`` runs first, see
    :data:`Precheck`.
    """

    right: str | Callable[[str], str]
    rejection: Rejection
    rejections: Mapping[str, Rejection] = dataclasses.field(default_factory=dict)
    chat_types: frozenset[str] = _GROUP_LIKE
    before: Precheck | None = None

    def right_in(self, chat_type: str) -> str:
        """The right a chat of ``chat_type`` takes."""
        return self.right if isinstance(self.right, str) else self.right(chat_type)

    def rejection_in(self, chat_type: str) -> Rejection:
        """Telegram's refusal in a chat of ``chat_type``."""
        return self.rejections.get(chat_type, self.rejection)


def _pin_right(chat_type: str) -> str:
    """Pins take ``can_edit_messages`` in a channel, as stated."""
    return "can_edit_messages" if chat_type == ChatType.CHANNEL else "can_pin_messages"


def _on_behalf_of_business(env: BotTestEnvironment, chat: ChatState, method: Any) -> bool:
    """A business account pins its own chats; no right is needed."""
    return getattr(method, "business_connection_id", None) is not None


def _owner_first(env: BotTestEnvironment, chat: ChatState, method: Any) -> bool:
    """
    TDLib refuses touching the owner before it reads the rights.

    Only in a supergroup or a channel; in a basic group the server
    decides, see :func:`_not_the_owner`.
    """
    if chat.type != ChatType.GROUP:
        _not_the_owner(chat, method.user_id)
    return False


def _unban_first(env: BotTestEnvironment, chat: ChatState, method: UnbanChatMember) -> bool:
    """With ``only_if_banned``, a user not banned needs nothing."""
    if method.only_if_banned and chat.member(method.user_id).status != ChatMemberStatus.KICKED:
        return True
    return _owner_first(env, chat, method)


def _forum_first(env: BotTestEnvironment, chat: ChatState, method: Any) -> bool:
    """A forum method is refused in a chat that is not one first."""
    forum_chat(env, chat.id)
    return False


def _opened_by_bot(env: BotTestEnvironment, chat: ChatState, method: Any) -> bool:
    """
    Whether the bot needs no right for the topic, as its creator.

    TDLib lets the creator of a topic edit, close, reopen and delete
    it without the right, and refuses anyone else who lacks it, but
    only for a topic it holds (ForumTopicManager.cpp, ``is_outgoing``
    behind ``get_topic_info``). A topic it does not hold goes on to
    the server unchecked, so the handler's refusal answers it, a bot
    holding the right or not. That covers a topic the bot itself
    deleted: TDLib drops it from its cache, so the bot's own
    exemption is gone with it and a later call meets ``TOPIC_DELETED``.
    """
    forum_chat(env, chat.id)
    topic = chat.topics.get(getattr(method, "message_thread_id", None) or 0)
    return topic is None or topic.creator_id == env.world.bot_user.id


_PINNING = RightRule(
    right=_pin_right,
    rejection=rejections.NO_RIGHTS_TO_PIN,
    before=_on_behalf_of_business,
)
_RESTRICTING = RightRule(
    right="can_restrict_members",
    # TDLib has no check of its own in a basic group, so the server's
    # error comes back.
    rejection=rejections.NO_RIGHTS_TO_RESTRICT,
    rejections={ChatType.GROUP: rejections.CHAT_ADMIN_REQUIRED},
    before=_owner_first,
)
#: Where the Bot API server takes unbanning and promoting at all
#: (Client.cpp, ``process_unban_chat_member_query`` and
#: ``process_promote_chat_member_query``); the handler refuses the
#: rest, after the standing check.
_SUPERGROUP_OR_CHANNEL = frozenset({ChatType.SUPERGROUP, ChatType.CHANNEL})
_STICKER_SET = RightRule(
    right="can_change_info",
    rejection=rejections.NO_RIGHTS_TO_CHANGE_STICKER_SET,
)
_SENDER_CHAT_BANS = RightRule(
    right="can_restrict_members",
    rejection=rejections.NO_RIGHTS_TO_RESTRICT,
    chat_types=_SUPERGROUP_OR_CHANNEL,
)
_SUGGESTED_POSTS = RightRule(
    right="can_post_messages",
    # TDLib's text when the right is missing (MessagesManager.cpp,
    # ``process_suggested_post``). The toolkit has no channel direct
    # messages chat, so the right is read off the chat named.
    rejection=rejections.SUGGESTED_POST_UNUSABLE,
    chat_types=frozenset({ChatType.CHANNEL}),
)
_INVITING = RightRule(
    right="can_invite_users",
    rejection=rejections.NO_RIGHTS_TO_MANAGE_INVITE_LINKS,
)
_JOIN_REQUESTS = RightRule(
    right="can_invite_users",
    rejection=rejections.NO_RIGHTS_TO_MANAGE_JOIN_REQUESTS,
)
_CHAT_PHOTO = RightRule(
    right="can_change_info",
    rejection=rejections.NO_RIGHTS_TO_CHANGE_PHOTO,
)
_SUPERGROUP = frozenset({ChatType.SUPERGROUP})
_TOGGLING_TOPICS = RightRule(
    right="can_manage_topics",
    rejection=rejections.NO_RIGHTS_TO_TOGGLE_TOPIC,
    chat_types=_SUPERGROUP,
    before=_opened_by_bot,
)
_TOGGLING_GENERAL = RightRule(
    right="can_manage_topics",
    rejection=rejections.NO_RIGHTS_TO_TOGGLE_TOPIC,
    chat_types=_SUPERGROUP,
    before=_forum_first,
)

#: Method type -> the right the bot needs to call it in a group, a
#: supergroup or a channel. See the comment above.
BOT_RIGHTS: dict[type[TelegramMethod[Any]], RightRule] = {
    PinChatMessage: _PINNING,
    UnpinChatMessage: _PINNING,
    UnpinAllChatMessages: _PINNING,
    # The rights first; the topic is the handler's to look up.
    UnpinAllForumTopicMessages: dataclasses.replace(_PINNING, before=_forum_first),
    UnpinAllGeneralForumTopicMessages: dataclasses.replace(_PINNING, before=_forum_first),
    BanChatMember: _RESTRICTING,
    UnbanChatMember: RightRule(
        right="can_restrict_members",
        rejection=rejections.NO_RIGHTS_TO_RESTRICT,
        chat_types=_SUPERGROUP_OR_CHANNEL,
        before=_unban_first,
    ),
    # Restricting is for supergroups only; the handler refuses the rest.
    RestrictChatMember: dataclasses.replace(_RESTRICTING, chat_types=_SUPERGROUP),
    PromoteChatMember: RightRule(
        right="can_promote_members",
        rejection=rejections.NO_RIGHTS_TO_PROMOTE,
        chat_types=_SUPERGROUP_OR_CHANNEL,
        before=_owner_first,
    ),
    SetChatPermissions: RightRule(
        right="can_restrict_members",
        rejection=rejections.NO_RIGHTS_TO_CHANGE_PERMISSIONS,
    ),
    SetChatStickerSet: _STICKER_SET,
    DeleteChatStickerSet: _STICKER_SET,
    BanChatSenderChat: _SENDER_CHAT_BANS,
    UnbanChatSenderChat: _SENDER_CHAT_BANS,
    SetChatMemberTag: RightRule(
        right="can_manage_tags",
        # TDLib leaves the check to the server, whose answer is not
        # in the open source; this is its usual one.
        rejection=rejections.CHAT_ADMIN_REQUIRED,
    ),
    ApproveSuggestedPost: _SUGGESTED_POSTS,
    DeclineSuggestedPost: _SUGGESTED_POSTS,
    SetChatTitle: RightRule(
        right="can_change_info",
        rejection=rejections.NO_RIGHTS_TO_CHANGE_TITLE,
    ),
    SetChatDescription: RightRule(
        right="can_change_info",
        rejection=rejections.NO_RIGHTS_TO_CHANGE_DESCRIPTION,
    ),
    SetChatPhoto: _CHAT_PHOTO,
    DeleteChatPhoto: _CHAT_PHOTO,
    CreateChatInviteLink: _INVITING,
    CreateChatSubscriptionInviteLink: _INVITING,
    EditChatInviteLink: _INVITING,
    EditChatSubscriptionInviteLink: _INVITING,
    RevokeChatInviteLink: _INVITING,
    ExportChatInviteLink: _INVITING,
    ApproveChatJoinRequest: _JOIN_REQUESTS,
    DeclineChatJoinRequest: _JOIN_REQUESTS,
    CreateForumTopic: RightRule(
        right="can_manage_topics",
        rejection=rejections.NO_RIGHTS_TO_CREATE_TOPIC,
        chat_types=_SUPERGROUP,
        before=_forum_first,
    ),
    EditForumTopic: RightRule(
        right="can_manage_topics",
        rejection=rejections.NO_RIGHTS_TO_EDIT_TOPIC,
        chat_types=_SUPERGROUP,
        before=_opened_by_bot,
    ),
    EditGeneralForumTopic: RightRule(
        right="can_manage_topics",
        rejection=rejections.NO_RIGHTS_TO_EDIT_TOPIC,
        chat_types=_SUPERGROUP,
        before=_forum_first,
    ),
    CloseForumTopic: _TOGGLING_TOPICS,
    ReopenForumTopic: _TOGGLING_TOPICS,
    CloseGeneralForumTopic: _TOGGLING_GENERAL,
    ReopenGeneralForumTopic: _TOGGLING_GENERAL,
    HideGeneralForumTopic: _TOGGLING_GENERAL,
    UnhideGeneralForumTopic: _TOGGLING_GENERAL,
    DeleteForumTopic: RightRule(
        right="can_delete_messages",
        rejection=rejections.NO_RIGHTS_TO_DELETE_TOPIC,
        chat_types=_SUPERGROUP,
        before=_opened_by_bot,
    ),
}


def check_bot_rights(env: BotTestEnvironment, method: TelegramMethod[Any]) -> None:
    """
    Refuse a call the bot's standing in its chat does not allow.

    Looks the method up in :data:`BOT_RIGHTS`. A chat the world does
    not have is left to the handler, which says how to declare it,
    and a method with no handler is still checked.
    """
    rule = BOT_RIGHTS.get(type(method))
    if rule is None or not env.enforce_bot_rights:
        return
    chat = known_chat(env, getattr(method, "chat_id", None))
    if chat is None or chat.type == ChatType.PRIVATE:
        return
    require_standing(env, chat)
    if chat.type not in rule.chat_types:
        return
    if rule.before is not None and rule.before(env, chat, method):
        return
    if not holds_right(chat, env.world.bot_user.id, rule.right_in(chat.type)):
        raise rule.rejection_in(chat.type)()


#: Message content field -> the permissions sending it takes, and how
#: Telegram's refusal names it. A field not listed is a text message.
_SEND_PERMISSIONS: dict[str, tuple[tuple[str, ...], str]] = {
    "animation": (("can_send_other_messages",), "animations"),
    "audio": (("can_send_audios",), "music"),
    "checklist": (("can_send_polls",), "checklists"),
    "contact": (("can_send_messages",), "contacts"),
    "dice": (("can_send_other_messages",), "dice"),
    "document": (("can_send_documents",), "documents"),
    "game": (("can_send_other_messages",), "games"),
    "invoice": (("can_send_messages",), "invoice messages"),
    "live_photo": (("can_send_photos",), "photos"),
    "live_location": (("can_send_messages",), "live locations"),
    "location": (("can_send_messages",), "locations"),
    # Checked when forwarded or copied only: a bot's own send of
    # paid media takes no permission in TDLib.
    "paid_media": (("can_send_photos", "can_send_videos"), "paid media"),
    "photo": (("can_send_photos",), "photos"),
    "poll": (("can_send_polls",), "polls"),
    "rich_message": (("can_send_messages",), "the rich message"),
    "sticker": (("can_send_other_messages",), "stickers"),
    "venue": (("can_send_messages",), "venues"),
    "video": (("can_send_videos",), "videos"),
    "video_note": (("can_send_video_notes",), "video notes"),
    "voice": (("can_send_voice_notes",), "voice notes"),
}


def content_kind(message: Message) -> str:
    """The :data:`_SEND_PERMISSIONS` key of what ``message`` carries."""
    kind = next(
        (name for name in _SEND_PERMISSIONS if getattr(message, name, None) is not None),
        "text",
    )
    if kind == "location" and message.location and message.location.live_period:
        return "live_location"
    return kind


def _permitted(permissions: ChatPermissions | None, name: str, *, unset: bool) -> bool:
    """Whether ``permissions`` grant ``name``; ``unset`` if None."""
    if permissions is None:
        return unset
    return bool(getattr(permissions, name, None))


def member_may(chat: ChatState, member: MemberState | None, permission: str) -> bool:
    """
    Whether a member who is no administrator has ``permission``.

    What the chat's permissions allow, narrowed by the member's own
    restriction. Chat permissions never set allow everything; a
    restriction allows only what it granted.
    """
    allowed = _permitted(chat.permissions, permission, unset=True)
    if member is not None and member.status == ChatMemberStatus.RESTRICTED:
        allowed = allowed and _permitted(member.permissions, permission, unset=False)
    return allowed


def may_create_topics(chat: ChatState, user_id: int) -> bool:
    """
    Whether ``user_id``, a user and not the bot, may open a topic.

    TDLib's ``can_create_topics``: the ``can_manage_topics`` right, or
    the chat permission of that name, which binds administrators who
    are not bots as much as members (DialogParticipant.cpp,
    ``apply_restrictions``). A restricted member needs it granted.
    """
    if holds_right(chat, user_id, "can_manage_topics"):
        return True
    member = _member_of(chat, user_id)
    return (
        member is not None and member.is_present and member_may(chat, member, "can_manage_topics")
    )


def require_send_permission(
    env: BotTestEnvironment,
    chat: ChatState,
    kind: str,
    *,
    forwarded: bool = False,
) -> None:
    """
    Refuse a message of ``kind`` the bot may not send into ``chat``.

    The owner and administrators send anything in a group, and in a
    channel only they may post at all, with ``can_post_messages``.
    Anyone else sends what :func:`member_may` allows. Paid media is
    checked only when ``forwarded``, as TDLib checks it. Declare
    ``bot_status=`` or ``Blueprint.set_member(chat, blueprint.bot,
    rights=...)`` for an administrator, or grant the permission on
    the chat's declared ``permissions``.
    """
    if chat.type == ChatType.PRIVATE or not env.enforce_bot_rights:
        return
    if chat.type == ChatType.CHANNEL:
        if not bot_has_right(env, chat, "can_post_messages"):
            raise rejections.NO_RIGHTS_TO_POST_IN_CHANNEL()
        return
    member = _bot_member(env, chat)
    if member is not None and member.status in _ADMINISTRATOR_STATUSES:
        return
    if kind == "paid_media" and not forwarded:
        return
    permissions, noun = _SEND_PERMISSIONS.get(kind, (("can_send_messages",), "text messages"))
    if not all(member_may(chat, member, permission) for permission in permissions):
        raise rejections.NO_RIGHTS_TO_SEND(noun=noun)


def bot_may_delete(env: BotTestEnvironment, chat: ChatState, message: Message) -> bool:
    """
    Whether the bot's standing lets it delete ``message``.

    Its own messages are always its to delete outside channels. In a
    basic group any administrator deletes the others', and in a
    supergroup one holding ``can_delete_messages``. In a channel that
    right deletes any post, and ``can_post_messages`` the bot's own,
    as ``deleteMessage`` states. A post with no signature is read as
    the bot's, since only an actor signs one here.
    """
    if chat.type == ChatType.PRIVATE or not env.enforce_bot_rights:
        return True
    sender = message.from_user
    if chat.type == ChatType.CHANNEL:
        sender_chat = message.sender_chat
        own = (
            sender_chat is not None
            and sender_chat.id == chat.id
            and message.author_signature is None
        )
        return bot_has_right(env, chat, "can_delete_messages") or (
            own and bot_has_right(env, chat, "can_post_messages")
        )
    if sender is not None and sender.id == env.world.bot_user.id:
        return True
    if chat.type == ChatType.GROUP:
        member = _bot_member(env, chat)
        return member is not None and member.status in _ADMINISTRATOR_STATUSES
    return bot_has_right(env, chat, "can_delete_messages")


def posting_topic(
    env: BotTestEnvironment,
    chat: ChatState,
    thread_id: int | None,
) -> TopicState | None:
    """
    The topic a message the bot sends lands in, once it may post there.

    ``None`` outside a forum and a private chat's topics. A thread
    the chat does not have fails as :meth:`ChatState.topic_for_call`
    says. A closed topic, or a closed or hidden General topic, takes
    messages only from someone who may manage topics or from the
    topic's creator: ``TOPIC_CLOSED`` otherwise, an MTProto error the
    Bot API server passes through as the description.
    """
    if chat.type == ChatType.PRIVATE:
        # The server looks up any thread a private chat is sent.
        return None if thread_id is None else chat.topic_for_call(thread_id, sending=True)
    if not chat.is_forum:
        return None
    topic = chat.topic_for_call(thread_id, sending=True)
    closed = topic.is_closed or (topic.is_general and topic.is_hidden)
    opened = topic.creator_id is not None and topic.creator_id == env.world.bot_user.id
    if closed and not opened and not bot_has_right(env, chat, "can_manage_topics"):
        raise rejections.TOPIC_CLOSED()
    return topic


def build_message(
    env: BotTestEnvironment,
    method: TelegramMethod[Any],
    chat: ChatState,
    media_field: str | None = None,
    *,
    content: Callable[[], dict[str, Any]] | None = None,
) -> Message:
    """
    Store the message a send method produces, and return it.

    ``content`` builds what the message carries when the method alone
    does not say, such as one item of a media group. It is called once
    the send is checked, so a refused one registers no file and uses up
    no file number.
    """
    thread_id = getattr(method, "message_thread_id", None)
    require_standing(env, chat)
    # An unknown thread id must fail rather than silently produce an
    # untagged message.
    topic = posting_topic(env, chat, thread_id)
    refuse_blank_text(method)
    receiver = _ephemeral_receiver(env, method, chat)
    if receiver is None and content is None:
        # An ephemeral message is exempt, as TDLib exempts it; a media
        # group checks its items itself.
        require_send_permission(env, chat, _sent_kind(method, media_field))
    reply = _reply_changes(env, method, chat, ephemeral=receiver is not None)
    connection_id = getattr(method, "business_connection_id", None)
    connection = None if connection_id is None else env.world.business_connection(connection_id)
    # Every check Telegram makes locally passed; nothing is changed yet.
    env.admit_send(chat)
    values: dict[str, Any] = {
        "message_id": 0 if receiver is not None else chat.allocate_message_id(connection),
        "date": env.world.next_date(),
        "chat": chat.as_chat(),
        **posted_by(chat, env.world.bot_user.as_user()),
    }
    if connection is not None:
        # Telegram sends on behalf of the business account, not the bot.
        values.update(_on_behalf_of(env, connection))
        values["sender_business_bot"] = env.world.bot_user.as_user()
    for name in _COPIED_FIELDS:
        value = getattr(method, name, None)
        if value is not None:
            values[name] = value
    values.update({name: flag for name, flag in media_flags(method).items() if flag is not None})

    reply_markup = getattr(method, "reply_markup", None)
    if isinstance(reply_markup, InlineKeyboardMarkup):
        values["reply_markup"] = reply_markup
    if getattr(method, "protect_content", None):
        values["has_protected_content"] = True
    if thread_id is not None and chat.is_forum:
        values["is_topic_message"] = True
    elif chat.type != ChatType.PRIVATE:
        # The Bot API server passes no topic for a group that is not a
        # forum, so the thread id is dropped there. A private chat's
        # thread was looked up above, so it is kept.
        values.pop("message_thread_id", None)

    values.update(reply)
    if topic is not None:
        values.update(topic.root_reply(values))

    if media_field is not None:
        values[media_field] = stored_content(
            env,
            method,
            media_field,
            getattr(method, media_field, None),
        )
    if content is not None:
        values.update(content())

    if receiver is not None:
        values["ephemeral_message_id"] = chat.allocate_ephemeral_message_id()
        values["receiver_user"] = receiver.as_user()
        return chat.add_ephemeral_message(Message(**values))
    message = Message(**values)
    return chat.add_message(message)


def _sent_kind(method: TelegramMethod[Any], media_field: str | None) -> str:
    """The :data:`_SEND_PERMISSIONS` key of what a send carries."""
    if isinstance(method, SendPoll):
        return "poll"
    if isinstance(method, SendLocation) and method.live_period:
        return "live_location"
    return media_field or "text"


def _on_behalf_of(env: BotTestEnvironment, connection: BusinessConnectionState) -> dict[str, Any]:
    """The sender fields of a message sent for a business account."""
    return {
        "from_user": env.world.user(connection.user_id).as_user(),
        "business_connection_id": connection.id,
    }


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
    legacy_receiver = getattr(method, "receiver_user_id", None)
    if parameters is None and legacy_receiver is not None:
        # The deprecated top-level fields still make a send ephemeral.
        parameters = EphemeralMessageParameters(
            receiver_user_id=legacy_receiver,
            callback_query_id=getattr(method, "callback_query_id", None),
        )
    reply_parameters = getattr(method, "reply_parameters", None)
    replied_id = None if reply_parameters is None else reply_parameters.ephemeral_message_id
    if parameters is None:
        if replied_id is not None:
            raise rejections.REPLY_TO_EPHEMERAL_NOT_EPHEMERAL()
        return None
    if chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
        raise rejections.EPHEMERAL_GROUPS_ONLY()
    receiver = env.world.user(parameters.receiver_user_id)
    if replied_id is not None:
        command = chat.find_ephemeral_command(replied_id)
        if command is None:
            raise rejections.MESSAGE_TO_BE_REPLIED_NOT_FOUND()
        if _age(env, command) > _EPHEMERAL_REPLY_WINDOW:
            raise rejections.EPHEMERAL_REPLY_WINDOW()
    if (
        parameters.replace_callback_query_message
        and parameters.callback_query_id in env.world.ephemeral_callbacks
    ):
        raise rejections.EPHEMERAL_CANT_REPLACE()
    return receiver


def _reply_changes(
    env: BotTestEnvironment,
    method: TelegramMethod[Any],
    chat: ChatState,
    *,
    ephemeral: bool,
) -> dict[str, Any]:
    """
    The reply fields of the message a send stores in ``chat``.

    The target is looked up in the chat ``reply_parameters.chat_id``
    names, or in ``chat``. A target that does not exist fails the send
    unless ``allow_sending_without_reply`` is set, which the Bot API
    reads as false for a reply in another chat or a forum topic and in
    an ephemeral message, and as true on behalf of a business account.
    A target in ``chat`` is the ``reply_to_message``; one in another
    chat is described by ``external_reply``. An ephemeral message or
    one sent on behalf of a business account cannot reply in another
    chat at all, as ``ReplyParameters.chat_id`` states.

    The deprecated top-level ``reply_to_message_id`` and
    ``allow_sending_without_reply`` still name a reply in the same chat
    when ``reply_parameters`` is not passed.
    """
    parameters = getattr(method, "reply_parameters", None)
    if parameters is not None:
        message_id = parameters.message_id
        target_chat = parameters.chat_id
        allow_without_reply = parameters.allow_sending_without_reply
    else:
        message_id = getattr(method, "reply_to_message_id", None)
        target_chat = None
        allow_without_reply = getattr(method, "allow_sending_without_reply", None)
    if message_id is None:
        return {}
    where = chat if target_chat is None else resolve_chat(env, target_chat)
    on_behalf = getattr(method, "business_connection_id", None) is not None
    if where is not chat and (ephemeral or on_behalf):
        raise rejections.REPLY_ELSEWHERE_UNSUPPORTED()
    replied = where.find_message(message_id)
    if replied is None:
        in_topic = chat.is_forum and getattr(method, "message_thread_id", None) is not None
        if on_behalf:
            allowed = True
        elif where is not chat or in_topic or ephemeral:
            allowed = False
        else:
            allowed = bool(allow_without_reply)
        if not allowed:
            raise rejections.MESSAGE_TO_BE_REPLIED_NOT_FOUND()
        return {}
    if where is chat:
        if replied.reply_to_message is not None:
            # The replied message carries no further reply_to_message,
            # as the Bot API states, so a reply chain does not nest.
            replied = replied.model_copy(update={"reply_to_message": None})
        return {"reply_to_message": replied}
    return {"external_reply": _external_reply(env, where, replied)}


#: The ``ExternalReplyInfo`` fields that describe where the replied
#: message is rather than what it carries.
_EXTERNAL_REPLY_PLACE = frozenset({"origin", "chat", "message_id"})

#: The ``ExternalReplyInfo`` fields that carry the content.
_EXTERNAL_REPLY_CONTENT = tuple(
    name for name in ExternalReplyInfo.model_fields if name not in _EXTERNAL_REPLY_PLACE
)


def _external_reply(
    env: BotTestEnvironment,
    where: ChatState,
    replied: Message,
) -> ExternalReplyInfo:
    """
    What a message knows about the message it replies to elsewhere.

    It names the replied message's origin, as a forward would, and
    carries its content. The chat and message id are given only for a
    supergroup or a channel, as ``ExternalReplyInfo`` documents.
    """
    content = {
        name: value
        for name in _EXTERNAL_REPLY_CONTENT
        if (value := getattr(replied, name, None)) is not None
    }
    public = where.type in {ChatType.SUPERGROUP, ChatType.CHANNEL}
    return ExternalReplyInfo(
        origin=forward_origin(where, replied, replied.from_user or env.world.bot_user.as_user()),
        chat=where.as_chat() if public else None,
        message_id=replied.message_id if public else None,
        **content,
    )


#: The highest value each dice emoji can show, as ``Dice`` documents.
_DICE_FACES: dict[str, int] = {
    DiceEmoji.DICE.value: 6,
    DiceEmoji.DART.value: 6,
    DiceEmoji.BOWLING.value: 6,
    DiceEmoji.BASKETBALL.value: 5,
    DiceEmoji.FOOTBALL.value: 5,
    DiceEmoji.SLOT_MACHINE.value: 64,
}


def stored_content(
    env: BotTestEnvironment,
    request: BaseModel,
    field: str,
    uploaded: Any,
) -> Any:
    """
    What a message stores in ``field`` for content a request sent.

    Rich content and checklists convert from what the request stated.
    Anything else is synthesized with the request's own values carried
    over, a dice folded into its emoji's range, and a file given the
    id the request passed or a fresh one, as
    :func:`~aiogram.test.synthesis.with_passed_file` describes.
    """
    if isinstance(uploaded, InputRichMessage):
        return materialize_rich_message(uploaded, env.synthesis_context())
    if isinstance(uploaded, InputChecklist):
        return stored_checklist(uploaded)
    payload = _carry_request_values(
        request,
        nonempty(
            Message.model_fields[field].annotation,
            env.synthesis_context(),
            name=field,
        ),
    )
    if isinstance(payload, Dice):
        faces = _DICE_FACES.get(payload.emoji, 6)
        return payload.model_copy(update={"value": (payload.value - 1) % faces + 1})
    if isinstance(payload, Venue):
        # The request states the venue's place as flat coordinates,
        # which no field of the same name carries over.
        return payload.model_copy(update={"location": _location(request, None)})  # type: ignore[arg-type]
    if isinstance(payload, Invoice):
        # The total is what the request's prices add up to.
        prices = getattr(request, "prices", None) or []
        return payload.model_copy(update={"total_amount": sum(price.amount for price in prices)})
    return with_passed_file(payload, uploaded, env.synthesis_context())


def stored_checklist(checklist: InputChecklist) -> Checklist:
    """
    The checklist a message stores for one a request stated.

    Fields are carried by name, so a field both shapes gain later
    carries over with no change here.
    """
    tasks = [ChecklistTask(**_shared_fields(task, ChecklistTask)) for task in checklist.tasks]
    return Checklist(**{**_shared_fields(checklist, Checklist), "tasks": tasks})


def _shared_fields(source: BaseModel, target: type[BaseModel]) -> dict[str, Any]:
    """The values ``source`` sets for fields ``target`` has too."""
    return {
        name: value
        for name in target.model_fields
        if name in type(source).model_fields and (value := getattr(source, name)) is not None
    }


def _carry_request_values(method: BaseModel, payload: Any) -> Any:
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


def _age(env: BotTestEnvironment, message: Message) -> datetime.timedelta:
    """
    How long ago ``message`` was sent, by the world's clock.

    A test can hand a message a naive ``date``; it is read as local
    time rather than failing to compare with the aware clock.
    """
    return env.world.now - aware(message.date)


def resolve_date(value: Any, now: datetime.datetime) -> datetime.datetime | None:
    """
    The moment a Bot API date parameter names, as an aware datetime.

    aiogram accepts a datetime, a duration from now, or a Unix time. A
    naive datetime is read as local time, the way aiogram's own
    serializer reads it. The Bot API counts in whole seconds, as the
    clock does, so a moment is taken to the second: a date the bot
    computed as ``datetime.now() + delta`` is reached by advancing the
    clock by ``delta``.
    """
    if isinstance(value, datetime.datetime):
        return aware(value).replace(microsecond=0)
    if isinstance(value, datetime.timedelta):
        return (now + value).replace(microsecond=0)
    if isinstance(value, int):
        # Counted from the epoch rather than through fromtimestamp,
        # which refuses a negative time on Windows.
        return UNTIL_FOREVER + datetime.timedelta(seconds=value)
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
    # The moment is in whole seconds, so it is measured from the clock's
    # whole second: a clock advanced by a fraction must not turn a
    # 30-second restriction into a forever one.
    if not shortest <= moment - now.replace(microsecond=0) <= longest:
        return None
    return moment


#: How long the Bot API lets a business message the bot did not send,
#: and that has no inline keyboard, be edited.
_BUSINESS_EDIT_WINDOW = datetime.timedelta(hours=48)


def edit_stamp(env: BotTestEnvironment) -> dict[str, Any]:
    """The change every edit makes: it dates the message's last edit."""
    return {"edit_date": int(env.world.next_date().timestamp())}


def _check_business_edit_window(env: BotTestEnvironment, message: Message) -> None:
    if (
        message.business_connection_id is not None
        and message.sender_business_bot is None
        and message.reply_markup is None
        and _age(env, message) > _BUSINESS_EDIT_WINDOW
    ):
        raise rejections.MESSAGE_CANT_BE_EDITED()


def _check_editable_by_bot(env: BotTestEnvironment, chat: ChatState, message: Message) -> None:
    """
    Refuse an edit of a message the bot may not edit.

    Outside business chats and channels, a bot edits only the messages
    it sent itself: a user's message is not the bot's to change. In a
    business chat it edits the business account's messages, its own
    sent on the account's behalf included, but not the customer's.
    """
    if chat.type == ChatType.CHANNEL:
        return
    sender = message.from_user
    if message.business_connection_id is not None:
        connection = env.world.business_connections.get(message.business_connection_id)
        if (
            connection is None
            or message.sender_business_bot is not None
            or (sender is not None and sender.id == connection.user_id)
        ):
            return
        raise rejections.MESSAGE_CANT_BE_EDITED()
    if sender is None or sender.id != env.world.bot_user.id:
        raise rejections.MESSAGE_CANT_BE_EDITED()


def _edit_target(
    env: BotTestEnvironment,
    method: TelegramMethod[Any],
    *,
    forwarded: Rejection = rejections.MESSAGE_CANT_BE_EDITED,
) -> tuple[ChatState, Message]:
    """
    The chat and stored message an edit targets, or a refusal.

    A forward shows the original's content in another place, so no
    edit method changes it; ``forwarded`` is the refusal's text.
    """
    if getattr(method, "inline_message_id", None) is not None:
        msg = "inline messages are not modeled by the test environment"
        raise WorldLookupError(msg)
    chat = resolve_chat(env, getattr(method, "chat_id", None))
    message_id: int | None = getattr(method, "message_id", None)
    stored = None if message_id is None else chat.find_message(message_id)
    if stored is None or getattr(method, "business_connection_id", None) != (
        stored.business_connection_id
    ):
        # A business message is edited through its connection, and only
        # a business message is: the bot's own chat and the business
        # chat are different places to Telegram.
        raise rejections.MESSAGE_TO_EDIT_NOT_FOUND()
    # Every edit method is bound by these rules, so check them here.
    _check_editable_by_bot(env, chat, stored)
    if stored.forward_origin is not None:
        raise forwarded()
    _check_business_edit_window(env, stored)
    return chat, stored


# -- sending ---------------------------------------------------------------------------


@models(SendMessage, *MEDIA_FIELDS, sends=True)
def handle_send(env: BotTestEnvironment, method: TelegramMethod[Any]) -> Message:
    chat = resolve_chat(env, method.chat_id)  # type: ignore[attr-defined]
    return build_message(env, method, chat, MEDIA_FIELDS.get(type(method)))


@models(SendMediaGroup, sends=True)
def handle_send_media_group(
    env: BotTestEnvironment,
    method: SendMediaGroup,
) -> list[Message]:
    """
    Store one message per item, under one ``media_group_id``.

    Each message carries its item's media and caption. The Bot API
    takes 2-10 items, and groups documents or audio files only with
    items of the same type.
    """
    chat = resolve_chat(env, method.chat_id)
    # The server reads the items before it looks at the chat.
    if not _MEDIA_GROUP_SIZE[0] <= len(method.media) <= _MEDIA_GROUP_SIZE[1]:
        raise rejections.MEDIA_GROUP_SIZE()
    kinds = {media_field(item) for item in method.media}
    if len(kinds) > 1 and kinds & _ALBUM_KINDS.keys():
        raise rejections.MEDIA_GROUP_MIXED()
    require_standing(env, chat)
    posting_topic(env, chat, method.message_thread_id)
    for kind in sorted(kinds):
        require_send_permission(env, chat, kind)
    group: list[str] = []

    def content(item: Any) -> dict[str, Any]:
        # Allocated once the album was let through, on its first item.
        if not group:
            group.append(env.world.next_query_id())
        return _media_group_item(env, item, group[0])

    return [
        build_message(env, method, chat, content=functools.partial(content, item))
        for item in method.media
    ]


#: How many items a media group takes, as ``sendMediaGroup`` states.
_MEDIA_GROUP_SIZE = (2, 10)


def _media_group_item(env: BotTestEnvironment, item: Any, group_id: str) -> dict[str, Any]:
    """What one media group item puts on its message."""
    field = media_field(item)
    return {
        field: stored_content(env, item, field, item.media),
        "caption": item.caption,
        "caption_entities": item.caption_entities,
        **media_flags(item),
        "media_group_id": group_id,
    }


def media_flags(source: BaseModel) -> dict[str, Any]:
    """
    How a request asks its media to be shown, as the message stores it.

    A send method and an input media both spell the spoiler
    ``has_spoiler``, while the message spells it ``has_media_spoiler``.
    """
    return {
        "show_caption_above_media": getattr(source, "show_caption_above_media", None),
        "has_media_spoiler": getattr(source, "has_spoiler", None),
    }


def forward_origin(source: ChatState, original: Message, sender: User) -> Any:
    """
    Where a forwarded message came from — what tells a forward apart from a copy.

    A channel post comes from its channel, and a message sent on
    behalf of a chat, such as an anonymous administrator's, from that
    chat; anything else from ``sender``. The hidden-user origin waits
    for the change that makes hidden senders possible.

    A message that is itself a forward keeps the origin it already
    names, and a channel post's signature moves into its origin.
    """
    if original.forward_origin is not None:
        return original.forward_origin
    if source.type == ChatType.CHANNEL:
        return MessageOriginChannel(
            date=original.date,
            chat=source.as_chat(),
            message_id=original.message_id,
            author_signature=original.author_signature,
        )
    if original.sender_chat is not None:
        return MessageOriginChat(
            date=original.date,
            sender_chat=original.sender_chat,
            author_signature=original.author_signature,
        )
    return MessageOriginUser(date=original.date, sender_user=sender)


#: The ``Message`` fields that carry content: a message with none of
#: them is a service message. Besides what send methods fill, a
#: message can carry a forwarded story or a giveaway.
_CONTENT_FIELDS: frozenset[str] = frozenset(
    {*MEDIA_FIELDS.values(), "text", "poll", "story", "giveaway", "giveaway_winners"},
)

#: Content the Bot API names as impossible to copy, besides service
#: messages.
_UNCOPYABLE_FIELDS = ("invoice", "paid_media", "giveaway", "giveaway_winners")


def is_service_message(message: Message) -> bool:
    """Whether ``message`` carries none of the content sends produce."""
    return all(getattr(message, name) is None for name in _CONTENT_FIELDS)


def _forwardable(message: Message) -> bool:
    """Whether ``message`` is not a service message or protected."""
    return not (message.has_protected_content or is_service_message(message))


def _copyable(message: Message) -> bool:
    """
    Whether ``message`` is none of the kinds copying refuses.

    A quiz copies only when the bot knows its correct answer, as the
    Bot API states: one the bot sent itself, not a user's.
    """
    poll = message.poll
    unknown_quiz = (
        poll is not None
        and poll.type == PollType.QUIZ
        and poll.correct_option_id is None
        and not poll.correct_option_ids
    )
    return not (
        unknown_quiz
        or is_service_message(message)
        or any(getattr(message, name) is not None for name in _UNCOPYABLE_FIELDS)
    )


def _thread_changes(
    env: BotTestEnvironment,
    target: ChatState,
    thread_id: int | None,
) -> dict[str, Any]:
    """
    Where a forward or copy lands within ``target``.

    That is the thread the request names, in a forum, and no thread
    otherwise: the original's thread belongs to its own chat.
    """
    topic = posting_topic(env, target, thread_id)
    if topic is None or topic.is_general:
        return {"message_thread_id": None, "is_topic_message": None}
    return {
        "message_thread_id": thread_id,
        "is_topic_message": True,
        **topic.root_reply({}),
    }


def forward_one(
    env: BotTestEnvironment,
    source: ChatState,
    target: ChatState,
    message_id: int,
    thread_id: int | None = None,
    protect_content: object = None,
    media_group_id: str | None = None,
) -> Message:
    """
    Store a forward of a message in ``target``.

    A single forward stands alone, so it is in no album; a batch passes
    the ``media_group_id`` that keeps an album's forwards together.
    """
    # The server checks the chat and the thread, then TDLib the rest;
    # all before an id is allocated, so a refused forward uses none.
    require_standing(env, target)
    thread = _thread_changes(env, target, thread_id)
    original = source.find_message(message_id)
    if original is None:
        raise rejections.MESSAGE_TO_FORWARD_NOT_FOUND()
    if not _forwardable(original):
        raise rejections.MESSAGE_CANT_BE_FORWARDED()
    require_send_permission(env, target, content_kind(original), forwarded=True)
    env.admit_send(target)
    return target.add_derived(
        original,
        message_id=target.allocate_message_id(),
        chat=target.as_chat(),
        date=env.world.next_date(),
        # Only a user origin reads the sender; the bot stands in
        # for typing.
        forward_origin=forward_origin(
            source,
            original,
            original.from_user or env.world.bot_user.as_user(),
        ),
        **{
            **_new_message_changes(protect_content),
            # After them: a topic's root is the reply a move gets.
            **thread,
            **posted_by(target, env.world.bot_user.as_user()),
            "media_group_id": media_group_id,
        },
    )


def _album_ids(env: BotTestEnvironment, originals: list[Message]) -> dict[str, str]:
    """
    A new ``media_group_id`` per album a batch forwards or copies.

    ``forwardMessages`` and ``copyMessages`` keep album grouping, and
    the new messages are an album of their own chat.
    """
    albums: dict[str, str] = {}
    for original in originals:
        if original.media_group_id is not None and original.media_group_id not in albums:
            albums[original.media_group_id] = env.world.next_query_id()
    return albums


def _new_message_changes(protect_content: object) -> dict[str, Any]:
    """
    What a forward or copy does not take from the original.

    It is a new message of its own chat: not edited, protected only
    when the request asks, and replying to nothing in the original's
    chat, since ``reply_to_message`` is a message of the same chat.
    The bot sends it itself, so it is not a business message even when
    the original was: ``deleteBusinessMessages`` and the business edit
    window must not reach it. Nor is it posted on behalf of the
    original's chat: a channel post's sender chat and signature stay
    with the original, and a forward names them in its origin. It is
    in no album unless a batch keeps one together under a new id. What
    the original's sender or its reply carried, such as a quote or a
    guest query to answer, stays with the original too.
    """
    return {
        "reply_to_message": None,
        "external_reply": None,
        "quote": None,
        "reply_to_story": None,
        "reply_to_checklist_task_id": None,
        "reply_to_poll_option_id": None,
        "guest_query_id": None,
        "sender_boost_count": None,
        "sender_tag": None,
        "edit_date": None,
        "has_protected_content": True if protect_content else None,
        "business_connection_id": None,
        "sender_business_bot": None,
        "sender_chat": None,
        "author_signature": None,
        "media_group_id": None,
        # How the original was sent, not how the bot sends this one.
        "is_automatic_forward": None,
        "is_from_offline": None,
        "is_paid_post": None,
        "paid_star_count": None,
    }


@models(ForwardMessage, sends=True)
def handle_forward(env: BotTestEnvironment, method: ForwardMessage) -> Message:
    source = resolve_chat(env, method.from_chat_id)
    target = resolve_chat(env, method.chat_id)
    return forward_one(
        env,
        source,
        target,
        method.message_id,
        method.message_thread_id,
        method.protect_content,
    )


@models(ForwardMessages, sends=True)
def handle_forward_many(env: BotTestEnvironment, method: ForwardMessages) -> list[MessageId]:
    source = resolve_chat(env, method.from_chat_id)
    target = resolve_chat(env, method.chat_id)
    # Telegram skips what it cannot forward rather than failing the whole batch.
    originals = [
        original
        for message_id in method.message_ids
        if (original := source.find_message(message_id)) is not None and _forwardable(original)
    ]
    # Checked for the whole batch first, so a refusal stores nothing.
    require_standing(env, target)
    posting_topic(env, target, method.message_thread_id)
    for original in originals:
        require_send_permission(env, target, content_kind(original), forwarded=True)
    if originals:
        # Every check passed, so the batch is let through before its
        # albums take ids.
        env.admit_send(target)
    albums = _album_ids(env, originals)
    forwarded = [
        forward_one(
            env,
            source,
            target,
            original.message_id,
            method.message_thread_id,
            method.protect_content,
            albums.get(original.media_group_id or ""),
        )
        for original in originals
    ]
    return [MessageId(message_id=message.message_id) for message in forwarded]


def copy_one(
    env: BotTestEnvironment,
    source: ChatState,
    target: ChatState,
    message_id: int,
    thread_id: int | None = None,
    protect_content: object = None,
    **changes: Any,
) -> Message:
    """
    Store a copy of a message in ``target``.

    ``changes`` are what the request replaces: a caption, an inline
    keyboard, or the album a batch keeps together. The rest is the
    original's.
    """
    require_standing(env, target)
    thread = _thread_changes(env, target, thread_id)
    original = source.find_message(message_id)
    if original is None:
        raise rejections.MESSAGE_TO_COPY_NOT_FOUND()
    if not _copyable(original):
        raise rejections.MESSAGE_CANT_BE_COPIED()
    require_send_permission(env, target, content_kind(original), forwarded=True)
    if all(getattr(original, name) is None for name in CAPTIONED_FIELDS):
        # A caption is for media: a text, sticker or poll copy takes
        # none, whatever the request passed.
        changes = {
            name: value
            for name, value in changes.items()
            if name not in {"caption", "caption_entities", "show_caption_above_media"}
        }
    # Checked before an id or a poll is allocated, so a refused copy
    # uses neither.
    env.admit_send(target)
    if original.poll is not None and "poll" not in changes:
        changes = {**changes, "poll": _copied_poll(env, original.poll)}
    return target.add_derived(
        original,
        message_id=target.allocate_message_id(),
        chat=target.as_chat(),
        date=env.world.next_date(),
        # A copy carries no trace of where it came from — that is the whole difference.
        forward_origin=None,
        **{
            **_new_message_changes(protect_content),
            # After them, and before the request's own reply, which
            # wins over a topic's root.
            **thread,
            **posted_by(target, env.world.bot_user.as_user()),
            # A copy takes only the original's content: its keyboard is
            # the one the request passes, or none.
            "reply_markup": None,
            **changes,
        },
    )


def _correct_option_ids(source: Poll | SendPoll) -> list[int] | None:
    """The correct option ids, or the deprecated single id."""
    if source.correct_option_ids is None and source.correct_option_id is not None:
        return [source.correct_option_id]
    return source.correct_option_ids


def _poll_state(poll: Poll) -> PollState:
    """
    The state a ``Poll`` the world does not hold describes.

    The correct option ids fall back to the deprecated single id, as
    ``sendPoll`` reads them, so a quiz copies with its answer.
    """
    return PollState(
        id=poll.id,
        question=poll.question,
        options=[option.text for option in poll.options],
        is_anonymous=poll.is_anonymous,
        type=poll.type,
        allows_multiple_answers=poll.allows_multiple_answers,
        allows_revoting=bool(poll.allows_revoting),
        members_only=bool(poll.members_only),
        correct_option_ids=_correct_option_ids(poll),
        explanation=poll.explanation,
        is_closed=poll.is_closed,
    )


def _copied_poll(env: BotTestEnvironment, poll: Poll) -> Poll:
    """
    The poll a copy carries: a new poll, unlike a forward's.

    It has its own id and no votes yet, so stopping or voting in one
    of the two leaves the other as it was. It takes no schedule along,
    as nothing would close the copy on it. A poll the world does not
    hold, such as one a user sent, is read off the message.
    """
    stored = env.world.polls.get(poll.id) or _poll_state(poll)
    copied = dataclasses.replace(
        stored,
        id=env.world.next_query_id(),
        options=list(stored.options),
        correct_option_ids=(
            None if stored.correct_option_ids is None else list(stored.correct_option_ids)
        ),
        votes={},
        open_period=None,
        close_date=None,
    )
    env.world.polls[copied.id] = copied
    return copied.as_poll()


@models(CopyMessage, sends=True)
def handle_copy(env: BotTestEnvironment, method: CopyMessage) -> MessageId:
    """
    Copy one message, with what the request replaces.

    A new caption brings its own entities, and the original caption is
    kept when the request names none.
    """
    source = resolve_chat(env, method.from_chat_id)
    target = resolve_chat(env, method.chat_id)
    changes: dict[str, Any] = {}
    if method.caption is not None:
        # An empty caption removes the original one.
        changes["caption"] = method.caption or None
        changes["caption_entities"] = method.caption_entities if method.caption else None
        changes["show_caption_above_media"] = method.show_caption_above_media
    if isinstance(method.reply_markup, InlineKeyboardMarkup):
        changes["reply_markup"] = method.reply_markup
    # The chat and the thread before the message replied to, as the
    # server checks them first.
    require_standing(env, target)
    posting_topic(env, target, method.message_thread_id)
    changes.update(_reply_changes(env, method, target, ephemeral=False))
    copied = copy_one(
        env,
        source,
        target,
        method.message_id,
        method.message_thread_id,
        method.protect_content,
        **changes,
    )
    return MessageId(message_id=copied.message_id)


@models(CopyMessages, sends=True)
def handle_copy_many(env: BotTestEnvironment, method: CopyMessages) -> list[MessageId]:
    source = resolve_chat(env, method.from_chat_id)
    target = resolve_chat(env, method.chat_id)
    changes: dict[str, Any] = {}
    if method.remove_caption:
        changes["caption"] = None
        changes["caption_entities"] = None
        # With no caption there is nothing to show above the media.
        changes["show_caption_above_media"] = None
    # Telegram skips what it cannot copy rather than failing the batch.
    originals = [
        original
        for message_id in method.message_ids
        if (original := source.find_message(message_id)) is not None and _copyable(original)
    ]
    # Checked for the whole batch first, so a refusal stores nothing.
    require_standing(env, target)
    posting_topic(env, target, method.message_thread_id)
    for original in originals:
        require_send_permission(env, target, content_kind(original), forwarded=True)
    if originals:
        # Every check passed, so the batch is let through before its
        # albums take ids.
        env.admit_send(target)
    albums = _album_ids(env, originals)
    copied = [
        copy_one(
            env,
            source,
            target,
            original.message_id,
            method.message_thread_id,
            method.protect_content,
            media_group_id=albums.get(original.media_group_id or ""),
            **changes,
        )
        for original in originals
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
        "show_caption_above_media": method.show_caption_above_media,
        "reply_markup": method.reply_markup,
    }


#: What ``editMessageText`` edits: text, rich and game messages.
_TEXT_FIELDS = ("text", "rich_message", "game")

#: The content a caption sits on: that of every send method taking
#: one, read off the methods so the set follows the Bot API.
CAPTIONED_FIELDS: tuple[str, ...] = tuple(
    field for method, field in MEDIA_FIELDS.items() if "caption" in method.model_fields
)


def _require_content(message: Message | None, fields: tuple[str, ...], kind: str) -> None:
    """Refuse to edit ``kind`` on a message with none of ``fields``."""
    if message is not None and all(getattr(message, name) is None for name in fields):
        raise rejections.NO_CONTENT_TO_EDIT(kind=kind)


@models(EditMessageText)
def handle_edit_text(env: BotTestEnvironment, method: EditMessageText) -> Message:
    chat, stored = _edit_target(env, method)
    message_id = stored.message_id
    # The message is found first; its new text is TDLib's to check.
    refuse_blank_text(method)
    _require_content(stored, _TEXT_FIELDS, "text")
    return chat.update_message(message_id, **edit_stamp(env), **_text_changes(env, method))


@models(EditMessageCaption)
def handle_edit_caption(env: BotTestEnvironment, method: EditMessageCaption) -> Message:
    chat, stored = _edit_target(env, method)
    message_id = stored.message_id
    _require_content(stored, CAPTIONED_FIELDS, "caption")
    return chat.update_message(message_id, **edit_stamp(env), **_caption_changes(method))


@models(EditMessageReplyMarkup)
def handle_edit_reply_markup(
    env: BotTestEnvironment,
    method: EditMessageReplyMarkup,
) -> Message:
    chat, stored = _edit_target(env, method)
    message_id = stored.message_id
    return chat.update_message(message_id, **edit_stamp(env), reply_markup=method.reply_markup)


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
    changes[field] = stored_content(env, method.media, field, method.media.media)
    changes["caption"] = method.media.caption
    changes["caption_entities"] = method.media.caption_entities
    # The new media brings its own presentation, or none.
    changes.update(media_flags(method.media))
    if method.reply_markup is not None:
        changes["reply_markup"] = method.reply_markup
    return changes


#: What ``editMessageMedia`` replaces: media, or a text or rich message.
_MEDIA_EDIT_SOURCES = (*EDITABLE_MEDIA_FIELDS, "text", "rich_message")

#: The media an album item can be edited to, by what the album holds:
#: audio and documents keep their kind, the rest take visual media.
_ALBUM_KINDS: dict[str, frozenset[str]] = {
    "audio": frozenset({"audio"}),
    "document": frozenset({"document"}),
}
_VISUAL_ALBUM_KINDS = frozenset({"photo", "live_photo", "video"})


def _check_media_edit(
    stored: Message, method: EditMessageMedia | EditEphemeralMessageMedia
) -> None:
    """
    Refuse an ``editMessageMedia`` the Bot API does not allow.

    It edits media messages and replaces text or rich messages, and an
    album item stays in its album's kind, as the method documents.
    """
    _require_content(stored, _MEDIA_EDIT_SOURCES, "media")
    if stored.media_group_id is None:
        return
    allowed = next(
        (kinds for kind, kinds in _ALBUM_KINDS.items() if getattr(stored, kind) is not None),
        _VISUAL_ALBUM_KINDS,
    )
    if media_field(method.media) not in allowed:
        raise rejections.ALBUM_ITEM_EDIT(kinds=", ".join(sorted(allowed)))


@models(EditMessageMedia)
def handle_edit_media(env: BotTestEnvironment, method: EditMessageMedia) -> Message:
    chat, stored = _edit_target(env, method)
    message_id = stored.message_id
    _check_media_edit(stored, method)
    return chat.update_message(message_id, **edit_stamp(env), **_media_changes(env, method))


# An ephemeral message is addressed by chat, receiver and ephemeral
# id, so these act on the chat's store of the bot's ephemeral
# messages, never on its shared history. Each returns True, as the
# Bot API declares.


_EphemeralEdit = (
    EditEphemeralMessageText
    | EditEphemeralMessageCaption
    | EditEphemeralMessageMedia
    | EditEphemeralMessageReplyMarkup
)


def _edit_ephemeral(env: BotTestEnvironment, method: _EphemeralEdit, **changes: Any) -> bool:
    chat = resolve_chat(env, method.chat_id)
    chat.update_ephemeral_message(
        method.receiver_user_id,
        method.ephemeral_message_id,
        **edit_stamp(env),
        **changes,
    )
    return True


def _stored_ephemeral(env: BotTestEnvironment, method: _EphemeralEdit) -> Message:
    """
    The ephemeral message an edit targets, or a refusal.

    Checked before the new content is built, so a refused edit
    registers no file and uses up no file number.
    """
    chat = resolve_chat(env, method.chat_id)
    message = chat.find_ephemeral_message(method.receiver_user_id, method.ephemeral_message_id)
    if message is None:
        raise rejections.MESSAGE_TO_EDIT_NOT_FOUND()
    return message


@models(EditEphemeralMessageText)
def handle_edit_ephemeral_text(env: BotTestEnvironment, method: EditEphemeralMessageText) -> bool:
    stored = _stored_ephemeral(env, method)
    refuse_blank_text(method)
    _require_content(stored, _TEXT_FIELDS, "text")
    return _edit_ephemeral(env, method, **_text_changes(env, method))


@models(EditEphemeralMessageCaption)
def handle_edit_ephemeral_caption(
    env: BotTestEnvironment,
    method: EditEphemeralMessageCaption,
) -> bool:
    _require_content(_stored_ephemeral(env, method), CAPTIONED_FIELDS, "caption")
    return _edit_ephemeral(env, method, **_caption_changes(method))


@models(EditEphemeralMessageMedia)
def handle_edit_ephemeral_media(
    env: BotTestEnvironment,
    method: EditEphemeralMessageMedia,
) -> bool:
    _check_media_edit(_stored_ephemeral(env, method), method)
    return _edit_ephemeral(env, method, **_media_changes(env, method))


@models(EditEphemeralMessageReplyMarkup)
def handle_edit_ephemeral_reply_markup(
    env: BotTestEnvironment,
    method: EditEphemeralMessageReplyMarkup,
) -> bool:
    return _edit_ephemeral(env, method, reply_markup=method.reply_markup)


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


def _require_live(env: BotTestEnvironment, stored: Message) -> Location:
    """
    A location that is still live, or a refusal.

    The Bot API lets a live location be edited or stopped "until its
    live_period expires" or it is stopped; a static location never was.
    """
    location = stored.location
    current = location.live_period if location is not None else None
    if (
        location is None
        or current is None
        or (current != LIVE_FOREVER and _age(env, stored) >= datetime.timedelta(seconds=current))
    ):
        raise rejections.MESSAGE_CANT_BE_EDITED()
    return location


@models(EditMessageLiveLocation)
def handle_edit_live_location(
    env: BotTestEnvironment,
    method: EditMessageLiveLocation,
) -> Message:
    chat, stored = _edit_target(env, method)
    message_id = stored.message_id
    # A live location always has a period; `or 0` only narrows the type.
    current = _require_live(env, stored).live_period or 0
    now = env.world.now
    live_period = method.live_period
    if live_period is None:
        # Omitting live_period leaves the existing one running, it does not end it.
        live_period = current
    elif live_period != LIVE_FOREVER:
        ends = aware(stored.date) + datetime.timedelta(seconds=live_period)
        if current != LIVE_FOREVER and live_period > current + _DAY:
            raise rejections.LIVE_PERIOD_EXTENDED_TOO_FAR()
        if ends > now + datetime.timedelta(days=90):
            raise rejections.LIVE_PERIOD_ENDS_TOO_LATE()
    return chat.update_message(
        message_id,
        **edit_stamp(env),
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
    chat, stored = _edit_target(env, method)
    message_id = stored.message_id
    location = _require_live(env, stored)
    return chat.update_message(
        message_id,
        **edit_stamp(env),
        reply_markup=method.reply_markup,
        location=location.model_copy(update={"live_period": None}),
    )


@models(EditMessageChecklist)
def handle_edit_checklist(
    env: BotTestEnvironment,
    method: EditMessageChecklist,
) -> Message:
    chat, stored = _edit_target(env, method)
    message_id = stored.message_id
    _require_content(stored, ("checklist",), "checklist")
    return chat.update_message(
        message_id,
        **edit_stamp(env),
        checklist=stored_checklist(method.checklist),
        reply_markup=method.reply_markup,
    )


#: The Bot API's age limits on deletion: a message older than this
#: cannot be deleted, and a dice in a private chat younger than the
#: second cannot.
_DELETABLE_FOR = datetime.timedelta(hours=48)
_PRIVATE_DICE_KEPT_FOR = datetime.timedelta(hours=24)


#: Service messages the Bot API names as never deletable: those about a
#: supergroup, channel, or forum topic creation.
_UNDELETABLE_SERVICE_FIELDS = (
    "supergroup_chat_created",
    "channel_chat_created",
    "forum_topic_created",
)


def _deletable(env: BotTestEnvironment, chat: ChatState, message: Message) -> bool:
    if any(getattr(message, name) for name in _UNDELETABLE_SERVICE_FIELDS):
        return False
    age = _age(env, message)
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
        raise rejections.MESSAGE_TO_DELETE_NOT_FOUND()
    if not (_deletable(env, chat, message) and bot_may_delete(env, chat, message)):
        raise rejections.MESSAGE_CANT_BE_DELETED()
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
        if (
            message is not None
            and _deletable(env, chat, message)
            and bot_may_delete(env, chat, message)
        ):
            chat.delete_message(message_id)
    return True


@models(PinChatMessage)
def handle_pin(env: BotTestEnvironment, method: PinChatMessage) -> bool:
    """
    Pin a message, and post the service message Telegram posts for it.

    The service message carries the pinned message without its own
    ``reply_to_message``, as the Bot API states. A message already
    pinned is not announced again.
    """
    chat = resolve_chat(env, method.chat_id)
    pinned = None if method.message_id is None else chat.find_message(method.message_id)
    if pinned is None:
        raise rejections.MESSAGE_TO_PIN_NOT_FOUND()
    connection = (
        None
        if method.business_connection_id is None
        else env.world.business_connection(method.business_connection_id)
    )
    if pinned.message_id in chat.pinned_message_ids:
        return True
    chat.pinned_message_ids.append(pinned.message_id)
    fields: dict[str, Any] = {
        "pinned_message": pinned.model_copy(update={"reply_to_message": None}),
    }
    if connection is not None:
        # Pinned on behalf of the business account, which announces it.
        fields.update(_on_behalf_of(env, connection))
    thread_id = pinned.message_thread_id if pinned.is_topic_message else None
    service_message(env, chat, fields, thread_id, connection)
    return True


@models(UnpinChatMessage)
def handle_unpin(env: BotTestEnvironment, method: UnpinChatMessage) -> bool:
    """
    Unpin a message, or without an id the most recent pin by date.

    Messages sent in the same second are told apart by id.
    """
    chat = resolve_chat(env, method.chat_id)
    if method.message_id is None:
        pinned = [
            message
            for message_id in chat.pinned_message_ids
            if (message := chat.find_message(message_id)) is not None
        ]
        if pinned:
            newest = max(pinned, key=lambda message: (aware(message.date), message.message_id))
            chat.pinned_message_ids.remove(newest.message_id)
    elif method.message_id in chat.pinned_message_ids:
        chat.pinned_message_ids.remove(method.message_id)
    return True


@models(UnpinAllChatMessages)
def handle_unpin_all(env: BotTestEnvironment, method: UnpinAllChatMessages) -> bool:
    chat = resolve_chat(env, method.chat_id)
    chat.pinned_message_ids.clear()
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
            # The same file as the one the id names everywhere else.
            "file_unique_id": unique_file_id(method.file_id),
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
        raise rejections.NO_PERSONAL_CHAT()
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
    ``unbanChatMember`` follows it too, since by default it removes a
    present member.
    """
    member = chat.member(user_id)
    if member.status == ChatMemberStatus.CREATOR:
        # TDLib's text, from its supergroup and channel path. In a basic
        # group the server decides, and its answer is not in the open
        # source; the toolkit gives its usual one.
        if chat.type == ChatType.GROUP:
            raise rejections.CHAT_ADMIN_REQUIRED()
        raise rejections.OWNER_PROTECTED()
    return member


@models(BanChatMember)
def handle_ban(env: BotTestEnvironment, method: BanChatMember) -> bool:
    chat = resolve_chat(env, method.chat_id)
    member = _not_the_owner(chat, method.user_id)
    member.set_status(ChatMemberStatus.KICKED)
    # A banned user cannot join, so a pending request of theirs goes
    # too: approving it would otherwise lift the ban.
    chat.join_requests.discard(method.user_id)
    # The Bot API applies `until_date` for supergroups and channels
    # only, so a ban in a basic group has no end, whatever end an
    # earlier restriction had.
    member.until_date = (
        None if chat.type == ChatType.GROUP else normalize_until(method.until_date, env.world.now)
    )
    return True


def _supergroup_or_channel(env: BotTestEnvironment, chat_id: Any) -> ChatState:
    """
    The chat a call names, refused unless a supergroup or a channel.

    As the Bot API server refuses unbanning and promoting elsewhere
    (Client.cpp, ``process_unban_chat_member_query``).
    """
    chat = resolve_chat(env, chat_id)
    if chat.type not in _SUPERGROUP_OR_CHANNEL:
        raise rejections.SUPERGROUP_OR_CHANNEL_ONLY()
    return chat


@models(UnbanChatMember)
def handle_unban(env: BotTestEnvironment, method: UnbanChatMember) -> bool:
    """
    Leave the user free to join, and outside the chat.

    By default the Bot API also removes a user who is a member, so the
    call always ends with the user absent. ``only_if_banned`` limits it
    to a banned user, leaving anyone else as they are.
    """
    chat = _supergroup_or_channel(env, method.chat_id)
    member = chat.member(method.user_id)
    if method.only_if_banned and member.status != ChatMemberStatus.KICKED:
        return True
    # Removing a present member is the default, and the owner cannot
    # be removed, the same as for a ban.
    _not_the_owner(chat, method.user_id)
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
    chat = _supergroup_or_channel(env, method.chat_id)
    member = _not_the_owner(chat, method.user_id)
    if (
        member.status == ChatMemberStatus.ADMINISTRATOR
        and member.promoted_by is not None
        and member.promoted_by != env.world.bot_user.id
    ):
        # The bot may edit only the administrators it promoted, which
        # is what ``can_be_edited`` reports; one known to be promoted
        # by someone else is not the bot's to edit or demote.
        raise rejections.NO_RIGHTS_TO_EDIT_ADMINISTRATOR()
    granted = mask(ChatAdministratorRights, method, coerce=True)
    if not any(granted.values()):
        # Demotion takes away an administrator's standing only: it
        # neither lifts a restriction or a ban nor brings anyone in.
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            member.set_status(ChatMemberStatus.MEMBER)
        member.rights = None
        member.custom_title = None
        return True
    was_administrator = member.status == ChatMemberStatus.ADMINISTRATOR
    member.set_status(ChatMemberStatus.ADMINISTRATOR)
    member.rights = ChatAdministratorRights(**granted)
    if not was_administrator:
        # Editing an administrator's rights does not make the bot the
        # one who promoted them, so ``can_be_edited`` stays truthful.
        member.promoted_by = env.world.bot_user.id
    return True


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

    Restricting is for supergroups only, as the method states.
    """
    chat = resolve_chat(env, method.chat_id)
    if chat.type != ChatType.SUPERGROUP:
        raise rejections.SUPERGROUPS_ONLY()
    member = _not_the_owner(chat, method.user_id)
    granted = granted_permissions(
        method.permissions,
        method.use_independent_chat_permissions,
    )
    if all(mask(ChatPermissions, granted, coerce=True).values()):
        if member.status == ChatMemberStatus.RESTRICTED:
            member.lift_restriction()
        return True
    member.set_status(ChatMemberStatus.RESTRICTED)
    member.permissions = granted
    member.rights = None
    member.until_date = normalize_until(method.until_date, env.world.now)
    return True


@models(LeaveChat)
def handle_leave(env: BotTestEnvironment, method: LeaveChat) -> bool:
    chat = resolve_chat(env, method.chat_id)
    # Leaving is leaving however it happens: a restriction outlives it.
    chat.member(env.world.bot_user.id).join_or_leave(ChatMemberStatus.LEFT)
    return True


@models(GetChatMember)
def handle_get_chat_member(env: BotTestEnvironment, method: GetChatMember) -> Any:
    chat = resolve_chat(env, method.chat_id)
    user = env.world.user(method.user_id)
    return chat.member(method.user_id).as_chat_member(
        user.as_user(),
        chat.type,
        env.world.bot_user.id,
    )


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
            "is_forum": chat.reported_forum,
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
    return env.world.bot_me()


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
        file_unique_id=unique_file_id(file_id),
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
        raise rejections.STICKER_SET_OCCUPIED()
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
    return synthesized.model_copy(
        update={
            "file_id": file_id,
            "file_unique_id": unique_file_id(file_id),
            "file_path": file_id,
        },
    )


@models(GetCustomEmojiStickers)
def handle_get_custom_emoji_stickers(
    env: BotTestEnvironment,
    method: GetCustomEmojiStickers,
) -> list[Sticker]:
    """One sticker per requested id, echoing it, so a lookup can be correlated."""
    return [
        Sticker(
            file_id=custom_emoji_id,
            file_unique_id=unique_file_id(custom_emoji_id),
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
        file_unique_id=unique_file_id(f"{gift_id}-sticker"),
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


def _spend(
    env: BotTestEnvironment,
    amount: int,
    charge_id: str | None = None,
    partner_id: int | None = None,
) -> None:
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
        partner_id=partner_id,
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
        transactions=[
            item.as_star_transaction(
                None if item.partner_id is None else env.world.user(item.partner_id).as_user(),
            )
            for item in env.world.stars.transactions
        ],
    )


@models(RefundStarPayment)
def handle_refund_star_payment(env: BotTestEnvironment, method: RefundStarPayment) -> bool:
    charge = env.world.stars.charge(method.telegram_payment_charge_id)
    if charge.user_id != method.user_id:
        # A charge is refunded to the user who paid it.
        raise rejections.CHARGE_NOT_PAID_BY(charge=charge.id, user_id=method.user_id)
    if charge.is_refunded:
        raise rejections.CHARGE_REFUNDED(charge=charge.id)
    charge.is_refunded = True
    _spend(env, charge.amount, charge_id=charge.id, partner_id=charge.user_id)
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
        raise rejections.GIFT_NEEDS_RECIPIENT()
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
        raise rejections.SUBSCRIPTION_PERIOD(period=SUBSCRIPTION_PERIOD)
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
        raise rejections.NOT_A_SUBSCRIPTION_LINK()
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
        raise rejections.SUPERGROUP_OR_CHANNEL_ONLY()
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
    Store the chat's permissions, which the bot's sends then obey.

    The checks of what a member may send read this value, see
    :func:`require_send_permission`, and so do a user's topic rights.
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
        member.as_chat_member(
            env.world.user(member.user_id).as_user(),
            chat.type,
            env.world.bot_user.id,
        )
        for member in admins
    ]


def _annotated_member(
    env: BotTestEnvironment,
    method: TelegramMethod[Any],
    allowed: set[str],
    complaint: Rejection,
) -> MemberState:
    chat = resolve_chat(env, method.chat_id)  # type: ignore[attr-defined]
    user_id: int = method.user_id  # type: ignore[attr-defined]
    env.world.user(user_id)
    member = chat.member(user_id)
    if member.status not in allowed:
        raise complaint()
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
        rejections.NOT_AN_ADMINISTRATOR,
    )
    if member.promoted_by is not None and member.promoted_by != env.world.bot_user.id:
        # The title is the bot's to set only on an administrator it
        # promoted, as for `promoteChatMember`.
        raise rejections.NO_RIGHTS_TO_CHANGE_CUSTOM_TITLE()
    member.custom_title = method.custom_title
    return True


@models(SetChatMemberTag)
def handle_set_member_tag(env: BotTestEnvironment, method: SetChatMemberTag) -> bool:
    """A tag belongs to a regular member; an administrator carries a custom title instead."""
    member = _annotated_member(
        env,
        method,
        {ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED},
        rejections.NOT_A_REGULAR_MEMBER,
    )
    if not member.is_present:
        # A restriction outlives leaving, but a user outside the chat
        # is not one of its members to tag.
        raise rejections.USER_NOT_A_MEMBER()
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
        raise rejections.POLL_PERIOD_CONFLICT()
    now = env.world.now
    moment: datetime.datetime | None
    if method.open_period is not None:
        start = now
        moment = now + datetime.timedelta(seconds=method.open_period)
    else:
        # A close date is in whole seconds, so it is measured from the
        # clock's whole second, as `normalize_until` measures an end.
        start = now.replace(microsecond=0)
        moment = resolve_date(method.close_date, now)
    if moment is None:
        return None
    shortest, longest = _POLL_SCHEDULE_RANGE
    if not shortest <= (moment - start).total_seconds() <= longest:
        raise rejections.POLL_SCHEDULE_RANGE(shortest=shortest, longest=longest)
    return moment


def _close_poll(
    env: BotTestEnvironment,
    poll: PollState,
    origin: tuple[ChatState, int] | None = None,
    **changes: Any,
) -> Poll:
    """
    Close ``poll`` and show it closed on every message that carries it.

    A forward carries the same poll as its original, so it closes with
    it. ``changes``, such as a new keyboard, apply to the message
    ``origin`` names, the one the poll was sent in, and to no other.
    """
    poll.is_closed = True
    for holder in env.world.chats.values():
        carriers = [
            message.message_id
            for message in holder.messages
            if message.poll is not None and message.poll.id == poll.id
        ]
        for message_id in carriers:
            own = origin is not None and holder is origin[0] and message_id == origin[1]
            holder.update_message(message_id, poll=poll.as_poll(), **(changes if own else {}))
    return poll.as_poll()


@models(SendPoll, sends=True)
def handle_send_poll(env: BotTestEnvironment, method: SendPoll) -> Message:
    """
    Store a poll with the defaults the Bot API documents.

    The correct option ids fall back to the deprecated single id.
    """
    chat = resolve_chat(env, method.chat_id)
    close_at = _poll_close(env, method)
    # Checked now, numbered once the send went through.
    poll = new_poll(
        "",
        method.question,
        [option if isinstance(option, str) else option.text for option in method.options],
        poll_type=method.type,
        is_anonymous=method.is_anonymous,
        allows_multiple_answers=method.allows_multiple_answers,
        allows_revoting=method.allows_revoting,
        correct_option_ids=_correct_option_ids(method),
        members_only=bool(method.members_only),
        explanation=method.explanation,
        is_closed=bool(method.is_closed),
        open_period=method.open_period,
        close_date=close_at,
    )
    message = build_message(env, method, chat)
    # Registered once the send went through, so a refused one leaves no
    # poll behind to vote in.
    poll.id = env.world.next_query_id()
    env.world.polls[poll.id] = poll
    if close_at is not None and not poll.is_closed:
        message_id = message.message_id

        async def close() -> None:
            # A poll stopped before its moment does not close twice.
            if poll.is_closed:
                return
            if chat.find_message(message_id) is None:
                # Its message is gone, but the poll still closes on
                # schedule, so no answer counts after its close date.
                _close_poll(env, poll)
                return
            closed = _close_poll(env, poll, (chat, message_id))
            await env.feed(Update(update_id=env.world.next_update_id(), poll=closed))

        env.schedule(close_at, close)
    return chat.update_message(message.message_id, poll=poll.as_poll())


@models(StopPoll)
def handle_stop_poll(env: BotTestEnvironment, method: StopPoll) -> Poll:
    """
    Stop a poll through the original message that carries it.

    ``stopPoll`` names "the original message with the poll", so a
    forward of it, which carries the same poll, is refused.
    """
    chat, stored = _edit_target(
        env, method, forwarded=rejections.MESSAGE_WITH_POLL_TO_STOP_NOT_FOUND
    )
    message_id = stored.message_id
    if stored.poll is None:
        raise rejections.NO_POLL()
    poll = env.world.poll(stored.poll.id)
    if poll.is_closed:
        raise rejections.POLL_CLOSED()
    # The keyboard is the one the request passes, or none.
    return _close_poll(env, poll, (chat, message_id), reply_markup=method.reply_markup)


# -- reactions -------------------------------------------------------------------------


def _reaction_target(
    env: BotTestEnvironment, method: TelegramMethod[Any]
) -> tuple[ChatState, int]:
    chat = resolve_chat(env, method.chat_id)  # type: ignore[attr-defined]
    message_id: int = method.message_id  # type: ignore[attr-defined]
    if chat.find_message(message_id) is None:
        raise rejections.MESSAGE_TO_REACT_NOT_FOUND()
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
        raise rejections.JOIN_REQUEST_NOT_PENDING()
    chat.join_requests.discard(user_id)
    return chat


@models(ApproveChatJoinRequest)
def handle_approve_join_request(
    env: BotTestEnvironment,
    method: ApproveChatJoinRequest,
) -> bool:
    chat = _pending_request(env, method)
    # An approved user joins as any other does: a restriction stays.
    chat.member(method.user_id).join_or_leave(ChatMemberStatus.MEMBER)
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
    connection: BusinessConnectionState | None = None,
    *,
    sender: User | None = None,
) -> Message:
    """
    Emit a service message the way Telegram posts one for an administrative action.

    One posted on behalf of a business account is numbered by its
    ``connection`` too, as every business message is. It is from the
    ``sender``, the bot unless a user actor took the action. A service
    message carries no ``author_signature``: Telegram's
    ``messageService`` has no post author.
    """
    values: dict[str, Any] = {
        "message_id": chat.allocate_message_id(connection),
        "date": env.world.next_date(),
        "chat": chat.as_chat(),
        **posted_by(chat, sender or env.world.bot_user.as_user()),
        **fields,
    }
    if thread_id is not None:
        values["message_thread_id"] = thread_id
        values["is_topic_message"] = True
        # The caller checked the topic, so a gap here is the toolkit's.
        values.update(chat.topic(thread_id).root_reply(values))
    return chat.add_message(Message(**values))


#: The forum methods a private chat takes too: TDLib lets a bot
#: create, edit and delete the topics of its private chats, the
#: General topic's name included (ForumTopicManager.cpp,
#: ``is_forum`` with ``allow_bots``), while closing, reopening and
#: hiding are a supergroup's.
#: Unpinning a topic's messages is let through as well; that TDLib
#: allows it there is not checked.
_PRIVATE_TOPIC_METHODS: frozenset[type[TelegramMethod[Any]]] = frozenset(
    {CreateForumTopic, EditForumTopic, DeleteForumTopic, UnpinAllForumTopicMessages},
)


def forum_chat(env: BotTestEnvironment, chat_id: Any, *, private: bool = False) -> ChatState:
    """
    The chat a forum method names, refused unless it is a forum.

    A supergroup whose owner turned topics off keeps them, so it is
    refused by its state rather than by having none. A private chat
    is one with ``private``, and refused in TDLib's words otherwise.
    The bot's topic mode in private chats is not modeled: every
    private chat takes topics.
    """
    chat = resolve_chat(env, chat_id)
    if chat.type == ChatType.PRIVATE:
        if not private:
            raise rejections.NOT_A_SUPERGROUP_FORUM()
        return chat
    if not chat.is_forum:
        raise rejections.NOT_A_FORUM()
    return chat


def _topic(env: BotTestEnvironment, method: TelegramMethod[Any]) -> tuple[ChatState, TopicState]:
    chat_id = method.chat_id  # type: ignore[attr-defined]
    chat = forum_chat(env, chat_id, private=type(method) in _PRIVATE_TOPIC_METHODS)
    return chat, chat.topic_for_call(getattr(method, "message_thread_id", None))


@models(CreateForumTopic)
def handle_create_forum_topic(env: BotTestEnvironment, method: CreateForumTopic) -> ForumTopic:
    chat = forum_chat(env, method.chat_id, private=True)
    topic = create_topic(
        chat,
        name=method.name,
        date=env.world.next_date(),
        icon_color=method.icon_color or DEFAULT_TOPIC_ICON_COLOR,
        icon_custom_emoji_id=method.icon_custom_emoji_id,
        from_user=env.world.bot_user.as_user(),
        creator_id=env.world.bot_user.id,
    )
    return topic.as_forum_topic()


@models(EditForumTopic)
def handle_edit_forum_topic(env: BotTestEnvironment, method: EditForumTopic) -> bool:
    """
    Edit a topic's name and icon.

    An empty name keeps the current one, and an empty emoji id removes
    the icon, as the Bot API documents.
    """
    chat, topic = _topic(env, method)
    if method.name:
        topic.name = method.name
    if method.icon_custom_emoji_id is not None:
        topic.icon_custom_emoji_id = method.icon_custom_emoji_id or None
    service_message(
        env,
        chat,
        {
            "forum_topic_edited": ForumTopicEdited(
                name=method.name or None,
                icon_custom_emoji_id=method.icon_custom_emoji_id,
            ),
        },
        topic.message_thread_id,
    )
    return True


def close_topic(
    env: BotTestEnvironment,
    chat: ChatState,
    topic: TopicState,
    *,
    by: User | None = None,
) -> Message:
    """Close ``topic``, and post the service message that says so."""
    topic.is_closed = True
    return service_message(
        env,
        chat,
        {"forum_topic_closed": ForumTopicClosed()},
        topic.message_thread_id,
        sender=by,
    )


def reopen_topic(
    env: BotTestEnvironment,
    chat: ChatState,
    topic: TopicState,
    *,
    by: User | None = None,
) -> Message:
    """Reopen ``topic``, and post the service message that says so."""
    topic.is_closed = False
    return service_message(
        env,
        chat,
        {"forum_topic_reopened": ForumTopicReopened()},
        topic.message_thread_id,
        sender=by,
    )


def delete_topic(chat: ChatState, topic: TopicState) -> None:
    """
    Delete ``topic`` with every message in it.

    Telegram posts no service message for it, and the Bot API has no
    type for one. The thread id is remembered as deleted.
    """
    for message in list(topic.messages):
        chat.delete_message(message.message_id)
    if topic.message_thread_id is not None:
        del chat.topics[topic.message_thread_id]
        chat.deleted_topic_ids.add(topic.message_thread_id)


def hide_general(
    env: BotTestEnvironment,
    chat: ChatState,
    *,
    by: User | None = None,
) -> Message:
    """Hide the General topic, which closes it, and post a message."""
    chat.general_topic.is_hidden = True
    # Hiding the General topic closes it too.
    chat.general_topic.is_closed = True
    return service_message(
        env, chat, {"general_forum_topic_hidden": GeneralForumTopicHidden()}, sender=by
    )


def unhide_general(
    env: BotTestEnvironment,
    chat: ChatState,
    *,
    by: User | None = None,
) -> Message:
    """Unhide the General topic, and post the service message."""
    chat.general_topic.is_hidden = False
    return service_message(
        env,
        chat,
        {"general_forum_topic_unhidden": GeneralForumTopicUnhidden()},
        sender=by,
    )


def close_general(
    env: BotTestEnvironment,
    chat: ChatState,
    *,
    by: User | None = None,
) -> Message:
    """
    Close the General topic, and post ``forum_topic_closed``.

    It goes through ``messages.editForumTopic`` as any topic does
    (ForumTopicManager.cpp), so the service message is the same.
    """
    chat.general_topic.is_closed = True
    return service_message(env, chat, {"forum_topic_closed": ForumTopicClosed()}, sender=by)


def reopen_general(
    env: BotTestEnvironment,
    chat: ChatState,
    *,
    by: User | None = None,
) -> Message:
    """
    Reopen the General topic, which unhides it too.

    One ``forum_topic_reopened`` says both, as TDLib reports the edit
    that reopens and unhides it (ForumTopicEditedData.cpp).
    """
    chat.general_topic.is_closed = False
    chat.general_topic.is_hidden = False
    return service_message(env, chat, {"forum_topic_reopened": ForumTopicReopened()}, sender=by)


@models(CloseForumTopic)
def handle_close_forum_topic(env: BotTestEnvironment, method: CloseForumTopic) -> bool:
    chat, topic = _topic(env, method)
    close_topic(env, chat, topic)
    return True


@models(ReopenForumTopic)
def handle_reopen_forum_topic(env: BotTestEnvironment, method: ReopenForumTopic) -> bool:
    chat, topic = _topic(env, method)
    reopen_topic(env, chat, topic)
    return True


@models(DeleteForumTopic)
def handle_delete_forum_topic(env: BotTestEnvironment, method: DeleteForumTopic) -> bool:
    chat, topic = _topic(env, method)
    delete_topic(chat, topic)
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
    # Allowed in a private chat as well: neither the server nor TDLib
    # checks the type (Client.cpp, ForumTopicManager.cpp).
    chat = forum_chat(env, method.chat_id, private=True)
    chat.general_topic.name = method.name
    return True


@models(CloseGeneralForumTopic)
def handle_close_general_forum_topic(
    env: BotTestEnvironment,
    method: CloseGeneralForumTopic,
) -> bool:
    close_general(env, forum_chat(env, method.chat_id))
    return True


@models(ReopenGeneralForumTopic)
def handle_reopen_general_forum_topic(
    env: BotTestEnvironment,
    method: ReopenGeneralForumTopic,
) -> bool:
    reopen_general(env, forum_chat(env, method.chat_id))
    return True


@models(HideGeneralForumTopic)
def handle_hide_general_forum_topic(
    env: BotTestEnvironment,
    method: HideGeneralForumTopic,
) -> bool:
    hide_general(env, forum_chat(env, method.chat_id))
    return True


@models(UnhideGeneralForumTopic)
def handle_unhide_general_forum_topic(
    env: BotTestEnvironment,
    method: UnhideGeneralForumTopic,
) -> bool:
    unhide_general(env, forum_chat(env, method.chat_id))
    return True


@models(UnpinAllGeneralForumTopicMessages)
def handle_unpin_all_general_forum_topic_messages(
    env: BotTestEnvironment,
    method: UnpinAllGeneralForumTopicMessages,
) -> bool:
    chat = forum_chat(env, method.chat_id)
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
        raise rejections.MESSAGE_TO_READ_NOT_FOUND()
    return True


@models(DeleteBusinessMessages)
def handle_delete_business_messages(
    env: BotTestEnvironment,
    method: DeleteBusinessMessages,
) -> bool:
    """
    Delete business messages, all of them from one chat.

    The method names no chat: the account numbers its business
    messages from one sequence, so the ids find their chat. Ids held
    by more than one chat mix chats, which the Bot API refuses.
    """
    connection = env.world.business_connection(method.business_connection_id)
    wanted = set(method.message_ids)
    held = {
        chat.id: ids
        for chat in env.world.chats.values()
        if (
            ids := {
                message.message_id
                for message in chat.messages
                if message.message_id in wanted and message.business_connection_id == connection.id
            }
        )
    }
    if len(held) > 1:
        raise rejections.MIXED_CHATS()
    for chat_id, ids in held.items():
        chat = env.world.chat(chat_id)
        for message_id in sorted(ids):
            chat.delete_message(message_id)
    return True
