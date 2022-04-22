import typing

from . import base
from . import fields
from .web_app_info import WebAppInfo
from ..utils import helper
from ..utils.helper import Item


class MenuButton(base.TelegramObject):
    """
    This object describes the bot's menu button in a private chat. It should be one of

     - MenuButtonCommands
     - MenuButtonWebApp
     - MenuButtonDefault

    If a menu button other than MenuButtonDefault is set for a private chat,
    then it is applied in the chat.
    Otherwise the default menu button is applied.
    By default, the menu button opens the list of bot commands.
    """
    type: base.String = fields.Field(default='default')

    @classmethod
    def resolve(cls, **kwargs) -> typing.Union[
        "MenuButtonCommands",
        "MenuButtonDefault",
        "MenuButtonWebApp",
    ]:
        type_ = kwargs.get('type')
        mapping = {
            MenuButtonType.DEFAULT: MenuButtonDefault,
            MenuButtonType.COMMANDS: MenuButtonCommands,
            MenuButtonType.WEB_APP: MenuButtonWebApp,
        }
        class_ = mapping.get(type_)
        if not class_:
            raise ValueError(f'Unknown MenuButton type: {type_}')
        return class_(**kwargs)


class MenuButtonCommands(MenuButton):
    """
    Represents a menu button, which opens the bot's list of commands.

    Source: https://core.telegram.org/bots/api#menubuttoncommands
    """
    type: base.String = fields.Field(default='commands')

    def __init__(self, **kwargs):
        super().__init__(type='commands', **kwargs)


class MenuButtonWebApp(MenuButton):
    """
    Represents a menu button, which launches a Web App.

    Source: https://core.telegram.org/bots/api#menubuttonwebapp
    """
    type: base.String = fields.Field(default='web_app')
    text: base.String = fields.Field()
    web_app: WebAppInfo = fields.Field(base=WebAppInfo)

    def __init__(self, text: base.String, web_app: WebAppInfo, **kwargs):
        super().__init__(type='web_app', text=text, web_app=web_app, **kwargs)


class MenuButtonDefault(MenuButton):
    """
    Describes that no specific value for the menu button was set.

    Source: https://core.telegram.org/bots/api#menubuttondefault
    """
    type: base.String = fields.Field(default='default')

    def __init__(self, **kwargs):
        super().__init__(type='default', **kwargs)


class MenuButtonType(helper.Helper):
    mode = helper.HelperMode.lowercase

    DEFAULT = Item()
    COMMANDS = Item()
    WEB_APP = Item()
