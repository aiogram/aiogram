from __future__ import annotations

import copy
import datetime
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, TypeAlias

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.types import (
    BotCommand,
    BusinessBotRights,
    ChatAdministratorRights,
    ChatPermissions,
    ChatPhoto,
    MenuButtonUnion,
    Message,
    Sticker,
)

from .synthesis import unique_file_id
from .world import (
    DEFAULT_TOPIC_ICON_COLOR,
    BotProfileState,
    BusinessConnectionState,
    ChatState,
    CommunityState,
    InviteLinkState,
    MemberState,
    OwnedGiftState,
    StarLedger,
    StickerSetState,
    UserState,
    World,
    aware,
    create_topic,
    default_chat_permissions,
    granted_permissions,
    new_poll,
    posted_by,
    private_chat_shape,
    quiz_problem,
    scope_key,
    wall_clock,
)

DEFAULT_TOKEN = "42:TEST"
FALLBACK_BOT_ID = 42
FIRST_USER_ID = 1000
FIRST_GROUP_ID = -1000
FIRST_SUPERGROUP_ID = -1001000000000
FIRST_COMMUNITY_ID = 5000


def free_id(
    explicit: int | None,
    first: int,
    step: int,
    taken: Collection[int],
    kind: str,
) -> int:
    """
    The id asked for, or the first free one counting from ``first``.

    The one allocation a blueprint and a running environment share,
    each passing the ids it has taken. An ``explicit`` id already
    taken raises :class:`ValueError`.
    """
    if explicit is not None:
        if explicit in taken:
            msg = f"{kind} {explicit} already exists in this world"
            raise ValueError(msg)
        return explicit
    candidate = first
    while candidate in taken:
        candidate += step
    return candidate


class _Identified(Protocol):
    @property
    def id(self) -> int: ...


class _Acting(Protocol):
    """A user actor, as a member is named by one."""

    @property
    def user(self) -> _Identified: ...


#: How a member is named: by declaration, by actor or by id.
UserRef: TypeAlias = "UserSpec | _Acting | int"


def user_ref_id(user: UserRef) -> int:
    """The id of the user ``user`` names."""
    if isinstance(user, int):
        return user
    if isinstance(user, UserSpec):
        return user.id
    return user.user.id


@dataclass(eq=False)
class UserSpec:
    """
    Declaration of a user, returned by :meth:`Blueprint.add_user` as a handle.

    Compared by identity so it can be used as a dict key when declaring memberships.
    """

    id: int
    is_bot: bool = False
    first_name: str = "User"
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    #: Bot-to-Bot Communication Mode, for a bot; see
    #: :meth:`Blueprint.add_user`.
    bot_to_bot_mode: bool = False


@dataclass
class MemberSpec:
    """
    Declaration of a user's membership in a chat.

    ``rights`` and ``permissions`` say what the membership *allows*, which the status alone
    does not: an administrator without declared rights has the ordinary ones, but an
    administrator the test declared as lacking one is the whole point of a test that checks
    the bot warns about a missing right. Declare either through
    :meth:`Blueprint.set_member`.
    """

    user_id: int
    status: str = ChatMemberStatus.MEMBER
    custom_title: str | None = None
    tag: str | None = None
    rights: ChatAdministratorRights | None = None
    permissions: ChatPermissions | None = None


@dataclass(eq=False)
class ChatSpec:
    """Declaration of a chat. Returned by the ``add_*_chat`` helpers as a handle."""

    id: int
    type: str = ChatType.PRIVATE
    title: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    description: str | None = None
    #: What members may do. ``None`` is every permission in a group or
    #: a supergroup, see :func:`~aiogram.test.default_chat_permissions`,
    #: and nothing in a private chat or a channel.
    permissions: ChatPermissions | None = None
    photo: ChatPhoto | None = None
    sticker_set_name: str | None = None
    invite_links: list[InviteLinkState] = field(default_factory=list)
    members: list[MemberSpec] = field(default_factory=list)
    #: Whether topics are on. Declaring a topic turns them on too.
    is_forum: bool = False


