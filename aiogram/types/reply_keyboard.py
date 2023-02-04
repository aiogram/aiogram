import typing

from . import base
from . import fields
from .chat_administrator_rights import ChatAdministratorRights
from .web_app_info import WebAppInfo


class KeyboardButtonPollType(base.TelegramObject):
    """
    This object represents type of a poll, which is allowed to be created and sent when the corresponding button is pressed.

    https://core.telegram.org/bots/api#keyboardbuttonpolltype
    """
    type: base.String = fields.Field()

    def __init__(self, type: typing.Optional[base.String] = None):
        super(KeyboardButtonPollType, self).__init__(type=type)


class ReplyKeyboardMarkup(base.TelegramObject):
    """
    This object represents a custom keyboard with reply options
    (see https://core.telegram.org/bots#keyboards to bots for details
    and examples).

    https://core.telegram.org/bots/api#replykeyboardmarkup
    """
    keyboard: 'typing.List[typing.List[KeyboardButton]]' = fields.ListOfLists(base='KeyboardButton', default=[])
    resize_keyboard: base.Boolean = fields.Field()
    one_time_keyboard: base.Boolean = fields.Field()
    input_field_placeholder: base.String = fields.Field()
    selective: base.Boolean = fields.Field()
    is_persistent: base.Boolean = fields.Field()

    def __init__(self, keyboard: 'typing.List[typing.List[KeyboardButton]]' = None,
                 resize_keyboard: base.Boolean = None,
                 one_time_keyboard: base.Boolean = None,
                 input_field_placeholder: base.String = None,
                 selective: base.Boolean = None,
                 row_width: base.Integer = 3,
                 is_persistent: base.Boolean = None,
                 conf=None):
        if conf is None:
            conf = {}
        super().__init__(
            keyboard=keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=one_time_keyboard,
            input_field_placeholder=input_field_placeholder,
            selective=selective,
            is_persistent=is_persistent,
            conf={'row_width': row_width, **conf},
        )

    @property
    def row_width(self):
        return self.conf.get('row_width', 3)

    @row_width.setter
    def row_width(self, value):
        self.conf['row_width'] = value

    def add(self, *args):
        """
        Add buttons

        :param args:
        :return: self
        :rtype: :obj:`types.ReplyKeyboardMarkup`
        """
        row = []
        for index, button in enumerate(args, start=1):
            row.append(button)
            if index % self.row_width == 0:
                self.keyboard.append(row)
                row = []
        if row:
            self.keyboard.append(row)
        return self

    def row(self, *args):
        """
        Add row

        :param args:
        :return: self
        :rtype: :obj:`types.ReplyKeyboardMarkup`
        """
        btn_array = [button for button in args]
        self.keyboard.append(btn_array)
        return self

    def insert(self, button):
        """
        Insert button to last row

        :param button:
        :return: self
        :rtype: :obj:`types.ReplyKeyboardMarkup`
        """
        if self.keyboard and len(self.keyboard[-1]) < self.row_width:
            self.keyboard[-1].append(button)
        else:
            self.add(button)
        return self



class KeyboardButtonRequestUser(base.TelegramObject):
    """
    This object defines the criteria used to request a suitable user.
    The identifier of the selected user will be shared with the bot when
    the corresponding button is pressed.

    https://core.telegram.org/bots/api#keyboardbuttonrequestuser
    """
    request_id: base.Integer = fields.Field()
    user_is_bot: base.Boolean = fields.Field()
    user_is_premium: base.Boolean = fields.Field()

    def __init__(
        self,
        request_id: base.Integer,
        user_is_bot: typing.Optional[base.Boolean] = None,
        user_is_premium: typing.Optional[base.Boolean] = None,
        **kwargs,
    ):
        super().__init__(
            request_id=request_id,
            user_is_bot=user_is_bot,
            user_is_premium=user_is_premium,
            **kwargs,
        )


