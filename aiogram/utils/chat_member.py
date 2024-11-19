from typing import Tuple, Type, Union

from pydantic import Field, TypeAdapter
from typing_extensions import Annotated

from aiogram.types import (
    ChatMember,
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberLeft,
    ChatMemberMember,
    ChatMemberOwner,
    ChatMemberRestricted,
)

ChatMemberUnion = Union[
    ChatMemberOwner,
    ChatMemberAdministrator,
    ChatMemberMember,
    ChatMemberRestricted,
    ChatMemberLeft,
    ChatMemberBanned,
]

ChatMemberCollection = Tuple[Type[ChatMember], ...]

ChatMemberAdapter: TypeAdapter[ChatMemberUnion] = TypeAdapter(
    Annotated[
        ChatMemberUnion,
        Field(discriminator="status"),
    ]
)

ADMINS: ChatMemberCollection = (ChatMemberOwner, ChatMemberAdministrator)
USERS: ChatMemberCollection = (ChatMemberMember, ChatMemberRestricted)
MEMBERS: ChatMemberCollection = ADMINS + USERS
NOT_MEMBERS: ChatMemberCollection = (ChatMemberLeft, ChatMemberBanned)