@dataclass(eq=False)
class TopicSpec:
    """Declaration of a forum topic. Compared by identity so it works as a handle."""

    chat_id: int
    name: str
    icon_color: int = DEFAULT_TOPIC_ICON_COLOR
    icon_custom_emoji_id: str | None = None
    message_thread_id: int | None = field(default=None, compare=False)
    #: Who opened the topic, by id, or ``None`` for no one; see
    #: :meth:`Blueprint.add_topic`.
    creator_id: int | None = None


@dataclass(eq=False)
class PollSpec:
    """
    Declaration of a poll the bot already sent. Compared by identity.

    ``poll_id`` and ``message_id`` are filled in by
    :meth:`Blueprint.build`, so a test can vote in the poll by its id.
    """

    chat_id: int
    question: str
    options: list[str]
    type: str | None = None
    is_anonymous: bool | None = None
    allows_multiple_answers: bool | None = None
    allows_revoting: bool | None = None
    correct_option_ids: list[int] | None = None
    explanation: str | None = None
    poll_id: str | None = field(default=None, compare=False)
    message_id: int | None = field(default=None, compare=False)


@dataclass(eq=False)
class BusinessConnectionSpec:
    """Declaration of a business account connection."""

    id: str
    user_id: int
    user_chat_id: int
    is_enabled: bool = True
    can_reply: bool = True
    rights: BusinessBotRights | None = None


@dataclass(eq=False)
class CommunitySpec:
    """Declaration of a community and the chats attached to it."""

    id: int
    name: str
    chat_ids: list[int] = field(default_factory=list)


