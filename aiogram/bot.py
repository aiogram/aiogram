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
        self.__token = token

        if loop is None:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=connections_limit),
            loop=self.loop)

        api.check_token(token)

    def __del__(self):
        if self.session and not self.session.closed:
            self.session.close()

    def prepare_object(self, obj, parent=None):
        obj.bot = self
        obj.parent = parent
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

    async def _send_file(self, file_type, file, payload):
        methods = {
            'photo': ApiMethods.SEND_PHOTO,
            'audio': ApiMethods.SEND_AUDIO,
            'document': ApiMethods.SEND_DOCUMENT,
            'sticker': ApiMethods.SEND_STICKER,
            'video': ApiMethods.SEND_VIDEO,
            'voice': ApiMethods.SEND_VOICE,
            'video_note': ApiMethods.SEND_VIDEO_NOTE
        }

        method = methods[file_type]
        if isinstance(file, str):
            payload[method] = file
            req = self.request(method, payload)
        else:
            data = {file_type: file}
            req = self.request(ApiMethods.SEND_PHOTO, payload, data)

        return self.prepare_object(Message.de_json(await req))

    async def send_photo(self, chat_id, photo, caption=None, disable_notification=None, reply_to_message_id=None,
                         reply_markup=None) -> Message:
        _message_type = 'photo'
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=[_message_type])
        return await self._send_file(_message_type, photo, payload)

    async def send_audio(self, chat_id, audio, caption=None, duration=None, performer=None, title=None,
                         disable_notification=None, reply_to_message_id=None, reply_markup=None) -> Message:
        _message_type = 'audio'
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=[_message_type])
        return await self._send_file(_message_type, audio, payload)

    async def send_document(self, chat_id, document, caption=None, disable_notification=None, reply_to_message_id=None,
                            reply_markup=None):
        _message_type = 'document'
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=[_message_type])
        return await self._send_file(_message_type, document, payload)

    async def send_sticker(self, chat_id, sticker, disable_notification=None, reply_to_message_id=None,
                           reply_markup=None) -> Message:
        _METHOD = 'sticker'
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=[_METHOD])
        return await self._send_file(_METHOD, sticker, payload)

    async def send_video(self, chat_id, video, duration=None, width=None, height=None, caption=None,
                         disable_notification=None, reply_to_message_id=None, reply_markup=None) -> Message:
        _message_type = 'video'
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=[_message_type])
        return await self._send_file(_message_type, video, payload)

    async def send_voice(self, chat_id, voice, caption=None, duration=None, disable_notification=None,
                         reply_to_message_id=None, reply_markup=None) -> Message:
        _message_type = 'voice'
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=[_message_type])
        return await self._send_file(_message_type, voice, payload)
