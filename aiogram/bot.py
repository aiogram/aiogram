import asyncio
import json

import aiohttp

from . import api
from .api import ApiMethods
from .types.chat import Chat
from .types.chat_member import ChatMember
from .types.file import File
from .types.message import Message
from .types.update import Update
from .types.user import User
from .types.user_profile_photos import UserProfilePhotos
from .types.webhook_info import WebhookInfo
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

    async def get_me(self) -> User:
        raw = await self.request(ApiMethods.GET_ME)
        return self.prepare_object(User.de_json(raw))

    async def get_updates(self, offset=None, limit=None, timeout=None, allowed_updates=None):
        payload = generate_payload(**locals())
        raw = await self.request(ApiMethods.GET_UPDATES, payload)
        return [self.prepare_object(Update.de_json(raw_update)) for raw_update in raw]

    async def set_webhook(self, url, certificate=None, max_connections=None, allowed_updates=None):
        payload = generate_payload(**locals(), exclude='certificate')
        if certificate:
            cert = {'certificate': certificate}
            req = self.request(ApiMethods.SET_WEBHOOK, payload, cert)
        else:
            req = self.request(ApiMethods.SET_WEBHOOK, payload)

        return self.prepare_object(WebhookInfo.de_json(await req))

    async def delete_webhook(self):
        payload = {}
        await self.request(ApiMethods.DELETE_WEBHOOK, payload)
        return True

    async def get_webhook_info(self):
        payload = {}
        webhook_info = await self.request(ApiMethods.GET_WEBHOOK_INFO, payload)
        return self.prepare_object(webhook_info)

    async def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None,
                           disable_notification=None, reply_to_message_id=None, reply_markup=None):
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals())
        message = await self.request(ApiMethods.SEND_MESSAGE, payload)
        return self.prepare_object(Message.de_json(message))

    async def forward_message(self, chat_id, from_chat_id, message_id, disable_notification=None):
        payload = generate_payload(**locals())
        message = await self.request(ApiMethods.FORWARD_MESSAGE, payload)
        return self.prepare_object(Message.de_json(message))

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

    async def send_video_note(self, chat_id, video_note, duration=None, length=None, disable_notification=None,
                              reply_to_message_id=None, reply_markup=None) -> Message:
        _message_type = 'video_note'
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=[_message_type])
        return await self._send_file(_message_type, video_note, payload)

    async def send_location(self, chat_id, latitude, longitude, disable_notification=None, reply_to_message_id=None,
                            reply_markup=None):
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals())
        message = await self.request(ApiMethods.SEND_LOCATION, payload)
        return self.prepare_object(Message.de_json(message))

    async def send_venue(self, chat_id, latitude, longitude, title, address, foursquare_id, disable_notification=None,
                         reply_to_message_id=None, reply_markup=None):
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals())
        message = await self.request(ApiMethods.SEND_VENUE, payload)
        return self.prepare_object(Message.de_json(message))

    async def send_contact(self, chat_id, phone_number, first_name, last_name=None, disable_notification=None,
                           reply_to_message_id=None, reply_markup=None):
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals())
        message = await self.request(ApiMethods.SEND_CONTACT, payload)
        return self.prepare_object(Message.de_json(message))

    async def send_chat_action(self, chat_id, action):
        payload = generate_payload(**locals())
        message = await self.request(ApiMethods.SEND_CHAT_ACTION, payload)
        return self.prepare_object(Message.de_json(message))

    async def get_user_profile_photos(self, user_id, offset=None, limit=None):
        payload = generate_payload(**locals())
        message = await self.request(ApiMethods.GET_USER_PROFILE_PHOTOS, payload)
        return self.prepare_object(UserProfilePhotos.de_json(message))

    async def get_file(self, file_id):
        payload = generate_payload(**locals())
        message = await self.request(ApiMethods.GET_FILE, payload)
        return self.prepare_object(File.de_json(message))

    async def kick_chat_user(self, chat_id, user_id):
        payload = generate_payload(**locals())
        return await self.request(ApiMethods.KICK_CHAT_MEMBER, payload)

    async def unban_chat_member(self, chat_id, user_id):
        payload = generate_payload(**locals())
        return await self.request(ApiMethods.UNBAN_CHAT_MEMBER, payload)

    async def leave_chat(self, chat_id):
        payload = generate_payload(**locals())
        return await self.request(ApiMethods.LEAVE_CHAT, payload)

    async def get_chat(self, chat_id) -> Chat:
        payload = generate_payload(**locals())
        raw = await self.request(ApiMethods.GET_CHAT, payload)
        return self.prepare_object(Chat.de_json(raw))

    async def get_chat_administrators(self, chat_id):
        payload = generate_payload(**locals())
        raw = await self.request(ApiMethods.GET_CHAT_ADMINISTRATORS, payload)
        return [self.prepare_object(ChatMember.de_json(raw_chat_member)) for raw_chat_member in raw]

    async def get_chat_members_count(self, chat_id):
        payload = generate_payload(**locals())
        return await self.request(ApiMethods.GET_CHAT_MEMBERS_COUNT, payload)

    async def get_chat_member(self, chat_id, user_id):
        payload = generate_payload(**locals())
        raw = await self.request(ApiMethods.GET_CHAT_MEMBER, payload)
        return self.prepare_object(ChatMember.de_json(raw))

    async def answer_callback_query(self, callback_query_id, text=None, show_alert=None, url=None, cache_time=None):
        payload = generate_payload(**locals())
        return await self.request(ApiMethods.LEAVE_CHAT, payload)

    async def edit_message_text(self, text, chat_id=None, message_id=None, inline_message_id=None, parse_mode=None,
                                disable_web_page_preview=None, reply_markup=None):
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(message_id, 'message_id'):
            message_id = message_id.message_id

        if hasattr(inline_message_id, 'message_id'):
            inline_message_id = inline_message_id.message_id

        payload = generate_payload(**locals())
        raw = await self.request(ApiMethods.EDIT_MESSAGE_TEXT, payload)
        if raw is True:
            return raw
        return self.prepare_object(Message.de_json(raw))

    async def edit_message_caption(self, chat_id=None, message_id=None, inline_message_id=None, caption=None,
                                   reply_markup=None):
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(message_id, 'message_id'):
            message_id = message_id.message_id

        if hasattr(inline_message_id, 'message_id'):
            inline_message_id = inline_message_id.message_id

        payload = generate_payload(**locals())
        raw = await self.request(ApiMethods.EDIT_MESSAGE_TEXT, payload)
        if raw is True:
            return raw
        return self.prepare_object(Message.de_json(raw))

    async def edit_message_reply_markup(self, chat_id=None, message_id=None, inline_message_id=None, reply_markup=None):
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(message_id, 'message_id'):
            message_id = message_id.message_id

        if hasattr(inline_message_id, 'message_id'):
            inline_message_id = inline_message_id.message_id

        payload = generate_payload(**locals())
        raw = await self.request(ApiMethods.EDIT_MESSAGE_TEXT, payload)
        if raw is True:
            return raw
        return self.prepare_object(Message.de_json(raw))

    async def delete_message(self, chat_id, message_id):
        payload = generate_payload(**locals())

        await self.request(ApiMethods.DELETE_MESSAGE, payload)
        return True
