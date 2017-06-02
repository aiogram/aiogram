import asyncio
import json
import logging

import aiohttp

from . import api
from . import types
from .utils.payload import generate_payload

log = logging.getLogger(__name__)


class Bot:
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
    async def me(self) -> types.User:
        if not hasattr(self, '_me'):
            setattr(self, '_me', await self.get_me())
        return getattr(self, '_me')

    async def request(self, method, data=None, files=None):
        return await api.request(self.session, self.__token, method, data, files)

    async def _send_file(self, file_type, file, payload):
        methods = {
            'photo': api.ApiMethods.SEND_PHOTO,
            'audio': api.ApiMethods.SEND_AUDIO,
            'document': api.ApiMethods.SEND_DOCUMENT,
            'sticker': api.ApiMethods.SEND_STICKER,
            'video': api.ApiMethods.SEND_VIDEO,
            'voice': api.ApiMethods.SEND_VOICE,
            'video_note': api.ApiMethods.SEND_VIDEO_NOTE
        }

        method = methods[file_type]
        if isinstance(file, str):
            payload[file_type] = file
            req = self.request(method, payload)
        else:
            data = {file_type: file}
            req = self.request(api.ApiMethods.SEND_PHOTO, payload, data)

        return self.prepare_object(types.Message.de_json(await req))

    async def get_me(self) -> types.User:
        raw = await self.request(api.ApiMethods.GET_ME)
        return self.prepare_object(types.User.de_json(raw))

    async def get_updates(self, offset=None, limit=None, timeout=None, allowed_updates=None) -> [types.Update]:
        payload = generate_payload(**locals())
        raw = await self.request(api.ApiMethods.GET_UPDATES, payload)
        return [self.prepare_object(types.Update.de_json(raw_update)) for raw_update in raw]

    async def set_webhook(self, url, certificate=None, max_connections=None, allowed_updates=None) -> types.WebhookInfo:
        payload = generate_payload(**locals(), exclude='certificate')
        if certificate:
            cert = {'certificate': certificate}
            req = self.request(api.ApiMethods.SET_WEBHOOK, payload, cert)
        else:
            req = self.request(api.ApiMethods.SET_WEBHOOK, payload)

        return self.prepare_object(types.WebhookInfo.de_json(await req))

    async def delete_webhook(self) -> bool:
        payload = {}
        await self.request(api.ApiMethods.DELETE_WEBHOOK, payload)
        return True

    async def get_webhook_info(self) -> types.WebhookInfo:
        payload = {}
        webhook_info = await self.request(api.ApiMethods.GET_WEBHOOK_INFO, payload)
        return self.prepare_object(webhook_info)

    async def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None,
                           disable_notification=None, reply_to_message_id=None, reply_markup=None) -> types.Message:
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals())
        message = await self.request(api.ApiMethods.SEND_MESSAGE, payload)
        return self.prepare_object(types.Message.de_json(message))

    async def forward_message(self, chat_id, from_chat_id, message_id, disable_notification=None) -> types.Message:
        payload = generate_payload(**locals())
        message = await self.request(api.ApiMethods.FORWARD_MESSAGE, payload)
        return self.prepare_object(types.Message.de_json(message))

    async def send_photo(self, chat_id, photo, caption=None, disable_notification=None, reply_to_message_id=None,
                         reply_markup=None) -> types.Message:
        _message_type = 'photo'
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=[_message_type])
        return await self._send_file(_message_type, photo, payload)

    async def send_audio(self, chat_id, audio, caption=None, duration=None, performer=None, title=None,
                         disable_notification=None, reply_to_message_id=None, reply_markup=None) -> types.Message:
        _message_type = 'audio'
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=[_message_type])
        return await self._send_file(_message_type, audio, payload)

    async def send_document(self, chat_id, document, caption=None, disable_notification=None, reply_to_message_id=None,
                            reply_markup=None) -> types.Message:
        _message_type = 'document'
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=[_message_type])
        return await self._send_file(_message_type, document, payload)

    async def send_sticker(self, chat_id, sticker, disable_notification=None, reply_to_message_id=None,
                           reply_markup=None) -> types.Message:
        _METHOD = 'sticker'
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=[_METHOD])
        return await self._send_file(_METHOD, sticker, payload)

    async def send_video(self, chat_id, video, duration=None, width=None, height=None, caption=None,
                         disable_notification=None, reply_to_message_id=None, reply_markup=None) -> types.Message:
        _message_type = 'video'
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=[_message_type])
        return await self._send_file(_message_type, video, payload)

    async def send_voice(self, chat_id, voice, caption=None, duration=None, disable_notification=None,
                         reply_to_message_id=None, reply_markup=None) -> types.Message:
        _message_type = 'voice'
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=[_message_type])
        return await self._send_file(_message_type, voice, payload)

    async def send_video_note(self, chat_id, video_note, duration=None, length=None, disable_notification=None,
                              reply_to_message_id=None, reply_markup=None) -> types.Message:
        _message_type = 'video_note'
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals(), exclude=[_message_type])
        return await self._send_file(_message_type, video_note, payload)

    async def send_location(self, chat_id, latitude, longitude, disable_notification=None, reply_to_message_id=None,
                            reply_markup=None) -> types.Message:
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals())
        message = await self.request(api.ApiMethods.SEND_LOCATION, payload)
        return self.prepare_object(types.Message.de_json(message))

    async def send_venue(self, chat_id, latitude, longitude, title, address, foursquare_id, disable_notification=None,
                         reply_to_message_id=None, reply_markup=None) -> types.Message:
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals())
        message = await self.request(api.ApiMethods.SEND_VENUE, payload)
        return self.prepare_object(types.Message.de_json(message))

    async def send_contact(self, chat_id, phone_number, first_name, last_name=None, disable_notification=None,
                           reply_to_message_id=None, reply_markup=None) -> types.Message:
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        payload = generate_payload(**locals())
        message = await self.request(api.ApiMethods.SEND_CONTACT, payload)
        return self.prepare_object(types.Message.de_json(message))

    async def send_chat_action(self, chat_id, action) -> bool:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.SEND_CHAT_ACTION, payload)

    async def get_user_profile_photos(self, user_id, offset=None, limit=None) -> types.UserProfilePhotos:
        payload = generate_payload(**locals())
        message = await self.request(api.ApiMethods.GET_USER_PROFILE_PHOTOS, payload)
        return self.prepare_object(types.UserProfilePhotos.de_json(message))

    async def get_file(self, file_id) -> types.File:
        payload = generate_payload(**locals())
        message = await self.request(api.ApiMethods.GET_FILE, payload)
        return self.prepare_object(types.File.de_json(message))

    async def kick_chat_user(self, chat_id, user_id) -> bool:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.KICK_CHAT_MEMBER, payload)

    async def unban_chat_member(self, chat_id, user_id) -> bool:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.UNBAN_CHAT_MEMBER, payload)

    async def leave_chat(self, chat_id) -> bool:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.LEAVE_CHAT, payload)

    async def get_chat(self, chat_id) -> types.Chat:
        payload = generate_payload(**locals())
        raw = await self.request(api.ApiMethods.GET_CHAT, payload)
        return self.prepare_object(types.Chat.de_json(raw))

    async def get_chat_administrators(self, chat_id) -> [types.ChatMember]:
        payload = generate_payload(**locals())
        raw = await self.request(api.ApiMethods.GET_CHAT_ADMINISTRATORS, payload)
        return [self.prepare_object(types.ChatMember.de_json(raw_chat_member)) for raw_chat_member in raw]

    async def get_chat_members_count(self, chat_id) -> int:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.GET_CHAT_MEMBERS_COUNT, payload)

    async def get_chat_member(self, chat_id, user_id) -> types.ChatMember:
        payload = generate_payload(**locals())
        raw = await self.request(api.ApiMethods.GET_CHAT_MEMBER, payload)
        return self.prepare_object(types.ChatMember.de_json(raw))

    async def answer_callback_query(self, callback_query_id, text=None, show_alert=None, url=None,
                                    cache_time=None) -> bool:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.LEAVE_CHAT, payload)

    async def answer_inline_query(self, inline_query_id, results, cache_time=None, is_personal=None, next_offset=None,
                                  switch_pm_text=None, switch_pm_parameter=None) -> bool:
        results = json.dumps([item.to_json() for item in results])

        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.ANSWER_INLINE_QUERY, payload)

    async def edit_message_text(self, text, chat_id=None, message_id=None, inline_message_id=None, parse_mode=None,
                                disable_web_page_preview=None, reply_markup=None) -> types.Message or bool:
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(message_id, 'message_id'):
            message_id = message_id.message_id

        if hasattr(inline_message_id, 'message_id'):
            inline_message_id = inline_message_id.message_id

        payload = generate_payload(**locals())
        raw = await self.request(api.ApiMethods.EDIT_MESSAGE_TEXT, payload)
        if raw is True:
            return raw
        return self.prepare_object(types.Message.de_json(raw))

    async def edit_message_caption(self, chat_id=None, message_id=None, inline_message_id=None, caption=None,
                                   reply_markup=None) -> types.Message or bool:
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(message_id, 'message_id'):
            message_id = message_id.message_id

        if hasattr(inline_message_id, 'message_id'):
            inline_message_id = inline_message_id.message_id

        payload = generate_payload(**locals())
        raw = await self.request(api.ApiMethods.EDIT_MESSAGE_TEXT, payload)
        if raw is True:
            return raw
        return self.prepare_object(types.Message.de_json(raw))

    async def edit_message_reply_markup(self, chat_id=None, message_id=None, inline_message_id=None,
                                        reply_markup=None) -> types.Message or bool:
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(message_id, 'message_id'):
            message_id = message_id.message_id

        if hasattr(inline_message_id, 'message_id'):
            inline_message_id = inline_message_id.message_id

        payload = generate_payload(**locals())
        raw = await self.request(api.ApiMethods.EDIT_MESSAGE_TEXT, payload)
        if raw is True:
            return raw
        return self.prepare_object(types.Message.de_json(raw))

    async def delete_message(self, chat_id, message_id) -> bool:
        payload = generate_payload(**locals())

        await self.request(api.ApiMethods.DELETE_MESSAGE, payload)
        return True

    async def send_invoice(self, chat_id: int, title: str, description: str, payload: str, provider_token: str,
                           start_parameter: str, currency: str, prices: [types.LabeledPrice], photo_url: str = None,
                           photo_size: int = None, photo_width: int = None, photo_height: int = None,
                           need_name: bool = None, need_phone_number: bool = None, need_email: bool = None,
                           need_shipping_address: bool = None, is_flexible: bool = None,
                           disable_notification: bool = None, reply_to_message_id: int = None,
                           reply_markup: types.InlineKeyboardMarkup = None) -> types.Message:
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())
        prices = json.dumps([item.to_json() for item in prices])

        payload_ = generate_payload(**locals())

        message = await self.request(api.ApiMethods.SEND_INVOICE, payload_)
        return self.prepare_object(types.Message.de_json(message))

    async def answer_shipping_query(self, shipping_query_id: str, ok: bool,
                                    shipping_options: [types.ShippingOption] = None, error_message: str = None) -> None:
        shipping_options = json.dumps([item.to_json() for item in shipping_options])

        payload = generate_payload(**locals())

        return await self.request(api.ApiMethods.ANSWER_SHIPPING_QUERY, payload)

    async def answer_pre_checkout_query(self, pre_checkout_query_id: str, ok: bool, error_message: str = None) -> bool:
        payload = generate_payload(**locals())

        return await self.request(api.ApiMethods.ANSWER_PRE_CHECKOUT_QUERY, payload)
