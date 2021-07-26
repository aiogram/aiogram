import typing

from . import base, fields
from ..utils import helper


class BotCommandScopeType(helper.Helper):
    mode = helper.HelperMode.snake_case

    DEFAULT = helper.Item()  # default
    ALL_PRIVATE_CHATS = helper.Item()  # all_private_chats
    ALL_GROUP_CHATS = helper.Item()  # all_group_chats
    ALL_CHAT_ADMINISTRATORS = helper.Item()  # all_chat_administrators
    CHAT = helper.Item()  # chat
    CHAT_ADMINISTRATORS = helper.Item()  # chat_administrators
    CHAT_MEMBER = helper.Item()  # chat_member


class BotCommandScope(base.TelegramObject):
    """
    This object represents the scope to which bot commands are applied.
    Currently, the following 7 scopes are supported:
        BotCommandScopeDefault
        BotCommandScopeAllPrivateChats
        BotCommandScopeAllGroupChats
        BotCommandScopeAllChatAdministrators
        BotCommandScopeChat
        BotCommandScopeChatAdministrators
        BotCommandScopeChatMember

    https://core.telegram.org/bots/api#botcommandscope
    """
    type: base.String = fields.Field()

    @classmethod
    def from_type(cls, type: str, **kwargs: typing.Any):
        if type == BotCommandScopeType.DEFAULT:
            return BotCommandScopeDefault(type=type, **kwargs)
        if type == BotCommandScopeType.ALL_PRIVATE_CHATS:
            return BotCommandScopeAllPrivateChats(type=type, **kwargs)
        if type == BotCommandScopeType.ALL_GROUP_CHATS:
            return BotCommandScopeAllGroupChats(type=type, **kwargs)
        if type == BotCommandScopeType.ALL_CHAT_ADMINISTRATORS:
            return BotCommandScopeAllChatAdministrators(type=type, **kwargs)
        if type == BotCommandScopeType.CHAT:
            return BotCommandScopeChat(type=type, **kwargs)
        if type == BotCommandScopeType.CHAT_ADMINISTRATORS:
            return BotCommandScopeChatAdministrators(type=type, **kwargs)
        if type == BotCommandScopeType.CHAT_MEMBER:
            return BotCommandScopeChatMember(type=type, **kwargs)
        raise ValueError(f"Unknown BotCommandScope type {type!r}")


class BotCommandScopeDefault(BotCommandScope):
    """
    Represents the default scope of bot commands.
    Default commands are used if no commands with a narrower scope are
    specified for the user.
    """
    type = fields.Field(default=BotCommandScopeType.DEFAULT)


class BotCommandScopeAllPrivateChats(BotCommandScope):
    """
    Represents the scope of bot commands, covering all private chats.
    """
    type = fields.Field(default=BotCommandScopeType.ALL_PRIVATE_CHATS)


class BotCommandScopeAllGroupChats(BotCommandScope):
    """
    Represents the scope of bot commands, covering all group and
    supergroup chats.
    """
    type = fields.Field(default=BotCommandScopeType.ALL_GROUP_CHATS)


class BotCommandScopeAllChatAdministrators(BotCommandScope):
    """
    Represents the scope of bot commands, covering all group and
    supergroup chat administrators.
    """
    type = fields.Field(default=BotCommandScopeType.ALL_CHAT_ADMINISTRATORS)


class BotCommandScopeChat(BotCommandScope):
    """
    Represents the scope of bot commands, covering a specific chat.
    """
    type = fields.Field(default=BotCommandScopeType.CHAT)
    chat_id: typing.Union[base.String, base.Integer] = fields.Field()

    def __init__(self, chat_id: typing.Union[base.String, base.Integer], **kwargs):
        super().__init__(chat_id=chat_id, **kwargs)


class BotCommandScopeChatAdministrators(BotCommandScopeChat):
    """
    Represents the scope of bot commands, covering all administrators
    of a specific group or supergroup chat.
    """
    type = fields.Field(default=BotCommandScopeType.CHAT_ADMINISTRATORS)
    chat_id: typing.Union[base.String, base.Integer] = fields.Field()


class BotCommandScopeChatMember(BotCommandScopeChat):
    """
    Represents the scope of bot commands, covering a specific member of
    a group or supergroup chat.
    """
    type = fields.Field(default=BotCommandScopeType.CHAT_MEMBER)
    chat_id: typing.Union[base.String, base.Integer] = fields.Field()
    user_id: base.Integer = fields.Field()

    def __init__(
            self,
            chat_id: typing.Union[base.String, base.Integer],
            user_id: base.Integer,
            **kwargs,
    ):
        super().__init__(chat_id=chat_id, user_id=user_id, **kwargs)