class Blueprint:
    """
    Declarative description of a test world.

    A blueprint holds no runtime state: :meth:`build` deep-copies it into a fresh
    :class:`~aiogram.test.world.World`, so the same blueprint can safely be shared by
    any number of tests at any pytest scope.
    """

    def __init__(
        self,
        *,
        token: str = DEFAULT_TOKEN,
        default: DefaultBotProperties | None = None,
        bot_first_name: str = "Bot",
        bot_username: str = "test_bot",
        bot_to_bot_mode: bool = False,
        bot_group_privacy: bool = True,
    ) -> None:
        """
        ``bot_to_bot_mode`` and ``bot_group_privacy`` are what the bot set in
        @BotFather: Bot-to-Bot Communication Mode, off by default, and
        Group Privacy, on by default. They decide which messages of
        other bots reach it, see :meth:`add_user`, and ``getMe``
        reports privacy off as ``can_read_all_group_messages``.
        """
        self.token = token
        self.default = default or DefaultBotProperties()
        self.bot_id = _token_bot_id(token)
        self.bot = UserSpec(
            id=self.bot_id,
            is_bot=True,
            first_name=bot_first_name,
            username=bot_username,
            bot_to_bot_mode=bot_to_bot_mode,
        )
        self.bot_group_privacy = bot_group_privacy
        self.users: list[UserSpec] = []
        self.chats: list[ChatSpec] = []
        #: Ids a running environment has taken already, so a blueprint
        #: it declares with allocates around them.
        self.taken_user_ids: set[int] = set()
        self.taken_chat_ids: set[int] = set()
        self.topics: list[TopicSpec] = []
        self.polls: list[PollSpec] = []
        self.business_connections: list[BusinessConnectionSpec] = []
        self.communities: list[CommunitySpec] = []
        self.profile = BotProfileState()
        self.files: dict[str, bytes] = {}
        self.star_balance = 0
        self.owned_gifts: list[OwnedGiftState] = []
        self.sticker_sets: list[StickerSetState] = []

    # -- declaration ------------------------------------------------------------------

    def add_user(
        self,
        first_name: str = "User",
        *,
        last_name: str | None = None,
        username: str | None = None,
        language_code: str | None = None,
        id: int | None = None,
        is_bot: bool = False,
        bot_to_bot_mode: bool = False,
    ) -> UserSpec:
        """
        Declare a user, or with ``is_bot`` another bot.

        Another bot acts through ``env.user(...)`` as a user does,
        and its messages carry ``is_bot``. ``bot_to_bot_mode`` is its
        Bot-to-Bot Communication Mode, which only a bot has: a
        message it posts in a group reaches the bot under test only
        when Telegram would deliver it, see the testing guide.
        """
        if bot_to_bot_mode and not is_bot:
            msg = "Only a bot has Bot-to-Bot Communication Mode; pass `is_bot=True`"
            raise ValueError(msg)
        taken = {*self.taken_user_ids, *(user.id for user in self.users), self.bot.id}
        user = UserSpec(
            id=free_id(
                id,
                FIRST_USER_ID + len(self.users) + len(self.taken_user_ids),
                1,
                taken,
                "User",
            ),
            first_name=first_name,
            last_name=last_name,
            username=username,
            language_code=language_code,
            is_bot=is_bot,
            bot_to_bot_mode=bot_to_bot_mode,
        )
        self.users.append(user)
        return user

    def add_private_chat(self, user: UserSpec) -> ChatSpec:
        """A private chat between the bot and ``user``; its id is the user's id."""
        chat = ChatSpec(**private_chat_shape(user), members=[MemberSpec(user_id=user.id)])
        self.chats.append(chat)
        return chat

    def add_group(
        self,
        title: str = "Group",
        *,
        members: Mapping[UserRef, str] | None = None,
        id: int | None = None,
        bot_status: str | None = None,
        permissions: ChatPermissions | None = None,
    ) -> ChatSpec:
        """
        Declare a basic group.

        ``permissions`` are what its members may do. Without them
        the group grants every permission, see
        :func:`~aiogram.test.default_chat_permissions`.
        """
        return self._add_group_like(
            chat_type=ChatType.GROUP,
            title=title,
            members=members,
            chat_id=self._chat_id(id, FIRST_GROUP_ID),
            bot_status=bot_status,
            permissions=permissions,
        )

    def add_supergroup(
        self,
        title: str = "Supergroup",
        *,
        members: Mapping[UserRef, str] | None = None,
        id: int | None = None,
        bot_status: str | None = None,
        is_forum: bool = False,
        permissions: ChatPermissions | None = None,
    ) -> ChatSpec:
        """
        Declare a supergroup.

        ``is_forum`` turns its topics on before any is declared, as for
        a forum whose topics the bot creates itself. ``permissions`` are
        what its members may do; without them it grants every one,
        :func:`~aiogram.test.default_chat_permissions`.
        """
        chat = self._add_group_like(
            chat_type=ChatType.SUPERGROUP,
            title=title,
            members=members,
            chat_id=self._chat_id(id, FIRST_SUPERGROUP_ID),
            bot_status=bot_status,
            permissions=permissions,
        )
        chat.is_forum = is_forum
        return chat

    def add_channel(
        self,
        title: str = "Channel",
        *,
        members: Mapping[UserRef, str] | None = None,
        id: int | None = None,
        bot_status: str | None = None,
    ) -> ChatSpec:
        return self._add_group_like(
            chat_type=ChatType.CHANNEL,
            title=title,
            members=members,
            chat_id=self._chat_id(id, FIRST_SUPERGROUP_ID),
            bot_status=bot_status,
        )

    def _chat_id(self, explicit: int | None, first: int) -> int:
        """A new chat's id, counting down from ``first``."""
        taken = {*self.taken_chat_ids, *(chat.id for chat in self.chats)}
        return free_id(explicit, first - len(taken), -1, taken, "Chat")

    def _add_group_like(
        self,
        chat_type: str,
        title: str,
        members: Mapping[UserRef, str] | None,
        chat_id: int,
        bot_status: str | None = None,
        permissions: ChatPermissions | None = None,
    ) -> ChatSpec:
        statuses = {user_ref_id(user): status for user, status in (members or {}).items()}
        bot_membership = statuses.get(self.bot.id)
        # `bot_status` and a `members[blueprint.bot]` entry are two ways of saying the
        # same thing; accepting both silently would let one shadow the other, so passing
        # `bot_status` (any value, including MEMBER) alongside an explicit entry is
        # rejected as ambiguous rather than letting one silently win.
        if bot_membership is not None and bot_status is not None:
            msg = (
                "The bot's status was given both via `members` and via `bot_status`; "
                "pass only one of them."
            )
            raise ValueError(msg)
        chat = ChatSpec(
            id=chat_id,
            type=chat_type,
            title=title,
            permissions=permissions,
            members=[
                MemberSpec(user_id=user_id, status=status) for user_id, status in statuses.items()
            ],
        )
        # Almost every group bot's first move is checking its own rights, so the bot is
        # always a member of the chats it is declared into — as itself if `members`
        # already named it, otherwise appended with `bot_status` (default: MEMBER).
        if bot_membership is None:
            chat.members.append(
                MemberSpec(user_id=self.bot.id, status=bot_status or ChatMemberStatus.MEMBER)
            )
        self.chats.append(chat)
        return chat

    def set_member(
        self,
        chat: ChatSpec,
        user: UserSpec,
        *,
        status: str | None = None,
        rights: ChatAdministratorRights | None = None,
        permissions: ChatPermissions | None = None,
        custom_title: str | None = None,
        tag: str | None = None,
    ) -> MemberSpec:
        """
        Declare, or amend, one member of a declared chat.

        The ``members=`` shorthand of the ``add_*`` helpers says what a user *is*; this says
        what they may **do**, which is what a bot gating itself on a right actually reads.
        The bot is a member like any other, so "the bot is an admin but cannot delete
        messages" — the case behind every "I can't do that, give me the right" branch — is
        declarable::

            team = blueprint.add_supergroup("Team")
            blueprint.set_member(
                team,
                blueprint.bot,
                rights=administrator_rights(can_delete_messages=False),
            )

        Passing ``rights`` or ``permissions`` implies the status that carries it, so the
        common cases are one call; an explicit ``status`` wins. The two belong to different
        statuses, so declaring both for one member is rejected rather than silently
        resolved.
        """
        if rights is not None and permissions is not None:
            msg = (
                "A member is either an administrator with `rights` or a restricted member "
                "with `permissions`; pass only one of them."
            )
            raise ValueError(msg)
        member = next((item for item in chat.members if item.user_id == user.id), None)
        if member is None:
            member = MemberSpec(user_id=user.id)
            chat.members.append(member)
        if status is not None:
            member.status = status
        elif rights is not None:
            member.status = ChatMemberStatus.ADMINISTRATOR
        elif permissions is not None:
            member.status = ChatMemberStatus.RESTRICTED
        if rights is not None:
            member.rights = rights
        if permissions is not None:
            member.permissions = permissions
        if custom_title is not None:
            member.custom_title = custom_title
        if tag is not None:
            member.tag = tag
        return member

    def add_topic(
        self,
        chat: ChatSpec,
        name: str = "Topic",
        *,
        icon_color: int = DEFAULT_TOPIC_ICON_COLOR,
        icon_custom_emoji_id: str | None = None,
        creator: UserRef | None = None,
    ) -> TopicSpec:
        """
        Declare a forum topic. The chat becomes a forum.

        ``creator`` is who opened it: a declared user, by spec, actor
        or id, or ``blueprint.bot``. Its ``forum_topic_created`` is
        from them, and they get a creator's exemptions: the bot posts
        into its own closed topic and edits, closes, reopens and
        deletes it without ``can_manage_topics``, and a user actor
        closes, reopens and deletes it.

        Without one, the topic is no one's, so no one gets those
        exemptions, though its ``forum_topic_created`` is from the
        bot, as it always was.
        """
        topic = TopicSpec(
            chat_id=chat.id,
            name=name,
            icon_color=icon_color,
            icon_custom_emoji_id=icon_custom_emoji_id,
            creator_id=None if creator is None else user_ref_id(creator),
        )
        self.topics.append(topic)
        return topic

    def add_poll(
        self,
        chat: ChatSpec,
        question: str,
        options: list[str],
        *,
        type: str | None = None,
        is_anonymous: bool | None = None,
        allows_multiple_answers: bool | None = None,
        allows_revoting: bool | None = None,
        correct_option_ids: list[int] | None = None,
        explanation: str | None = None,
    ) -> PollSpec:
        """
        Declare a poll the bot already sent into ``chat``.

        It is stored as ``sendPoll`` stores one, on a message from the
        bot, with the same defaults. A quiz needs its correct option
        ids, as ``sendPoll`` requires.
        """
        problem = quiz_problem(type, list(options), correct_option_ids)
        if problem is not None:
            raise ValueError(problem.description)
        poll = PollSpec(
            chat_id=chat.id,
            question=question,
            options=list(options),
            type=type,
            is_anonymous=is_anonymous,
            allows_multiple_answers=allows_multiple_answers,
            allows_revoting=allows_revoting,
            correct_option_ids=correct_option_ids,
            explanation=explanation,
        )
        self.polls.append(poll)
        return poll

    def add_business_connection(
        self,
        owner: UserSpec,
        *,
        id: str | None = None,
        is_enabled: bool = True,
        can_reply: bool = True,
        rights: BusinessBotRights | None = None,
    ) -> BusinessConnectionSpec:
        """Declare a business connection the bot acts on behalf of."""
        connection = BusinessConnectionSpec(
            id=id if id is not None else f"bc-{len(self.business_connections) + 1}",
            user_id=owner.id,
            user_chat_id=owner.id,
            is_enabled=is_enabled,
            can_reply=can_reply,
            rights=rights,
        )
        self.business_connections.append(connection)
        return connection

    def add_community(
        self,
        name: str = "Community",
        *,
        chats: list[ChatSpec] | None = None,
        id: int | None = None,
    ) -> CommunitySpec:
        """Declare a community and attach chats to it."""
        community = CommunitySpec(
            id=id if id is not None else FIRST_COMMUNITY_ID + len(self.communities),
            name=name,
            chat_ids=[chat.id for chat in chats or []],
        )
        self.communities.append(community)
        return community

    def add_invite_link(
        self,
        chat: ChatSpec,
        *,
        url: str | None = None,
        name: str | None = None,
        member_limit: int | None = None,
        creates_join_request: bool = False,
        is_primary: bool = False,
    ) -> InviteLinkState:
        """Declare an invite link the chat already has."""
        link = InviteLinkState(
            invite_link=url or f"https://t.me/+declared-{len(chat.invite_links) + 1}",
            creator_id=self.bot.id,
            name=name,
            member_limit=member_limit,
            creates_join_request=creates_join_request,
            is_primary=is_primary,
        )
        chat.invite_links.append(link)
        return link

    def add_sticker_set(
        self,
        name: str,
        title: str = "Pack",
        *,
        sticker_type: str = "regular",
        stickers: int = 1,
    ) -> StickerSetState:
        """Declare a sticker set the bot already owns, carrying ``stickers`` stickers."""
        sticker_set = StickerSetState(
            name=name,
            title=title,
            sticker_type=sticker_type,
            stickers=[
                Sticker(
                    file_id=f"{name}-{index + 1}",
                    file_unique_id=unique_file_id(f"{name}-{index + 1}"),
                    type=sticker_type,
                    width=512,
                    height=512,
                    is_animated=False,
                    is_video=False,
                )
                for index in range(stickers)
            ],
        )
        self.sticker_sets.append(sticker_set)
        return sticker_set

    def set_star_balance(self, amount: int) -> Blueprint:
        """Declare the stars the bot starts with, so a test need not earn them first."""
        self.star_balance = amount
        return self

    def add_owned_gift(
        self,
        owner: UserSpec | ChatSpec,
        gift_id: str = "gift-star",
        *,
        star_count: int = 15,
        is_unique: bool = False,
    ) -> OwnedGiftState:
        """Declare a gift somebody already owns."""
        gift = OwnedGiftState(
            owned_gift_id=f"owned-{len(self.owned_gifts) + 1}",
            gift_id=gift_id,
            owner_id=owner.id,
            star_count=star_count,
            is_unique=is_unique,
        )
        self.owned_gifts.append(gift)
        return gift

    def add_file(self, file_id: str, content: bytes) -> str:
        """Declare downloadable content for a file id, and return that id."""
        self.files[file_id] = content
        return file_id

    def set_bot_commands(
        self,
        commands: list[BotCommand],
        *,
        scope: Any = None,
        language_code: str | None = None,
    ) -> Blueprint:
        """Declare commands the bot has already registered, for one scope and language."""
        self.profile.commands[scope_key(scope, language_code)] = list(commands)
        return self

    def set_bot_profile(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        short_description: str | None = None,
        language_code: str | None = None,
        menu_button: MenuButtonUnion | None = None,
        menu_button_chat: ChatSpec | None = None,
        default_admin_rights: ChatAdministratorRights | None = None,
        for_channels: bool = False,
    ) -> Blueprint:
        """Declare the bot's own profile as if it had already been configured."""
        profile = self.profile
        if name is not None:
            profile.set_localized(profile.name, language_code, name)
        if description is not None:
            profile.set_localized(profile.description, language_code, description)
        if short_description is not None:
            profile.set_localized(profile.short_description, language_code, short_description)
        if menu_button is not None:
            profile.menu_buttons[menu_button_chat.id if menu_button_chat else None] = menu_button
        if default_admin_rights is not None:
            profile.default_admin_rights[for_channels] = default_admin_rights
        return self

    # -- materialization --------------------------------------------------------------

    def build(self, start: datetime.datetime | None = None) -> World:
        """
        Materialize an independent world, leaving the blueprint as is.

        The world's clock starts at ``start``, or at the real time, to
        the second, when none is given.
        """
        spec = copy.deepcopy(self)
        world = World(
            now=aware(start) if start is not None else wall_clock(),
            bot_user=user_state(spec.bot),
            profile=spec.profile,
            files=spec.files,
            stars=StarLedger(opening_balance=spec.star_balance),
            owned_gifts={gift.owned_gift_id: gift for gift in spec.owned_gifts},
            sticker_sets={item.name: item for item in spec.sticker_sets},
            bot_group_privacy=spec.bot_group_privacy,
        )
        for user in spec.users:
            world.users[user.id] = user_state(user)
        for chat in spec.chats:
            world.chats[chat.id] = chat_state(chat)
        for community in spec.communities:
            world.communities[community.id] = CommunityState(
                id=community.id,
                name=community.name,
                chat_ids=list(community.chat_ids),
            )
            for chat_id in community.chat_ids:
                world.chat(chat_id).community_id = community.id
        for connection in spec.business_connections:
            world.business_connections[connection.id] = BusinessConnectionState(
                id=connection.id,
                user_id=connection.user_id,
                user_chat_id=connection.user_chat_id,
                is_enabled=connection.is_enabled,
                can_reply=connection.can_reply,
                rights=connection.rights,
                # Dated by the clock, as declared topics and polls are.
                date=world.now,
            )
        for index, topic in enumerate(spec.topics):
            # Declared topics go through the same path as `createForumTopic`, so a
            # declared world is indistinguishable from one built by API calls.
            opener = world.bot_user if topic.creator_id is None else world.user(topic.creator_id)
            created = create_topic(
                world.chat(topic.chat_id),
                name=topic.name,
                date=world.now,
                icon_color=topic.icon_color,
                icon_custom_emoji_id=topic.icon_custom_emoji_id,
                from_user=opener.as_user(),
                creator_id=topic.creator_id,
            )
            self.topics[index].message_thread_id = created.message_thread_id
        for index, declared in enumerate(spec.polls):
            # Stored as `sendPoll` stores one, for the same reason.
            target = world.chat(declared.chat_id)
            poll = new_poll(
                world.next_query_id(),
                declared.question,
                declared.options,
                poll_type=declared.type,
                is_anonymous=declared.is_anonymous,
                allows_multiple_answers=declared.allows_multiple_answers,
                allows_revoting=declared.allows_revoting,
                correct_option_ids=declared.correct_option_ids,
                explanation=declared.explanation,
                chat_id=target.id,
            )
            world.polls[poll.id] = poll
            message = target.add_message(
                Message(
                    message_id=target.allocate_message_id(),
                    date=world.now,
                    chat=target.as_chat(),
                    **posted_by(target, world.bot_user.as_user()),
                    poll=poll.as_poll(),
                ),
            )
            self.polls[index].poll_id = poll.id
            self.polls[index].message_id = message.message_id
        return world


