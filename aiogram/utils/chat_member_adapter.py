from typing import Union

from pydantic import Field, TypeAdapter
from typing_extensions import Annotated

from aiogram import types

ChatMemberUnion = Union[
    types.ChatMemberOwner,
    types.ChatMemberAdministrator,
    types.ChatMemberMember,
    types.ChatMemberRestricted,
    types.ChatMemberLeft,
    types.ChatMemberBanned,
]

ChatMemberAdapter = TypeAdapter(
    Annotated[
        ChatMemberUnion,
        Field(discriminator="status"),
    ]
)