class KeyboardButtonRequestChat(base.TelegramObject):
    """
    This object defines the criteria used to request a suitable chat.
    The identifier of the selected chat will be shared with the bot when
    the corresponding button is pressed.

    https://core.telegram.org/bots/api#keyboardbuttonrequestchat
    """
    request_id: base.Integer = fields.Field()
    chat_is_channel: base.Boolean = fields.Field()
    chat_is_forum: base.Boolean = fields.Field()
    chat_has_username: base.Boolean = fields.Field()
    chat_is_created: base.Boolean = fields.Field()
    user_administrator_rights: ChatAdministratorRights = fields.Field()
    bot_administrator_rights: ChatAdministratorRights = fields.Field()
    bot_is_member: base.Boolean = fields.Field()

    def __init__(
        self,
        request_id: base.Integer,
        chat_is_channel: base.Boolean,
        chat_is_forum: typing.Optional[base.Boolean] = None,
        chat_has_username: typing.Optional[base.Boolean] = None,
        chat_is_created: typing.Optional[base.Boolean] = None,
        user_administrator_rights: typing.Optional[ChatAdministratorRights] = None,
        bot_administrator_rights: typing.Optional[ChatAdministratorRights] = None,
        bot_is_member: typing.Optional[base.Boolean] = None,
        **kwargs,
    ):
        super().__init__(
            request_id=request_id,
            chat_is_channel=chat_is_channel,
            chat_is_forum=chat_is_forum,
            chat_has_username=chat_has_username,
            chat_is_created=chat_is_created,
            user_administrator_rights=user_administrator_rights,
            bot_administrator_rights=bot_administrator_rights,
            bot_is_member=bot_is_member,
            **kwargs,
        )


class KeyboardButton(base.TelegramObject):
    """
    This object represents one button of the reply keyboard.
    For simple text buttons String can be used instead of this object to specify text of the button.
    Optional fields request_contact, request_location, and request_poll are mutually exclusive.
    Note: request_contact and request_location options will only work in Telegram versions released after 9 April, 2016.
    Older clients will ignore them.
    Note: request_poll option will only work in Telegram versions released after 23 January, 2020.
    Older clients will receive unsupported message.

    https://core.telegram.org/bots/api#keyboardbutton
    """
    text: base.String = fields.Field()
    request_user: KeyboardButtonRequestUser = fields.Field()
    request_chat: KeyboardButtonRequestChat = fields.Field()
    request_contact: base.Boolean = fields.Field()
    request_location: base.Boolean = fields.Field()
    request_poll: KeyboardButtonPollType = fields.Field()
    web_app: WebAppInfo = fields.Field(base=WebAppInfo)

    def __init__(self, text: base.String,
                 request_user: typing.Optional[KeyboardButtonRequestUser] = None,
                 request_chat: typing.Optional[KeyboardButtonRequestChat] = None,
                 request_contact: base.Boolean = None,
                 request_location: base.Boolean = None,
                 request_poll: KeyboardButtonPollType = None,
                 web_app: WebAppInfo = None,
                 **kwargs):
        super(KeyboardButton, self).__init__(text=text,
                                             request_user=request_user,
                                             request_chat=request_chat,
                                             request_contact=request_contact,
                                             request_location=request_location,
                                             request_poll=request_poll,
                                             web_app=web_app,
                                             **kwargs)



class ReplyKeyboardRemove(base.TelegramObject):
    """
    Upon receiving a message with this object, Telegram clients will remove the current custom keyboard
    and display the default letter-keyboard. By default, custom keyboards are displayed until a new keyboard is sent by a bot.
    An exception is made for one-time keyboards that are hidden immediately after the user presses a button (see ReplyKeyboardMarkup).

    https://core.telegram.org/bots/api#replykeyboardremove
    """
    remove_keyboard: base.Boolean = fields.Field(default=True)
    selective: base.Boolean = fields.Field()

    def __init__(self, selective: base.Boolean = None):
        super(ReplyKeyboardRemove, self).__init__(remove_keyboard=True, selective=selective)