def _chat_permissions(chat: ChatSpec) -> ChatPermissions | None:
    """
    What a declared chat lets its members do.

    A group or a supergroup that declares nothing grants every
    permission, and a private chat or a channel has no permissions
    to report.
    """
    if chat.permissions is None and chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
        return default_chat_permissions()
    return _granted(chat.permissions)


def _granted(permissions: ChatPermissions | None) -> ChatPermissions | None:
    """Declared permissions as the API would store the same request."""
    if permissions is None:
        return None
    return granted_permissions(permissions, use_independent_chat_permissions=None)


def _token_bot_id(token: str) -> int:
    head = token.split(":", maxsplit=1)[0]
    return int(head) if head.isdigit() else FALLBACK_BOT_ID


def chat_state(spec: ChatSpec) -> ChatState:
    """
    The state a declared chat starts as.

    The one place a chat declaration is turned into a chat, for
    :meth:`Blueprint.build` and for the chats a running environment
    adds, so a chat added late is shaped exactly like a declared one.
    """
    return ChatState(
        id=spec.id,
        type=spec.type,
        title=spec.title,
        username=spec.username,
        first_name=spec.first_name,
        last_name=spec.last_name,
        description=spec.description,
        permissions=_chat_permissions(spec),
        photo=spec.photo,
        sticker_set_name=spec.sticker_set_name,
        invite_links=list(spec.invite_links),
        is_forum=spec.is_forum,
        members={
            member.user_id: MemberState(
                user_id=member.user_id,
                status=member.status,
                custom_title=member.custom_title,
                tag=member.tag,
                rights=member.rights,
                permissions=_granted(member.permissions),
            )
            for member in spec.members
        },
    )


def user_state(spec: UserSpec) -> UserState:
    """The state a declared user starts as; see :func:`chat_state`."""
    return UserState(
        id=spec.id,
        is_bot=spec.is_bot,
        first_name=spec.first_name,
        last_name=spec.last_name,
        username=spec.username,
        language_code=spec.language_code,
        bot_to_bot_mode=spec.bot_to_bot_mode,
    )


def default_blueprint() -> Blueprint:
    """The zero-configuration world: one user in a private chat with the bot."""
    blueprint = Blueprint()
    user = blueprint.add_user("Test", username="test_user", language_code="en")
    blueprint.add_private_chat(user)
    return blueprint
