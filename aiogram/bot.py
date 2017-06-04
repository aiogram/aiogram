import asyncio
import io
import json
import logging

import aiohttp

from . import api
from . import types
from .utils.payload import generate_payload

log = logging.getLogger(__name__)


class RawBot:
    """
    Base bot object
    """

    def __init__(self, token, loop=None, connections_limit=10):
        """
        Bot instance
        
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

    async def download_file(self, file_id, destination=None, timeout=30, chunk_size=65536, seek=True):
        """
        Download file by file_id to destination

        if You want to automatically create destination (:class:`io.BytesIO`) use default 
        value of destination and handle result of this method.
        
        :param file_id: str
        :param destination: filename or instance of :class:`io.IOBase`. For e. g. :class:`io.BytesIO` 
        :param timeout: int
        :param chunk_size: int
        :param seek: bool - go to start of file when downloading is finished.
        :return: destination
        """
        if destination is None:
            destination = io.BytesIO()

        file = await self.get_file(file_id)

        session = self.create_temp_session()
        url = api.FILE_URL.format(token=self.__token, path=file.get('file_path'))

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
        elif isinstance(file, io.IOBase):
            data = {file_type: file.read()}
            req = self.request(api.ApiMethods.SEND_PHOTO, payload, data)
        elif isinstance(file, bytes):
            data = {file_type: file}
            req = self.request(api.ApiMethods.SEND_PHOTO, payload, data)
        else:
            data = {file_type: file}
            req = self.request(api.ApiMethods.SEND_PHOTO, payload, data)

        return await req

    async def get_me(self) -> types.User:
        return await self.request(api.ApiMethods.GET_ME)

    async def get_updates(self, offset=None, limit=None, timeout=None, allowed_updates=None) -> [dict, ...]:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.GET_UPDATES, payload)

    async def set_webhook(self, url, certificate=None, max_connections=None, allowed_updates=None) -> dict:
        payload = generate_payload(**locals(), exclude='certificate')
        if certificate:
            cert = {'certificate': certificate}
            req = self.request(api.ApiMethods.SET_WEBHOOK, payload, cert)
        else:
            req = self.request(api.ApiMethods.SET_WEBHOOK, payload)

        return await req

    async def delete_webhook(self) -> bool:
        payload = {}
        return await self.request(api.ApiMethods.DELETE_WEBHOOK, payload)

    async def get_webhook_info(self) -> types.WebhookInfo:
        payload = {}
        return await self.request(api.ApiMethods.GET_WEBHOOK_INFO, payload)

    async def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None,
                           disable_notification=None, reply_to_message_id=None, reply_markup=None) -> dict:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.SEND_MESSAGE, payload)

    async def forward_message(self, chat_id, from_chat_id, message_id, disable_notification=None) -> dict:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.FORWARD_MESSAGE, payload)

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
        return await self.request(api.ApiMethods.SEND_LOCATION, payload)

    async def send_venue(self, chat_id, latitude, longitude, title, address, foursquare_id, disable_notification=None,
                         reply_to_message_id=None, reply_markup=None) -> dict:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.SEND_VENUE, payload)

    async def send_contact(self, chat_id, phone_number, first_name, last_name=None, disable_notification=None,
                           reply_to_message_id=None, reply_markup=None) -> types.Message:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.SEND_CONTACT, payload)

    async def send_chat_action(self, chat_id, action) -> bool:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.SEND_CHAT_ACTION, payload)

    async def get_user_profile_photos(self, user_id, offset=None, limit=None) -> dict:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.GET_USER_PROFILE_PHOTOS, payload)

    async def get_file(self, file_id) -> dict:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.GET_FILE, payload)

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
        return await self.request(api.ApiMethods.GET_CHAT, payload)

    async def get_chat_administrators(self, chat_id) -> [types.ChatMember]:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.GET_CHAT_ADMINISTRATORS, payload)

    async def get_chat_members_count(self, chat_id) -> int:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.GET_CHAT_MEMBERS_COUNT, payload)

    async def get_chat_member(self, chat_id, user_id) -> types.ChatMember:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.GET_CHAT_MEMBER, payload)

    async def answer_callback_query(self, callback_query_id, text=None, show_alert=None, url=None,
                                    cache_time=None) -> bool:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.ANSWER_CALLBACK_QUERY, payload)

    async def answer_inline_query(self, inline_query_id, results, cache_time=None, is_personal=None, next_offset=None,
                                  switch_pm_text=None, switch_pm_parameter=None) -> bool:
        if isinstance(results, list):
            results = json.dumps([item for item in results])

        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.ANSWER_INLINE_QUERY, payload)

    async def edit_message_text(self, text, chat_id=None, message_id=None, inline_message_id=None, parse_mode=None,
                                disable_web_page_preview=None, reply_markup=None) -> dict or bool:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        raw = await self.request(api.ApiMethods.EDIT_MESSAGE_TEXT, payload)
        if raw is True:
            return raw
        return raw

    async def edit_message_caption(self, chat_id=None, message_id=None, inline_message_id=None, caption=None,
                                   reply_markup=None) -> dict or bool:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        raw = await self.request(api.ApiMethods.EDIT_MESSAGE_CAPTION, payload)
        if raw is True:
            return raw
        return raw

    async def edit_message_reply_markup(self, chat_id=None, message_id=None, inline_message_id=None,
                                        reply_markup=None) -> dict or bool:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())
        raw = await self.request(api.ApiMethods.EDIT_MESSAGE_REPLY_MARKUP, payload)
        if raw is True:
            return raw
        return raw

    async def delete_message(self, chat_id, message_id) -> bool:
        payload = generate_payload(**locals())
        return await self.request(api.ApiMethods.DELETE_MESSAGE, payload)

    async def send_invoice(self, chat_id: int, title: str, description: str, payload: str, provider_token: str,
                           start_parameter: str, currency: str, prices: list, photo_url: str = None,
                           photo_size: int = None, photo_width: int = None, photo_height: int = None,
                           need_name: bool = None, need_phone_number: bool = None, need_email: bool = None,
                           need_shipping_address: bool = None, is_flexible: bool = None,
                           disable_notification: bool = None, reply_to_message_id: int = None,
                           reply_markup: types.InlineKeyboardMarkup = None) -> dict:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        if isinstance(prices, list):
            prices = json.dumps(prices)

        payload_ = generate_payload(**locals())

        return await self.request(api.ApiMethods.SEND_INVOICE, payload_)

    async def answer_shipping_query(self, shipping_query_id: str, ok: bool,
                                    shipping_options: [types.ShippingOption] = None, error_message: str = None) -> bool:
        if shipping_options and isinstance(shipping_options, list):
            shipping_options = json.dumps(shipping_options)

        payload = generate_payload(**locals())

        return await self.request(api.ApiMethods.ANSWER_SHIPPING_QUERY, payload)

    async def answer_pre_checkout_query(self, pre_checkout_query_id: str, ok: bool, error_message: str = None) -> bool:
        payload = generate_payload(**locals())

        return await self.request(api.ApiMethods.ANSWER_PRE_CHECKOUT_QUERY, payload)

    async def send_game(self, chat_id: int, game_short_name: str, disable_notification: bool = None,
                        reply_to_message_id: int = None,
                        reply_markup: types.InlineKeyboardMarkup = None) -> dict:
        if reply_markup and isinstance(reply_markup, dict):
            reply_markup = json.dumps(reply_markup)

        payload = generate_payload(**locals())

        return await self.request(api.ApiMethods.SEND_GAME, payload)

    async def set_game_score(self, user_id: int, score: int, force: bool = None, disable_edit_message: bool = None,
                             chat_id: int = None, message_id: int = None,
                             inline_message_id: str = None) -> dict or bool:
        payload = generate_payload(**locals())

        raw = self.request(api.ApiMethods.SET_GAME_SCORE, payload)
        if raw is True:
            return raw
        return raw

    async def get_game_high_scores(self, user_id: int, chat_id: int = None, message_id: int = None,
                                   inline_message_id: str = None) -> dict:
        payload = generate_payload(**locals())

        return await self.request(api.ApiMethods.GET_GAME_HIGH_SCORES, payload)


class Bot(RawBot):
    """
    Base bot object
    """

    def prepare_object(self, obj, parent=None):
        """
        Setup bot instance and objects tree for object

        :param obj: instance of types.base.Serializable 
        :param parent: first parent object
        :return: configured object
        """
        obj.bot = self
        obj.parent = parent
        return obj

    @property
    async def me(self) -> types.User:
        if not hasattr(self, '_me'):
            setattr(self, '_me', await self.get_me())
        return getattr(self, '_me')

    async def get_me(self) -> types.User:
        """
        A simple method for testing your bot's auth token.

        :return: :class:`aiogram.types.User`
        """
        raw = await super(Bot, self).get_me()
        return self.prepare_object(types.User.de_json(raw))

    async def get_updates(self, offset=None, limit=None, timeout=None, allowed_updates=None) -> [types.Update]:
        """
        Use this method to receive incoming updates using long polling (wiki).
        An Array of Update objects is returned.

        :param offset: int
        :param limit: int
        :param timeout: int
        :param allowed_updates: list 
        :return: list of :class:`aiogram.types.Update`
        """
        raw = await super(Bot, self).get_updates(offset, limit, timeout, allowed_updates)
        return [self.prepare_object(types.Update.de_json(raw_update)) for raw_update in raw]

    async def set_webhook(self, url, certificate=None, max_connections=None, allowed_updates=None) -> types.WebhookInfo:
        """
        Use this method to specify a url and receive incoming updates via an outgoing webhook.
    
        :param url: str
        :param certificate: file
        :param max_connections: int 
        :param allowed_updates: list of str
        :return: :class:`aiogram.types.WebhookInfo`
        """
        req = super(Bot, self).set_webhook(url, certificate, max_connections)
        return self.prepare_object(types.WebhookInfo.de_json(await req))

    async def delete_webhook(self) -> bool:
        """
        Use this method to remove webhook integration if you decide to switch back to getUpdates.
        
        :return: bool
        :raise: :class:`aiogram.exceptions.TelegramAPIError`
        """
        return await super(Bot, self).delete_webhook()

    async def get_webhook_info(self) -> types.WebhookInfo:
        """
        Use this method to get current webhook status.
        
        :return: :class:`aiogram.types.WebhookInfo`
        """
        webhook_info = await super(Bot, self).get_webhook_info()
        return self.prepare_object(webhook_info)

    async def send_message(self, chat_id, text, parse_mode=None, disable_web_page_preview=None,
                           disable_notification=None, reply_to_message_id=None, reply_markup=None) -> types.Message:
        """
        Use this method to send text messages.
        
        :param chat_id: int 
        :param text: str
        :param parse_mode: str
        :param disable_web_page_preview: bool
        :param disable_notification: bool
        :param reply_to_message_id: int
        :param reply_markup: :class:`aiogram.types.Serializable` 
        :return: :class:`aiogram.types.Message` 
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        message = await super(Bot, self).send_message(chat_id, text, parse_mode, disable_web_page_preview,
                                                      disable_notification, reply_to_message_id, reply_markup)
        return self.prepare_object(types.Message.de_json(message))

    async def forward_message(self, chat_id, from_chat_id, message_id, disable_notification=None) -> types.Message:
        """
        Use this method to forward messages of any kind. 
        
        :param chat_id: int 
        :param from_chat_id: int 
        :param message_id: int
        :param disable_notification: bool 
        :return: :class:`aiogram.types.Message`
        """
        message = await super(Bot, self).forward_message(chat_id, from_chat_id, message_id, disable_notification)
        return self.prepare_object(types.Message.de_json(message))

    async def send_photo(self, chat_id, photo, caption=None, disable_notification=None, reply_to_message_id=None,
                         reply_markup=None) -> types.Message:
        """
        Use this method to send photos.
        
        :param chat_id: int
        :param photo: file or str
        :param caption: str
        :param disable_notification: bool 
        :param reply_to_message_id: int
        :param reply_markup: :class:`aiogram.types.Serializable`
        :return: :class:`aiogram.types.Message`
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        message = await super(Bot, self).send_photo(chat_id, photo, caption, disable_notification, reply_to_message_id,
                                                    reply_markup)
        return self.prepare_object(types.Message.de_json(message))

    async def send_audio(self, chat_id, audio, caption=None, duration=None, performer=None, title=None,
                         disable_notification=None, reply_to_message_id=None, reply_markup=None) -> types.Message:
        """
        Use this method to send audio files, if you want Telegram clients to display them in the music player.
        Your audio must be in the .mp3 format.
        
        :param chat_id: int 
        :param audio: file or str
        :param caption: str
        :param duration: int
        :param performer: str
        :param title: str
        :param disable_notification: bool 
        :param reply_to_message_id: int
        :param reply_markup: :class:`aiogram.types.Serializable`
        :return: :class:`aiogram.types.Message`
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        message = await super(Bot, self).send_audio(chat_id, audio, caption, duration, performer, title,
                                                    disable_notification, reply_to_message_id, reply_markup)
        return self.prepare_object(types.Message.de_json(message))

    async def send_document(self, chat_id, document, caption=None, disable_notification=None, reply_to_message_id=None,
                            reply_markup=None) -> types.Message:
        """
        Use this method to send general files.

        :param chat_id: int
        :param document: file or str 
        :param caption: str
        :param disable_notification: bool 
        :param reply_to_message_id: int
        :param reply_markup: :class:`aiogram.types.Serializable`
        :return: :class:`aiogram.types.Message`
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        message = await super(Bot, self).send_document(chat_id, document, caption, disable_notification,
                                                       reply_to_message_id, reply_markup)
        return self.prepare_object(types.Message.de_json(message))

    async def send_sticker(self, chat_id, sticker, disable_notification=None, reply_to_message_id=None,
                           reply_markup=None) -> types.Message:
        """
        Use this method to send .webp stickers. 

        :param chat_id: int
        :param sticker: file or str
        :param disable_notification: bool 
        :param reply_to_message_id: int
        :param reply_markup: :class:`aiogram.types.Serializable`
        :return: :class:`aiogram.types.Message`
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        message = super(Bot, self).send_sticker(chat_id, sticker, disable_notification, reply_to_message_id,
                                                reply_markup)
        return self.prepare_object(types.Message.de_json(message))

    async def send_video(self, chat_id, video, duration=None, width=None, height=None, caption=None,
                         disable_notification=None, reply_to_message_id=None, reply_markup=None) -> types.Message:
        """
        Use this method to send video files, 
        Telegram clients support mp4 videos (other formats may be sent as Document).
        
        :param chat_id: int
        :param video: file or str
        :param duration: int
        :param width: int
        :param height: int
        :param caption: str
        :param disable_notification: bool
        :param reply_to_message_id: int
        :param reply_markup: :class:`aiogram.types.Serializable`
        :return: :class:`aiogram.types.Message`
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        message = await super(Bot, self).send_video(chat_id, video, duration, width, height, caption,
                                                    disable_notification, reply_to_message_id, reply_markup)
        return self.prepare_object(types.Message.de_json(message))

    async def send_voice(self, chat_id, voice, caption=None, duration=None, disable_notification=None,
                         reply_to_message_id=None, reply_markup=None) -> types.Message:
        """
        Use this method to send audio files, if you want Telegram clients to display the file as a 
        playable voice message.
        For this to work, your audio must be in an .ogg file encoded with OPUS 
        (other formats may be sent as Audio or Document).
        
        :param chat_id: int
        :param voice: file or str
        :param caption: str
        :param duration: int
        :param disable_notification: bool
        :param reply_to_message_id: int
        :param reply_markup: :class:`aiogram.types.Serializable`
        :return: :class:`aiogram.types.Message`
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        message = await super(Bot, self).send_voice(chat_id, voice, caption, duration, disable_notification,
                                                    reply_to_message_id, reply_markup)
        return self.prepare_object(types.Message.de_json(message))

    async def send_video_note(self, chat_id, video_note, duration=None, length=None, disable_notification=None,
                              reply_to_message_id=None, reply_markup=None) -> types.Message:
        """
        Use this method to send video messages.

        :param chat_id: int
        :param video_note: file or str
        :param duration: int 
        :param length: int
        :param disable_notification: bool
        :param reply_to_message_id: int
        :param reply_markup: :class:`aiogram.types.Serializable`
        :return: :class:`aiogram.types.Message`
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        message = await super(Bot, self).send_video_note(chat_id, video_note, duration, length, disable_notification,
                                                         reply_to_message_id, reply_markup)
        return self.prepare_object(types.Message.de_json(message))

    async def send_location(self, chat_id, latitude, longitude, disable_notification=None, reply_to_message_id=None,
                            reply_markup=None) -> types.Message:
        """
        Use this method to send point on the map.
        
        :param chat_id: int
        :param latitude: float
        :param longitude: float
        :param disable_notification: bool
        :param reply_to_message_id: int
        :param reply_markup: :class:`aiogram.types.Serializable`
        :return: :class:`aiogram.types.Message`
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        message = super(Bot, self).send_location(chat_id, latitude, longitude, disable_notification,
                                                 reply_to_message_id, reply_markup)
        return self.prepare_object(types.Message.de_json(message))

    async def send_venue(self, chat_id, latitude, longitude, title, address, foursquare_id, disable_notification=None,
                         reply_to_message_id=None, reply_markup=None) -> types.Message:
        """
        
        :param chat_id: int
        :param latitude: float
        :param longitude: float
        :param title: str
        :param address: str
        :param foursquare_id: str
        :param disable_notification: bool
        :param reply_to_message_id: int
        :param reply_markup: :class:`aiogram.types.Serializable`
        :return: :class:`aiogram.types.Message`
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        message = await super(Bot, self).send_venue(chat_id, latitude, longitude, title, address, foursquare_id,
                                                    disable_notification, reply_to_message_id, reply_markup)
        return self.prepare_object(types.Message.de_json(message))

    async def send_contact(self, chat_id, phone_number, first_name, last_name=None, disable_notification=None,
                           reply_to_message_id=None, reply_markup=None) -> types.Message:
        """
        Use this method to send phone contacts.
        
        :param chat_id: int
        :param phone_number: str 
        :param first_name: str
        :param last_name: str
        :param disable_notification: bool
        :param reply_to_message_id: int
        :param reply_markup: :class:`aiogram.types.Serializable`
        :return: :class:`aiogram.types.Message`
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(reply_to_message_id, 'message_id'):
            reply_to_message_id = reply_to_message_id.message_id

        message = await super(Bot, self).send_contact(chat_id, phone_number, first_name, last_name,
                                                      disable_notification, reply_to_message_id, reply_markup)
        return self.prepare_object(types.Message.de_json(message))

    async def send_chat_action(self, chat_id, action) -> bool:
        """
        Use this method when you need to tell the user that something is happening on the bot's side. 
        The status is set for 5 seconds or less 
        (when a message arrives from your bot, Telegram clients clear its typing status).

        :param chat_id: int
        :param action: str
        :return: bool
        """
        return await super(Bot, self).send_chat_action(chat_id, action)

    async def get_user_profile_photos(self, user_id, offset=None, limit=None) -> types.UserProfilePhotos:
        """
        Use this method to get a list of profile pictures for a user. 

        :param user_id: int 
        :param offset: int
        :param limit: int
        :return: :class:`aiogram.types.UserProfilePhotos`
        """
        message = await super(Bot, self).get_user_profile_photos(user_id, offset, limit)
        return self.prepare_object(types.UserProfilePhotos.de_json(message))

    async def get_file(self, file_id) -> types.File:
        """
        Use this method to get basic info about a file and prepare it for downloading.
        For the moment, bots can download files of up to 20MB in size.

        :param file_id: str
        :return: :class:`aiogram.types.File` 
        """
        payload = generate_payload(**locals())
        file = await super(Bot, self).get_file(file_id)
        return self.prepare_object(types.File.de_json(file))

    async def kick_chat_user(self, chat_id, user_id) -> bool:
        """
        Use this method to kick a user from a group or a supergroup. In the case of supergroups, 
        the user will not be able to return to the group on their own using invite links, etc., 
        unless unbanned first. The bot must be an administrator in the group for this to work. 

        :param chat_id: int
        :param user_id: int
        :return: bool
        """
        return await super(Bot, self).kick_chat_user(chat_id, user_id)

    async def unban_chat_member(self, chat_id, user_id) -> bool:
        """
        Use this method to unban a previously kicked user in a supergroup or channel. 
        The user will not return to the group or channel automatically, but will be able to join via link, etc. 
        The bot must be an administrator for this to work. 
        
        :param chat_id: int
        :param user_id: int
        :return: bool
        """
        return await super(Bot, self).unban_chat_member(chat_id, user_id)

    async def leave_chat(self, chat_id) -> bool:
        """
        Use this method for your bot to leave a group, supergroup or channel.
        
        :param chat_id: int 
        :return: bool 
        """
        return await super(Bot, self).leave_chat(chat_id)

    async def get_chat(self, chat_id) -> types.Chat:
        """
        Use this method to get up to date information about the chat 
        (current name of the user for one-on-one conversations, 
        current username of a user, group or channel, etc.).
        
        :param chat_id: int 
        :return: :class:`aiogram.types.Chat` 
        """
        chat = await super(Bot, self).get_chat(chat_id)
        return self.prepare_object(types.Chat.de_json(chat))

    async def get_chat_administrators(self, chat_id) -> [types.ChatMember]:
        """
        Use this method to get a list of administrators in a chat. 
        On success, returns an Array of ChatMember objects that 
        contains information about all chat administrators except other bots. 
        If the chat is a group or a supergroup and no administrators were appointed, 
        only the creator will be returned.
        
        :param chat_id: int
        :return: array of :class:`aiogram.types.ChatMember` 
        """
        raw = await super(Bot, self).get_chat_administrators(chat_id)
        return [self.prepare_object(types.ChatMember.de_json(raw_chat_member)) for raw_chat_member in raw]

    async def get_chat_members_count(self, chat_id) -> int:
        """
        Use this method to get the number of members in a chat.

        :param chat_id: int 
        :return: int
        """
        return await super(Bot, self).get_chat_members_count(chat_id)

    async def get_chat_member(self, chat_id, user_id) -> types.ChatMember:
        """
        Use this method to get information about a member of a chat.

        :param chat_id: int
        :param user_id: int
        :return: :class:`aiogram.types.ChatMembers`
        """
        raw = await super(Bot, self).get_chat_member(chat_id, user_id)
        return self.prepare_object(types.ChatMember.de_json(raw))

    async def answer_callback_query(self, callback_query_id, text=None, show_alert=None, url=None,
                                    cache_time=None) -> bool:
        """
        Use this method to send answers to callback queries sent from inline keyboards. 
        The answer will be displayed to the user as a notification at the top of the chat screen or as an alert.
    
        :param callback_query_id: int
        :param text: str
        :param show_alert: bool 
        :param url: str
        :param cache_time: int 
        :return: bool
        """
        return await super(Bot, self).answer_callback_query(callback_query_id, text, show_alert, url, cache_time)

    async def answer_inline_query(self, inline_query_id, results, cache_time=None, is_personal=None, next_offset=None,
                                  switch_pm_text=None, switch_pm_parameter=None) -> bool:
        """
        Use this method to send answers to an inline query. 
        No more than 50 results per query are allowed.

        :param inline_query_id: int
        :param results: Array of :class:`InlineQueryResult`
        :param cache_time: int
        :param is_personal: bool
        :param next_offset: int
        :param switch_pm_text: str
        :param switch_pm_parameter: str 
        :return: bool
        """
        results = json.dumps([item.to_json() for item in results])

        return await super(Bot, self).answer_inline_query(inline_query_id, results, cache_time, is_personal,
                                                          next_offset, switch_pm_text, switch_pm_parameter)

    async def edit_message_text(self, text, chat_id=None, message_id=None, inline_message_id=None, parse_mode=None,
                                disable_web_page_preview=None, reply_markup=None) -> types.Message or bool:
        """
        Use this method to edit text and game messages sent by the bot or via the bot (for inline bots).
        On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.
        
        :param text: str
        :param chat_id: int
        :param message_id: int
        :param inline_message_id: int 
        :param parse_mode: str
        :param disable_web_page_preview: bool 
        :param reply_markup: 
        :return: :class:`aiogram.types.Message` or bool
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(message_id, 'message_id'):
            message_id = message_id.message_id

        if hasattr(inline_message_id, 'message_id'):
            inline_message_id = inline_message_id.message_id

        raw = await super(Bot, self).edit_message_text(text, chat_id, message_id, inline_message_id, parse_mode,
                                                       disable_web_page_preview, reply_markup)
        if raw is True:
            return raw
        return self.prepare_object(types.Message.de_json(raw))

    async def edit_message_caption(self, chat_id=None, message_id=None, inline_message_id=None, caption=None,
                                   reply_markup=None) -> types.Message or bool:
        """
        Use this method to edit captions of messages sent by the bot or via the bot (for inline bots).
        On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.
        
        :param chat_id: int
        :param message_id: int
        :param inline_message_id: int  
        :param caption: str
        :param reply_markup:  
        :return: :class:`aiogram.types.Message` or bool
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(message_id, 'message_id'):
            message_id = message_id.message_id

        if hasattr(inline_message_id, 'message_id'):
            inline_message_id = inline_message_id.message_id

        raw = await super(Bot, self).edit_message_caption(chat_id, message_id, inline_message_id, caption, reply_markup)
        if raw is True:
            return raw
        return self.prepare_object(types.Message.de_json(raw))

    async def edit_message_reply_markup(self, chat_id=None, message_id=None, inline_message_id=None,
                                        reply_markup=None) -> types.Message or bool:
        """
        Use this method to edit only the reply markup of messages sent by the bot or via the bot (for inline bots).
        On success, if edited message is sent by the bot, the edited Message is returned, otherwise True is returned.
        
        :param chat_id: int
        :param message_id: int
        :param inline_message_id: int 
        :param reply_markup: 
        :return: :class:`aiogram.types.Message` or bool
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        if hasattr(message_id, 'message_id'):
            message_id = message_id.message_id

        if hasattr(inline_message_id, 'message_id'):
            inline_message_id = inline_message_id.message_id

        raw = await super(Bot, self).edit_message_reply_markup(chat_id, message_id, inline_message_id, reply_markup)
        if raw is True:
            return raw
        return self.prepare_object(types.Message.de_json(raw))

    async def delete_message(self, chat_id, message_id) -> bool:
        """
        Use this method to delete a message. 
        A message can only be deleted if it was sent less than 48 hours ago. 
        Any such recently sent outgoing message may be deleted. Additionally, 
        if the bot is an administrator in a group chat, it can delete any message. 
        If the bot is an administrator in a supergroup, it can delete messages 
        from any other user and service messages about people joining or leaving the group 
        (other types of service messages may only be removed by the group creator). 
        In channels, bots can only remove their own messages.
        
        :param chat_id: int
        :param message_id: int
        :return: 
        """
        return await super(Bot, self).delete_message(chat_id, message_id)

    async def send_invoice(self, chat_id: int, title: str, description: str, payload: str, provider_token: str,
                           start_parameter: str, currency: str, prices: [types.LabeledPrice], photo_url: str = None,
                           photo_size: int = None, photo_width: int = None, photo_height: int = None,
                           need_name: bool = None, need_phone_number: bool = None, need_email: bool = None,
                           need_shipping_address: bool = None, is_flexible: bool = None,
                           disable_notification: bool = None, reply_to_message_id: int = None,
                           reply_markup: types.InlineKeyboardMarkup = None) -> types.Message:
        """
        Use this method to send invoices.
        
        :param chat_id: int
        :param title: str
        :param description:str 
        :param payload: str
        :param provider_token: str 
        :param start_parameter: str 
        :param currency: str
        :param prices: list of :class:`aiogram.typesLabeledPrice`
        :param photo_url: str
        :param photo_size: int
        :param photo_width: int
        :param photo_height: int
        :param need_name: bool
        :param need_phone_number: bool 
        :param need_email: bool
        :param need_shipping_address: bool 
        :param is_flexible: bool
        :param disable_notification: bool 
        :param reply_to_message_id: int
        :param reply_markup: :class:`aiogram.types.InlineReplyMarkup`
        :return: :class:`aiogram.types.Message`
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())
        prices = json.dumps([item.to_json() for item in prices])

        message = await super(Bot, self).send_invoice(chat_id, title, description, payload, provider_token,
                                                      start_parameter, currency, prices, photo_url, photo_size,
                                                      photo_width, photo_height, need_name, need_phone_number,
                                                      need_email, need_shipping_address, is_flexible,
                                                      disable_notification, reply_to_message_id, reply_markup)
        return self.prepare_object(types.Message.de_json(message))

    async def answer_shipping_query(self, shipping_query_id: str, ok: bool,
                                    shipping_options: [types.ShippingOption] = None, error_message: str = None) -> bool:
        """
        If you sent an invoice requesting a shipping address and the parameter is_flexible was specified, 
        the Bot API will send an Update with a shipping_query field to the bot. 
        Use this method to reply to shipping queries. 
        
        :param shipping_query_id: str
        :param ok: bool
        :param shipping_options: list of :class:`aiogram.types.ShippingOption` 
        :param error_message: str
        :return: bool
        """
        shipping_options = json.dumps([item.to_json() for item in shipping_options])

        return await super(Bot, self).answer_shipping_query(shipping_query_id, ok, shipping_options, error_message)

    async def answer_pre_checkout_query(self, pre_checkout_query_id: str, ok: bool, error_message: str = None) -> bool:
        """
        Once the user has confirmed their payment and shipping details, 
        the Bot API sends the final confirmation in the form of an Update with the field pre_checkout_query. 
        Use this method to respond to such pre-checkout queries. 
        
        Note: The Bot API must receive an answer within 10 seconds after the pre-checkout query was sent.
        
        :param pre_checkout_query_id: str
        :param ok: bool
        :param error_message: str 
        :return: bool
        """
        return await super(Bot, self).answer_pre_checkout_query(pre_checkout_query_id, ok, error_message)

    async def send_game(self, chat_id: int, game_short_name: str, disable_notification: bool = None,
                        reply_to_message_id: int = None,
                        reply_markup: types.InlineKeyboardMarkup = None) -> types.Message:
        """
        Use this method to send a game.
        
        :param chat_id: int
        :param game_short_name: str 
        :param disable_notification: bool 
        :param reply_to_message_id: int
        :param reply_markup: :class:`aiogram.types.InlineKeyboardMarkup`
        :return: :class:`aiogram.types.Message`
        """
        if reply_markup and hasattr(reply_markup, 'to_json'):
            reply_markup = json.dumps(reply_markup.to_json())

        message = await super(Bot, self).send_game(chat_id, game_short_name, disable_notification, reply_to_message_id,
                                                   reply_markup)
        return self.prepare_object(types.Message.de_json(message))

    async def set_game_score(self, user_id: int, score: int, force: bool = None, disable_edit_message: bool = None,
                             chat_id: int = None, message_id: int = None,
                             inline_message_id: str = None) -> types.Message or bool:
        """
        Use this method to set the score of the specified user in a game. On success, 
        if the message was sent by the bot, returns the edited Message, otherwise returns True. 
        Returns an error, if the new score is not greater than the user's current score in the chat and force is False.
        
        :param user_id: int
        :param score: int
        :param force: bool
        :param disable_edit_message: bool 
        :param chat_id: int
        :param message_id: int
        :param inline_message_id: str 
        :return: :class:`aiogram.types.Message` or bool
        """
        raw = await super(Bot, self).set_game_score(user_id, score, force, disable_edit_message, chat_id, message_id,
                                                    inline_message_id)
        if raw is True:
            return raw
        return self.prepare_object(types.Message.de_json(raw))

    async def get_game_high_scores(self, user_id: int, chat_id: int = None, message_id: int = None,
                                   inline_message_id: str = None) -> types.GameHighScore:
        """
        Use this method to get data for high score tables. 
        Will return the score of the specified user and several of his neighbors in a game. 
        On success, returns an Array of GameHighScore objects.
        
        :param user_id: int
        :param chat_id: int
        :param message_id: int
        :param inline_message_id: str 
        :return: :class:`aiogram.types.GameHighScore`
        """
        req = await super(Bot, self).get_game_high_scores(user_id, chat_id, message_id, inline_message_id)
        return self.prepare_object(types.GameHighScore.de_json(req))
