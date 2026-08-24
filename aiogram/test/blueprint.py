from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.types import (
    BotCommand,
    BusinessBotRights,
    ChatAdministratorRights,
    ChatPermissions,
    ChatPhoto,
    MenuButtonUnion,
    Sticker,
)

from .world import (
    BASE_DATE,
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
    create_topic,
    scope_key,
)

DEFAULT_TOKEN = "42:TEST"
FALLBACK_BOT_ID = 42
FIRST_USER_ID = 1000
FIRST_GROUP_ID = -1000
FIRST_SUPERGROUP_ID = -1001000000000
FIRST_COMMUNITY_ID = 5000


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


@dataclass
class MemberSpec:
    """Declaration of a user's membership in a chat."""

    user_id: int
    status: str = ChatMemberStatus.MEMBER
    custom_title: str | None = None
    tag: str | None = None


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
    permissions: ChatPermissions | None = None
    photo: ChatPhoto | None = None
    sticker_set_name: str | None = None
    invite_links: list[InviteLinkState] = field(default_factory=list)
    members: list[MemberSpec] = field(default_factory=list)


@dataclass(eq=False)
class TopicSpec:
    """Declaration of a forum topic. Compared by identity so it works as a handle."""

    chat_id: int
    name: str
    icon_color: int = DEFAULT_TOPIC_ICON_COLOR
    icon_custom_emoji_id: str | None = None
    message_thread_id: int | None = field(default=None, compare=False)


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
    ) -> None:
        self.token = token
        self.default = default or DefaultBotProperties()
        self.bot_id = _token_bot_id(token)
        self.bot = UserSpec(
            id=self.bot_id,
            is_bot=True,
            first_name=bot_first_name,
            username=bot_username,
        )
        self.users: list[UserSpec] = []
        self.chats: list[ChatSpec] = []
        self.topics: list[TopicSpec] = []
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
    ) -> UserSpec:
        user = UserSpec(
            id=id if id is not None else FIRST_USER_ID + len(self.users),
            first_name=first_name,
            last_name=last_name,
            username=username,
            language_code=language_code,
        )
        self.users.append(user)
        return user

    def add_private_chat(self, user: UserSpec) -> ChatSpec:
        """A private chat between the bot and ``user``; its id is the user's id."""
        chat = ChatSpec(
            id=user.id,
            type=ChatType.PRIVATE,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            members=[MemberSpec(user_id=user.id)],
        )
        self.chats.append(chat)
        return chat

    def add_group(
        self,
        title: str = "Group",
        *,
        members: dict[UserSpec, str] | None = None,
        id: int | None = None,
    ) -> ChatSpec:
        return self._add_group_like(
            chat_type=ChatType.GROUP,
            title=title,
            members=members,
            chat_id=id if id is not None else FIRST_GROUP_ID - len(self.chats),
        )

    def add_supergroup(
        self,
        title: str = "Supergroup",
        *,
        members: dict[UserSpec, str] | None = None,
        id: int | None = None,
    ) -> ChatSpec:
        return self._add_group_like(
            chat_type=ChatType.SUPERGROUP,
            title=title,
            members=members,
            chat_id=id if id is not None else FIRST_SUPERGROUP_ID - len(self.chats),
        )

    def add_channel(
        self,
        title: str = "Channel",
        *,
        members: dict[UserSpec, str] | None = None,
        id: int | None = None,
    ) -> ChatSpec:
        return self._add_group_like(
            chat_type=ChatType.CHANNEL,
            title=title,
            members=members,
            chat_id=id if id is not None else FIRST_SUPERGROUP_ID - len(self.chats),
        )

    def _add_group_like(
        self,
        chat_type: str,
        title: str,
        members: dict[UserSpec, str] | None,
        chat_id: int,
    ) -> ChatSpec:
        chat = ChatSpec(
            id=chat_id,
            type=chat_type,
            title=title,
            members=[
                MemberSpec(user_id=user.id, status=status)
                for user, status in (members or {}).items()
            ],
        )
        chat.members.append(MemberSpec(user_id=self.bot.id, status=ChatMemberStatus.MEMBER))
        self.chats.append(chat)
        return chat

    def add_topic(
        self,
        chat: ChatSpec,
        name: str = "Topic",
        *,
        icon_color: int = DEFAULT_TOPIC_ICON_COLOR,
        icon_custom_emoji_id: str | None = None,
    ) -> TopicSpec:
        """Declare a forum topic. The chat becomes a forum."""
        topic = TopicSpec(
            chat_id=chat.id,
            name=name,
            icon_color=icon_color,
            icon_custom_emoji_id=icon_custom_emoji_id,
        )
        self.topics.append(topic)
        return topic

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
                    file_unique_id=f"{name}-{index + 1}-unique",
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

    def build(self) -> World:
        """Materialize an independent world. The blueprint itself is left untouched."""
        spec = copy.deepcopy(self)
        world = World(
            bot_user=_user_state(spec.bot),
            profile=spec.profile,
            files=spec.files,
            stars=StarLedger(opening_balance=spec.star_balance),
            owned_gifts={gift.owned_gift_id: gift for gift in spec.owned_gifts},
            sticker_sets={item.name: item for item in spec.sticker_sets},
        )
        for user in spec.users:
            world.users[user.id] = _user_state(user)
        for chat in spec.chats:
            world.chats[chat.id] = ChatState(
                id=chat.id,
                type=chat.type,
                title=chat.title,
                username=chat.username,
                first_name=chat.first_name,
                last_name=chat.last_name,
                description=chat.description,
                permissions=chat.permissions,
                photo=chat.photo,
                sticker_set_name=chat.sticker_set_name,
                invite_links=list(chat.invite_links),
                members={
                    member.user_id: MemberState(
                        user_id=member.user_id,
                        status=member.status,
                        custom_title=member.custom_title,
                        tag=member.tag,
                    )
                    for member in chat.members
                },
            )
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
            )
        for index, topic in enumerate(spec.topics):
            # Declared topics go through the same path as `createForumTopic`, so a
            # declared world is indistinguishable from one built by API calls.
            created = create_topic(
                world.chat(topic.chat_id),
                name=topic.name,
                date=BASE_DATE,
                icon_color=topic.icon_color,
                icon_custom_emoji_id=topic.icon_custom_emoji_id,
            )
            self.topics[index].message_thread_id = created.message_thread_id
        return world


def _token_bot_id(token: str) -> int:
    head = token.split(":", maxsplit=1)[0]
    return int(head) if head.isdigit() else FALLBACK_BOT_ID


def _user_state(spec: UserSpec) -> UserState:
    return UserState(
        id=spec.id,
        is_bot=spec.is_bot,
        first_name=spec.first_name,
        last_name=spec.last_name,
        username=spec.username,
        language_code=spec.language_code,
    )


def default_blueprint() -> Blueprint:
    """The zero-configuration world: one user in a private chat with the bot."""
    blueprint = Blueprint()
    user = blueprint.add_user("Test", username="test_user", language_code="en")
    blueprint.add_private_chat(user)
    return blueprint
