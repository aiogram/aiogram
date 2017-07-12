import asyncio
import io

import aiohttp

from . import api
from ..utils import json
from ..utils.payload import generate_payload


class BaseBot:
    """
    Base class for bot. It's raw bot.
    """

    def __init__(self, token, loop=None, connections_limit=10):
        """
        :param token: token from @BotFather
        :param loop: event loop
        :param connections_limit: connections limit for aiohttp.ClientSession 
        """

        self.__token = token

        if loop is None:
            loop = asyncio.get_event_loop()

        self.loop = loop
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=connections_limit),
            loop=self.loop)
        self._temp_sessions = []
        api.check_token(token)

    def __del__(self):
        for session in self._temp_sessions:
            if not session.closed:
                session.close()
        if self.session and not self.session.closed:
            self.session.close()

    def create_temp_session(self) -> aiohttp.ClientSession:
        """
        Create temp session
        
        :return: 
        """
        session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=1, force_close=True),
            loop=self.loop)
        self._temp_sessions.append(session)
        return session

    def destroy_temp_session(self, session):
        """
        Destroy temp session
        
        :param session: 
        :return: 
        """
        if not session.closed:
            session.close()
        if session in self._temp_sessions:
            self._temp_sessions.remove(session)

    async def request(self, method, data=None, files=None) -> list or dict:
        """
        Make an request to Telegram Bot API

        :param method: API method
        :param data: request parameters
        :param files: files
        :return: list or dict
        :raise: :class:`aiogram.exceptions.TelegramApiError`
        """
        return await api.request(self.session, self.__token, method, data, files)

    async def download_file(self, file_path, destination=None, timeout=30, chunk_size=65536, seek=True):
        """
        Download file by file_path to destination

        if You want to automatically create destination (:class:`io.BytesIO`) use default 
        value of destination and handle result of this method.

        :param file_path: str
        :param destination: filename or instance of :class:`io.IOBase`. For e. g. :class:`io.BytesIO` 
        :param timeout: int
        :param chunk_size: int
        :param seek: bool - go to start of file when downloading is finished.
        :return: destination
        """
        if destination is None:
            destination = io.BytesIO()

        session = self.create_temp_session()
        url = api.Methods.file_url(token=self.__token, path=file_path)

        dest = destination if isinstance(destination, io.IOBase) else open(destination, 'wb')
        try:
            async with session.get(url, timeout=timeout) as response:
                while True:
                    chunk = await response.content.read(chunk_size)
                    if not chunk:
                        break
                    dest.write(chunk)
                    dest.flush()
            if seek:
                dest.seek(0)
            return dest
        finally:
            self.destroy_temp_session(session)

    async def _send_file(self, file_type, file, payload):
        methods = {
            'photo': api.Methods.SEND_PHOTO,
            'audio': api.Methods.SEND_AUDIO,
            'document': api.Methods.SEND_DOCUMENT,
            'sticker': api.Methods.SEND_STICKER,
            'video': api.Methods.SEND_VIDEO,
            'voice': api.Methods.SEND_VOICE,
            'video_note': api.Methods.SEND_VIDEO_NOTE,
        }

        method = methods[file_type]
        if isinstance(file, str):
            payload[file_type] = file
            req = self.request(method, payload)
        elif isinstance(file, io.IOBase):
            data = {file_type: file.read()}
            req = self.request(method, payload, data)
        else:
            data = {file_type: file}
            req = self.request(method, payload, data)

        return await req

    async def get_me(self) -> dict:
        return await self.request(api.Methods.GET_ME)

    async def get_updates(self, offset=None, limit=None, timeout=None, allowed_updates=None) -> [dict, ...]:
        payload = generate_payload(**locals())
        return await self.request(api.Methods.GET_UPDATES, payload)

    async def set_webhook(self, url, certificate=None, max_connections=None, allowed_updates=None) -> bool:
        payload = generate_payload(**locals(), exclude=['certificate'])
        if certificate:
            cert = {'certificate': certificate}
            req = self.request(api.Methods.SET_WEBHOOK, payload, cert)
        else:
            req = self.request(api.Methods.SET_WEBHOOK, payload)

        return await req

    async def delete_webhook(self) -> bool:
        payload = {}
        return await self.request(api.Methods.DELETE_WEBHOOK, payload)

    async def get_webhook_info(self) -> dict:
        payload = {}
        return await self.request(api.Methods.GET_WEBHOOK_INFO, payload)

    async def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None,
                           disable_notification=None, reply_to_message_id=None, reply_markup=None) -> dict:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        return await self.request(api.Methods.SEND_MESSAGE, payload)

    async def forward_message(self, chat_id, from_chat_id, message_id, disable_notification=None) -> dict:
        payload = generate_payload(**locals())
        return await self.request(api.Methods.FORWARD_MESSAGE, payload)

    async def send_photo(self, chat_id, photo, caption=None, disable_notification=None, reply_to_message_id=None,
                         reply_markup=None) -> dict:
        _message_type = 'photo'
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        return await self._send_file(_message_type, photo, payload)

    async def send_audio(self, chat_id, audio, caption=None, duration=None, performer=None, title=None,
                         disable_notification=None, reply_to_message_id=None, reply_markup=None) -> dict:
        _message_type = 'audio'
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        return await self._send_file(_message_type, audio, payload)

    async def send_document(self, chat_id, document, caption=None, disable_notification=None, reply_to_message_id=None,
                            reply_markup=None) -> dict:
        _message_type = 'document'
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        return await self._send_file(_message_type, document, payload)

    async def send_sticker(self, chat_id, sticker, disable_notification=None, reply_to_message_id=None,
                           reply_markup=None) -> dict:
        _message_type = 'sticker'
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        return await self._send_file(_message_type, sticker, payload)

    async def send_video(self, chat_id, video, duration=None, width=None, height=None, caption=None,
                         disable_notification=None, reply_to_message_id=None, reply_markup=None) -> dict:
        _message_type = 'video'
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        return await self._send_file(_message_type, video, payload)

    async def send_voice(self, chat_id, voice, caption=None, duration=None, disable_notification=None,
                         reply_to_message_id=None, reply_markup=None) -> dict:
        _message_type = 'voice'
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        return await self._send_file(_message_type, voice, payload)

    async def send_video_note(self, chat_id, video_note, duration=None, length=None, disable_notification=None,
                              reply_to_message_id=None, reply_markup=None) -> dict:
        _message_type = 'video_note'
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        return await self._send_file(_message_type, video_note, payload)

    async def send_location(self, chat_id, latitude, longitude, disable_notification=None, reply_to_message_id=None,
                            reply_markup=None) -> dict:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        return await self.request(api.Methods.SEND_LOCATION, payload)

    async def send_venue(self, chat_id, latitude, longitude, title, address, foursquare_id, disable_notification=None,
                         reply_to_message_id=None, reply_markup=None) -> dict:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        return await self.request(api.Methods.SEND_VENUE, payload)

    async def send_contact(self, chat_id, phone_number, first_name, last_name=None, disable_notification=None,
                           reply_to_message_id=None, reply_markup=None) -> dict:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        return await self.request(api.Methods.SEND_CONTACT, payload)

    async def send_chat_action(self, chat_id, action) -> bool:
        payload = generate_payload(**locals())
        return await self.request(api.Methods.SEND_CHAT_ACTION, payload)

    async def get_user_profile_photos(self, user_id, offset=None, limit=None) -> dict:
        payload = generate_payload(**locals())
        return await self.request(api.Methods.GET_USER_PROFILE_PHOTOS, payload)

    async def get_file(self, file_id) -> dict:
        payload = generate_payload(**locals())
        return await self.request(api.Methods.GET_FILE, payload)

    async def kick_chat_member(self, chat_id, user_id) -> bool:
        payload = generate_payload(**locals())
        return await self.request(api.Methods.KICK_CHAT_MEMBER, payload)

    async def promote_chat_member(self, chat_id: int, user_id: int, can_change_info: bool, can_post_messages: bool,
                                  can_edit_messages: bool, can_delete_messages: bool, can_invite_users: bool,
                                  can_restrict_members: bool, can_pin_messages: bool,
                                  can_promote_members: bool) -> bool:
        payload = generate_payload(**locals())

        return await self.request(api.Methods.PROMOTE_CHAT_MEMBER, payload)

    async def restrict_chat_member(self, chat_id: int, user_id: int, until_date: int, can_send_messages: bool,
                                   can_send_media_messages: bool, can_send_other_messages: bool,
                                   can_add_web_page_previews: bool) -> bool:
        payload = generate_payload(**locals())

        return await self.request(api.Methods.RESTRICT_CHAT_MEMBER, payload)

    async def export_chat_invite_link(self, chat_id: int) -> str:
        payload = generate_payload(**locals())

        return await self.request(api.Methods.EXPORT_CHAT_INVITE_LINK, payload)

    async def set_chat_photo(self, chat_id: int, photo) -> bool:
        payload = generate_payload(**locals(), exclude=['photo'])

        if isinstance(photo, str):
            payload['photo'] = photo
            req = self.request(api.Methods.SET_CHAT_PHOTO, payload)
        elif isinstance(photo, io.IOBase):
            data = {'photo': photo.read()}
            req = self.request(api.Methods.SET_CHAT_PHOTO, payload, data)
        else:
            data = {'photo': photo}
            req = self.request(api.Methods.SET_CHAT_PHOTO, payload, data)

        return await req

    async def delete_chat_photo(self, chat_id: int) -> bool:
        payload = generate_payload(**locals())

        return await self.request(api.Methods.DELETE_CHAT_PHOTO, payload)

    async def set_chat_title(self, chat_id: int, title: str) -> bool:
        payload = generate_payload(**locals())

        return await self.request(api.Methods.SET_CHAT_TITLE, payload)

    async def set_chat_description(self, chat_id: int, description: str) -> bool:
        payload = generate_payload(**locals())

        return await self.request(api.Methods.SET_CHAT_DESCRIPTION, payload)

    async def pin_chat_message(self, chat_id: int, message_id: int, disable_notification: bool) -> bool:
        payload = generate_payload(**locals())

        return await self.request(api.Methods.PIN_CHAT_MESSAGE, payload)

    async def unpin_chat_message(self, chat_id: int) -> bool:
        payload = generate_payload(**locals())

        return await self.request(api.Methods.UNPIN_CHAT_MESSAGE, payload)

    async def unban_chat_member(self, chat_id, user_id) -> bool:
        payload = generate_payload(**locals())
        return await self.request(api.Methods.UNBAN_CHAT_MEMBER, payload)

    async def leave_chat(self, chat_id) -> bool:
        payload = generate_payload(**locals())
        return await self.request(api.Methods.LEAVE_CHAT, payload)

    async def get_chat(self, chat_id) -> dict:
        payload = generate_payload(**locals())
        return await self.request(api.Methods.GET_CHAT, payload)

    async def get_chat_administrators(self, chat_id) -> [dict]:
        payload = generate_payload(**locals())
        return await self.request(api.Methods.GET_CHAT_ADMINISTRATORS, payload)

    async def get_chat_members_count(self, chat_id) -> int:
        payload = generate_payload(**locals())
        return await self.request(api.Methods.GET_CHAT_MEMBERS_COUNT, payload)

    async def get_chat_member(self, chat_id, user_id) -> dict:
        payload = generate_payload(**locals())
        return await self.request(api.Methods.GET_CHAT_MEMBER, payload)

    async def answer_callback_query(self, callback_query_id, text=None, show_alert=None, url=None,
                                    cache_time=None) -> bool:
        payload = generate_payload(**locals())
        return await self.request(api.Methods.ANSWER_CALLBACK_QUERY, payload)

    async def answer_inline_query(self, inline_query_id, results, cache_time=None, is_personal=None, next_offset=None,
                                  switch_pm_text=None, switch_pm_parameter=None) -> bool:
        if isinstance(results, list):
            results = json.dumps([item for item in results])

        payload = generate_payload(**locals())
        return await self.request(api.Methods.ANSWER_INLINE_QUERY, payload)

    async def edit_message_text(self, text, chat_id=None, message_id=None, inline_message_id=None, parse_mode=None,
                                disable_web_page_preview=None, reply_markup=None) -> dict or bool:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        raw = await self.request(api.Methods.EDIT_MESSAGE_TEXT, payload)
        if raw is True:
            return raw
        return raw

    async def edit_message_caption(self, chat_id=None, message_id=None, inline_message_id=None, caption=None,
                                   reply_markup=None) -> dict or bool:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        raw = await self.request(api.Methods.EDIT_MESSAGE_CAPTION, payload)
        if raw is True:
            return raw
        return raw

    async def edit_message_reply_markup(self, chat_id=None, message_id=None, inline_message_id=None,
                                        reply_markup=None) -> dict or bool:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        raw = await self.request(api.Methods.EDIT_MESSAGE_REPLY_MARKUP, payload)
        if raw is True:
            return raw
        return raw

    async def delete_message(self, chat_id, message_id) -> bool:
        payload = generate_payload(**locals())
        return await self.request(api.Methods.DELETE_MESSAGE, payload)

    async def send_invoice(self, chat_id: int, title: str, description: str, payload: str, provider_token: str,
                           start_parameter: str, currency: str, prices: list, photo_url: str = None,
                           photo_size: int = None, photo_width: int = None, photo_height: int = None,
                           need_name: bool = None, need_phone_number: bool = None, need_email: bool = None,
                           need_shipping_address: bool = None, is_flexible: bool = None,
                           disable_notification: bool = None, reply_to_message_id: int = None,
                           reply_markup: dict or str = None) -> dict:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        if isinstance(prices, list):
            prices = json.dumps(prices)

        payload_ = generate_payload(**locals())

        return await self.request(api.Methods.SEND_INVOICE, payload_)

    async def answer_shipping_query(self, shipping_query_id: str, ok: bool,
                                    shipping_options=None, error_message: str = None) -> bool:
        if shipping_options and isinstance(shipping_options, list):
            shipping_options = json.dumps(shipping_options)

        payload = generate_payload(**locals())

        return await self.request(api.Methods.ANSWER_SHIPPING_QUERY, payload)

    async def answer_pre_checkout_query(self, pre_checkout_query_id: str, ok: bool, error_message: str = None) -> bool:
        payload = generate_payload(**locals())

        return await self.request(api.Methods.ANSWER_PRE_CHECKOUT_QUERY, payload)

    async def send_game(self, chat_id: int, game_short_name: str, disable_notification: bool = None,
                        reply_to_message_id: int = None,
                        reply_markup: dict or str = None) -> dict:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())

        return await self.request(api.Methods.SEND_GAME, payload)

    async def set_game_score(self, user_id: int, score: int, force: bool = None, disable_edit_message: bool = None,
                             chat_id: int = None, message_id: int = None,
                             inline_message_id: str = None) -> dict or bool:
        payload = generate_payload(**locals())

        raw = self.request(api.Methods.SET_GAME_SCORE, payload)
        if raw is True:
            return raw
        return raw

    async def get_game_high_scores(self, user_id: int, chat_id: int = None, message_id: int = None,
                                   inline_message_id: str = None) -> dict:
        payload = generate_payload(**locals())

        return await self.request(api.Methods.GET_GAME_HIGH_SCORES, payload)
