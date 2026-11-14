from typing import Annotated

from pydantic import Field, TypeAdapter

from aiogram.types import (
    ChatMember,
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
)

ChatMemberUnion = (
    ChatMemberOwner
    | ChatMemberAdministrator
    | ChatMemberMember
    | ChatMemberRestricted
    | ChatMemberLeft
    | ChatMemberBanned
)

ChatMemberCollection = tuple[type[ChatMember], ...]

ChatMemberAdapter: TypeAdapter[ChatMemberUnion] = TypeAdapter(
    Annotated[
        ChatMemberUnion,
        Field(discriminator="status"),
    ],
)

ADMINS: ChatMemberCollection = (ChatMemberOwner, ChatMemberAdministrator)
USERS: ChatMemberCollection = (ChatMemberMember, ChatMemberRestricted)
MEMBERS: ChatMemberCollection = ADMINS + USERS
"""
Statuses of chat members, including restricted ones.

.. note::

    A restricted user keeps the :code:`restricted` status after leaving the chat,
    so :code:`isinstance(member, MEMBERS)` is also :code:`True` for a restricted user
    who is not in the chat (:code:`is_member=False`).
    Use :func:`is_chat_member` to check whether the user is actually in the chat.
"""
NOT_MEMBERS: ChatMemberCollection = (ChatMemberLeft, ChatMemberBanned)


def is_chat_member(member: ChatMember) -> bool:
    """
    Check whether the user is a member of the chat at the moment of the request.

    Unlike :code:`isinstance(member, MEMBERS)`, a restricted user counts only
    when :code:`member.is_member` is :code:`True`.

    :param member: chat member object
    :return: :code:`True` if the user is in the chat
    """
    if isinstance(member, ChatMemberRestricted):
        return member.is_member
    return isinstance(member, MEMBERS)
