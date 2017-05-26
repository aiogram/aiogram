import asyncio
import json

import aiohttp

from . import api
from .api import ApiMethods
from .types.chat import Chat
from .types.message import Message
from .types.update import Update
from .types.user import User
from .utils.payload import generate_payload


class AIOGramBot:
    def __init__(self, token, loop=None, connections_limit=10):
        """
        :param token: 
        :param loop: 
        :param connections_limit: 
        """
        api.check_token(token)
        self.__token = token

        if loop is None:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=connections_limit),
            loop=self.loop)

    def __del__(self):
        self.session.close()

    def prepare_object(self, obj):
        obj.bot = self
        return obj

    @property
    async def me(self) -> User:
        if not hasattr(self, '_me'):
            setattr(self, '_me', await self.get_me())
        return getattr(self, '_me')

    async def request(self, method, data=None, files=None):
        return await api.request(self.session, self.__token, method, data, files)

    async def get_me(self) -> User:
        raw = await self.request(ApiMethods.GET_ME)
        return self.prepare_object(User.de_json(raw))

    async def get_chat(self, chat_id) -> Chat:
        payload = generate_payload(**locals())
        raw = await self.request(ApiMethods.GET_CHAT, payload)
        return self.prepare_object(Chat.de_json(raw))

    async def get_updates(self, offset=None, limit=None, timeout=None, allowed_updates=None):
        """
        offset	Integer	Optional	Identifier of the first update to be returned. Must be greater by one than the highest among the identifiers of previously received updates. By default, updates starting with the earliest unconfirmed update are returned. An update is considered confirmed as soon as getUpdates is called with an offset higher than its update_id. The negative offset can be specified to retrieve updates starting from -offset update from the end of the updates queue. All previous updates will forgotten.
        limit	Integer	Optional	Limits the number of updates to be retrieved. Values between 1—100 are accepted. Defaults to 100.
        timeout	Integer	Optional	Timeout in seconds for long polling. Defaults to 0, i.e. usual short polling. Should be positive, short polling should be used for testing purposes only.
        allowed_updates	Array of String	Optional	List the types of updates you want your bot to receive. For example, specify [“message”, “edited_channel_post”, “callback_query”] to only receive updates of these types. See Update for a complete list of available update types. Specify an empty list to receive all updates regardless of type (default). If not specified, the previous setting will be used.
        
        Please note that this parameter doesn't affect updates created before the call to the getUpdates, so unwanted updates may be received for a short period of time.
        :return: 
        """
        payload = generate_payload(**locals())
        raw = await self.request(ApiMethods.GET_UPDATES, payload)
        return [self.prepare_object(Update.de_json(raw_update)) for raw_update in raw]

    async def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None,
                           disable_notification=None, reply_to_message_id=None, reply_markup=None):
        """
        chat_id	Integer or String	Yes	Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        text	String	Yes	Text of the message to be sent
        parse_mode	String	Optional	Send Markdown or HTML, if you want Telegram apps to show bold, italic, fixed-width text or inline URLs in your bot's message.
        disable_web_page_preview	Boolean	Optional	Disables link previews for links in this message
        disable_notification	Boolean	Optional	Sends the message silently. iOS users will not receive a notification, Android users will receive a notification with no sound.
        reply_to_message_id	Integer	Optional	If the message is a reply, ID of the original message
        reply_markup	InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply	Optional	Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: 
        """

        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals())
        message = await self.request(ApiMethods.SEND_MESSAGE, payload)
        return self.prepare_object(Message.de_json(message))

    async def delete_message(self, chat_id, message_id):
        payload = generate_payload(**locals())

        await self.request(ApiMethods.DELETE_MESSAGE, payload)
        return True

    async def forward_message(self, chat_id, from_chat_id, message_id, disable_notification=None):
        """
        chat_id	Integer or String	Yes	Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        from_chat_id	Integer or String	Yes	Unique identifier for the chat where the original message was sent (or channel username in the format @channelusername)
        disable_notification	Boolean	Optional	Sends the message silently. iOS users will not receive a notification, Android users will receive a notification with no sound.
        message_id	Integer	Yes	Message identifier in the chat specified in from_chat_id
        :return: 
        """

        payload = generate_payload(**locals())
        message = await self.request(ApiMethods.FORWARD_MESSAGE, payload)
        return self.prepare_object(Message.de_json(message))

    async def send_photo(self, chat_id, photo, caption=None, disable_notification=None, reply_to_message_id=None,
                         reply_markup=None) -> Message:
        """
        chat_id	Integer or String	Yes	Unique identifier for the target chat or username of the target channel (in the format @channelusername)
        photo	InputFile or String	Yes	Photo to send. Pass a file_id as String to send a photo that exists on the Telegram servers (recommended), pass an HTTP URL as a String for Telegram to get a photo from the Internet, or upload a new photo using multipart/form-data. More info on Sending Files »
        caption	String	Optional	Photo caption (may also be used when resending photos by file_id), 0-200 characters
        disable_notification	Boolean	Optional	Sends the message silently. iOS users will not receive a notification, Android users will receive a notification with no sound.
        reply_to_message_id	Integer	Optional	If the message is a reply, ID of the original message
        reply_markup	InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply	Optional	Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.

        :return: 
        """

        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=['photo'])

        if isinstance(photo, str):
            payload['photo'] = photo
            file = None
        else:
            file = photo

        message = await self.request(ApiMethods.SEND_PHOTO, payload, {'photo': file})

        return self.prepare_object(Message.de_json(message))
