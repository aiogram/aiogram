from .base import *
from .. import types


class Bot(BaseBot):
    """
    Main bot class.
    Based on :class:`aiogram.bot.BaseBot` and in this module is realized data serialization. 
    """

    def prepare_object(self, obj, parent=None):
        """
        Setup bot instance and objects tree for object

        :param obj: instance of :class:`types.base.Deserializable`
        :param parent: first parent object
        :return: configured object
        """
        obj.bot = self
        obj.parent = parent
        return obj

    @property
    async def me(self) -> types.User:
        """
        Alias for self.get_me() but lazy and with caching.

        :return: :class:`aiogram.types.User`
        """
        if not hasattr(self, '_me'):
            setattr(self, '_me', await self.get_me())
        return getattr(self, '_me')

    @me.deleter
    def me(self):
        """
        Reset `me`

        :return:
        """
        if hasattr(self, '_me'):
            delattr(self, '_me')

    async def download_file(self, file_path: str, destination: io.BytesIO or str = None, timeout: int = 30,
                            chunk_size: int = 65536, seek: bool = True) -> io.BytesIO:
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
        return await super(Bot, self).download_file(file_path=file_path, destination=destination, timeout=timeout,
                                                    chunk_size=chunk_size, seek=seek)

    async def download_file_by_id(self, file_id, destination=None, timeout=30, chunk_size=65536, seek=True):
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
        file = await self.get_file(file_id)
        return await self.download_file(file_path=file.file_path, destination=destination, timeout=timeout,
                                        chunk_size=chunk_size, seek=seek)

    # === Getting updates ===
    # https://core.telegram.org/bots/api#getting-updates

    async def get_updates(self, offset: Optional[Integer] = None,
                          limit: Optional[Integer] = None,
                          timeout: Optional[Integer] = None,
                          allowed_updates: Optional[List[String]] = None) -> List[types.Update]:
        """
        Use this method to receive incoming updates using long polling (wiki). An Array of Update objects is returned.

        Notes
            1. This method will not work if an outgoing webhook is set up.
            2. In order to avoid getting duplicate updates, recalculate offset after each server response.

        Source: https://core.telegram.org/bots/api#getupdates

        :param offset: Integer (Optional) - Identifier of the first update to be returned. Must be greater
            by one than the highest among the identifiers of previously received updates.
            By default, updates starting with the earliest unconfirmed update are returned.
            An update is considered confirmed as soon as getUpdates is called with an offset higher than its update_id.
            The negative offset can be specified to retrieve updates starting from -
            offset update from the end of the updates queue.
            All previous updates will forgotten.
        :param limit: Integer (Optional) - Limits the number of updates to be retrieved.
            Values between 1—100 are accepted. Defaults to 100.
        :param timeout: Integer (Optional) - Timeout in seconds for long polling.
            Defaults to 0, i.e. usual short polling.
            Should be positive, short polling should be used for testing purposes only.
        :param allowed_updates: List[String] (Optional) - List the types of updates you want your bot to receive.
            For example, specify [“message”, “edited_channel_post”, “callback_query”]
            to only receive updates of these types.
            See Update for a complete list of available update types.
            Specify an empty list to receive all updates regardless of type (default).
            If not specified, the previous setting will be used.

            Please note that this parameter doesn't affect updates created before the call to the getUpdates,
            so unwanted updates may be received for a short period of time.
        :return: An Array of Update objects is returned.
        """
        raw = super(Bot, self).get_updates(offset=offset, limit=limit, timeout=timeout,
                                           allowed_updates=allowed_updates)
        return [self.prepare_object(types.Update.de_json(raw_update)) for raw_update in await raw]

    async def get_webhook_info(self) -> types.WebhookInfo:
        """
        Use this method to get current webhook status. Requires no parameters. On success,
            returns a WebhookInfo object. If the bot is using getUpdates, will return an object
            with the url field empty.

        Source: https://core.telegram.org/bots/api#getwebhookinfo

        :return: On success, returns a WebhookInfo object.
        """
        raw = super(Bot, self).get_webhook_info()
        return self.prepare_object(types.WebhookInfo.deserialize(await raw))

    # === Base methods ===
    # https://core.telegram.org/bots/api#available-methods

    async def get_me(self) -> types.User:
        """
        A simple method for testing your bot's auth token. Requires no parameters.
            Returns basic information about the bot in form of a User object.

        Source: https://core.telegram.org/bots/api#getme

        :return: Returns basic information about the bot in form of a User object.
        """
        raw = super(Bot, self).get_me()
        return self.prepare_object(types.User.deserialize(await raw))

    async def send_message(self, chat_id: Union[Integer, String],
                           text: String, parse_mode: Optional[String] = None,
                           disable_web_page_preview: Optional[Boolean] = None,
                           disable_notification: Optional[Boolean] = None,
                           reply_to_message_id: Optional[Integer] = None,
                           reply_markup: Optional[Union[
                               types.InlineKeyboardMarkup,
                               types.ReplyKeyboardMarkup, Dict, String]] = None) -> types.Message:
        """
        Use this method to send text messages. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendmessage

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param text: String - Text of the message to be sent
        :param parse_mode: String (Optional) - Send Markdown or HTML, if you want Telegram apps to show bold,
            italic, fixed-width text or inline URLs in your bot's message.
        :param disable_web_page_preview: Boolean (Optional) - Disables link previews for links in this message
        :param disable_notification: Boolean (Optional) - Sends the message silently. Users will receive
            a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        raw = super(Bot, self).send_message(chat_id=chat_id,
                                            text=text, parse_mode=parse_mode,
                                            disable_web_page_preview=disable_web_page_preview,
                                            disable_notification=disable_notification,
                                            reply_to_message_id=reply_to_message_id,
                                            reply_markup=reply_markup)
        return self.prepare_object(types.Message.deserialize(await raw))

    async def forward_message(self, chat_id: Union[Integer, String],
                              from_chat_id: Union[Integer, String],
                              message_id: Integer,
                              disable_notification: Optional[Boolean] = None) -> types.Message:
        """
        Use this method to forward messages of any kind. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#forwardmessage

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username of the
            target channel (in the format @channelusername)
        :param from_chat_id: Union[Integer, String] - Unique identifier for the chat where the original
            message was sent (or channel username in the format @channelusername)
        :param disable_notification: Boolean (Optional) - Sends the message silently. Users will receive a
            notification with no sound.
        :param message_id: Integer - Message identifier in the chat specified in from_chat_id
        :return: On success, the sent Message is returned.
        """
        raw = super(Bot, self).forward_message(chat_id=chat_id, from_chat_id=from_chat_id,
                                               message_id=message_id, disable_notification=disable_notification)
        return self.prepare_object(types.Message.deserialize(await raw))

    async def send_photo(self, chat_id: Union[Integer, String],
                         photo: Union[io.BytesIO, io.FileIO, String],
                         caption: Optional[String] = None,
                         disable_notification: Optional[Boolean] = None,
                         reply_to_message_id: Optional[Integer] = None,
                         reply_markup: Optional[Union[
                             types.InlineKeyboardMarkup,
                             types.ReplyKeyboardMarkup, Dict, String]] = None) -> types.Message:
        """
        Use this method to send photos. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendphoto

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username of
            the target channel (in the format @channelusername)
        :param photo: Union[io.BytesIO, io.FileIO, String] - Photo to send. Pass a file_id as String to send
            a photo that exists on the Telegram servers (recommended), pass an HTTP URL as a String for
            Telegram to get a photo from the Internet, or upload a new photo using multipart/form-data.
        :param caption: String (Optional) - Photo caption (may also be used when resending photos by file_id),
            0-200 characters
        :param disable_notification: Boolean (Optional) - Sends the message silently. Users will receive
            a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        raw = super(Bot, self).send_photo(chat_id=chat_id, photo=photo, caption=caption,
                                          disable_notification=disable_notification,
                                          reply_to_message_id=reply_to_message_id,
                                          reply_markup=reply_markup)
        return self.prepare_object(types.Message.deserialize(await raw))

    async def send_audio(self, chat_id: Union[Integer, String],
                         audio: Union[io.BytesIO, io.FileIO, String],
                         caption: Optional[String] = None,
                         duration: Optional[Integer] = None,
                         performer: Optional[String] = None,
                         title: Optional[String] = None,
                         disable_notification: Optional[Boolean] = None,
                         reply_to_message_id: Optional[Integer] = None,
                         reply_markup: Optional[Union[
                             types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String]] = None) -> Dict:
        """
        Use this method to send audio files, if you want Telegram clients to display them in the music player.
            Your audio must be in the .mp3 format. On success, the sent Message is returned.
            Bots can currently send audio files of up to 50 MB in size, this limit may be changed in the future.

        For sending voice messages, use the sendVoice method instead.

        Source: https://core.telegram.org/bots/api#sendaudio

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param audio: Union[io.BytesIO, io.FileIO, String] - Audio file to send. Pass a file_id as String
            to send an audio file that exists on the Telegram servers (recommended), pass an HTTP URL
            as a String for Telegram to get an audio file from the Internet, or upload a new one
            using multipart/form-data.
        :param caption: String (Optional) - Audio caption, 0-200 characters
        :param duration: Integer (Optional) - Duration of the audio in seconds
        :param performer: String (Optional) - Performer
        :param title: String (Optional) - Track name
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        raw = super(Bot, self).send_audio(chat_id=chat_id, audio=audio, caption=caption,
                                          duration=duration, performer=performer, title=title,
                                          disable_notification=disable_notification,
                                          reply_to_message_id=reply_to_message_id,
                                          reply_markup=reply_markup)
        return self.prepare_object(types.Message.deserialize(await raw))

    async def send_document(self, chat_id: Union[Integer, String],
                            document: Union[io.BytesIO, io.FileIO, String],
                            caption: Optional[String] = None,
                            disable_notification: Optional[Boolean] = None,
                            reply_to_message_id: Optional[Integer] = None,
                            reply_markup: Optional[Union[
                                types.InlineKeyboardMarkup,
                                types.ReplyKeyboardMarkup, Dict, String]] = None) -> types.Message:
        """
        Use this method to send general files. On success, the sent Message is returned.
            Bots can currently send files of any type of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#senddocument

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param document: Union[io.BytesIO, io.FileIO, String] - File to send. Pass a file_id as String
            to send a file that exists on the Telegram servers (recommended), pass an HTTP URL
            as a String for Telegram to get a file from the Internet, or upload a new one
            using multipart/form-data.
        :param caption: String (Optional) - Document caption
            (may also be used when resending documents by file_id), 0-200 characters
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        raw = super(Bot, self).send_document(chat_id=chat_id, document=document, caption=caption,
                                             disable_notification=disable_notification,
                                             reply_to_message_id=reply_to_message_id,
                                             reply_markup=reply_markup)
        return self.prepare_object(types.Message.deserialize(await raw))

    async def send_video(self, chat_id: Union[Integer, String],
                         video: Union[io.BytesIO, io.FileIO, String],
                         duration: Optional[Integer] = None,
                         width: Optional[Integer] = None,
                         height: Optional[Integer] = None,
                         caption: Optional[String] = None,
                         disable_notification: Optional[Boolean] = None,
                         reply_to_message_id: Optional[Integer] = None,
                         reply_markup: Optional[Union[
                             types.InlineKeyboardMarkup,
                             types.ReplyKeyboardMarkup, Dict, String]] = None) -> types.Message:
        """
        Use this method to send video files, Telegram clients support mp4 videos
            (other formats may be sent as Document). On success, the sent Message is returned.
            Bots can currently send video files of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendvideo

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param video: Union[io.BytesIO, io.FileIO, String] - Video to send. Pass a file_id as String
            to send a video that exists on the Telegram servers (recommended), pass an HTTP URL
            as a String for Telegram to get a video from the Internet, or upload a new video
            using multipart/form-data.
        :param duration: Integer (Optional) - Duration of sent video in seconds
        :param width: Integer (Optional) - Video width
        :param height: Integer (Optional) - Video height
        :param caption: String (Optional) - Video caption (may also be used when resending videos by file_id),
            0-200 characters
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        raw = super(Bot, self).send_video(chat_id=chat_id, video=video, duration=duration,
                                          width=width, height=height, caption=caption,
                                          disable_notification=disable_notification,
                                          reply_to_message_id=reply_to_message_id, reply_markup=reply_markup)
        return self.prepare_object(types.Message.deserialize(await raw))

    async def send_voice(self, chat_id: Union[Integer, String],
                         voice: Union[io.BytesIO, io.FileIO, String],
                         caption: Optional[String] = None,
                         duration: Optional[Integer] = None,
                         disable_notification: Optional[Boolean] = None,
                         reply_to_message_id: Optional[Integer] = None,
                         reply_markup: Optional[Union[
                             types.InlineKeyboardMarkup,
                             types.ReplyKeyboardMarkup, Dict, String]] = None) -> types.Message:
        """
        Use this method to send audio files, if you want Telegram clients to display the file
            as a playable voice message. For this to work, your audio must be in an .ogg file encoded with OPUS
            (other formats may be sent as Audio or Document). On success, the sent Message is returned.
            Bots can currently send voice messages of up to 50 MB in size, this limit may be changed in the future.

        Source: https://core.telegram.org/bots/api#sendvoice

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param voice: Union[io.BytesIO, io.FileIO, String] - Audio file to send. Pass a file_id as String
            to send a file that exists on the Telegram servers (recommended), pass an HTTP URL
            as a String for Telegram to get a file from the Internet, or upload a new one
            using multipart/form-data.
        :param caption: String (Optional) - Voice message caption, 0-200 characters
        :param duration: Integer (Optional) - Duration of the voice message in seconds
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard, custom reply keyboard,
            instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        raw = super(Bot, self).send_voice(chat_id=chat_id, voice=voice, caption=caption,
                                          duration=duration,
                                          disable_notification=disable_notification,
                                          reply_to_message_id=reply_to_message_id,
                                          reply_markup=reply_markup)
        return self.prepare_object(types.Message.deserialize(await raw))

    async def send_video_note(self, chat_id: Union[Integer, String],
                              video_note: Union[io.BytesIO, io.FileIO, String],
                              duration: Optional[Integer] = None,
                              length: Optional[Integer] = None,
                              disable_notification: Optional[Boolean] = None,
                              reply_to_message_id: Optional[Integer] = None,
                              reply_markup: Optional[Union[
                                  types.InlineKeyboardMarkup,
                                  types.ReplyKeyboardMarkup, Dict, String]] = None) -> types.Message:
        """
        As of v.4.0, Telegram clients support rounded square mp4 videos of up to 1 minute long. Use this method
            to send video messages. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendvideonote

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param video_note: Union[io.BytesIO, io.FileIO, String] - Video note to send. Pass a file_id
            as String to send a video note that exists on the Telegram servers (recommended)
            or upload a new video using multipart/form-data. Sending video notes by a URL is currently unsupported
        :param duration: Integer (Optional) - Duration of sent video in seconds
        :param length: Integer (Optional) - Video width and height
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        raw = super(Bot, self).send_video_note(chat_id=chat_id, video_note=video_note, duration=duration, length=length,
                                               disable_notification=disable_notification,
                                               reply_to_message_id=reply_to_message_id, reply_markup=reply_markup)
        return self.prepare_object(types.Message.deserialize(await raw))

    async def send_location(self, chat_id: Union[Integer, String],
                            latitude: Float, longitude: Float,
                            disable_notification: Optional[Boolean] = None,
                            reply_to_message_id: Optional[Integer] = None,
                            reply_markup: Optional[Union[
                                types.InlineKeyboardMarkup,
                                types.ReplyKeyboardMarkup, Dict, String]] = None) -> types.Message:
        """
        Use this method to send point on the map. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendlocation

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param latitude: Float - Latitude of location
        :param longitude: Float - Longitude of location
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        raw = super(Bot, self).send_location(chat_id=chat_id, latitude=latitude, longitude=longitude,
                                             disable_notification=disable_notification,
                                             reply_to_message_id=reply_to_message_id)
        return self.prepare_object(types.Message.deserialize(await raw))

    async def send_venue(self, chat_id: Union[Integer, String],
                         latitude: Float,
                         longitude: Float,
                         title: String,
                         address: String,
                         foursquare_id: Optional[String] = None,
                         disable_notification: Optional[Boolean] = None,
                         reply_to_message_id: Optional[Integer] = None,
                         reply_markup: Optional[Union[
                             types.InlineKeyboardMarkup,
                             types.ReplyKeyboardMarkup, Dict, String]] = None) -> types.Message:
        """
        Use this method to send information about a venue. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendvenue

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param latitude: Float - Latitude of the venue
        :param longitude: Float - Longitude of the venue
        :param title: String - Name of the venue
        :param address: String - Address of the venue
        :param foursquare_id: String (Optional) - Foursquare identifier of the venue
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        raw = super(Bot, self).send_venue(chat_id=chat_id, latitude=latitude, longitude=longitude, title=title,
                                          address=address, foursquare_id=foursquare_id,
                                          disable_notification=disable_notification,
                                          reply_to_message_id=reply_to_message_id, reply_markup=reply_markup)
        return self.prepare_object(types.Message.deserialize(await raw))

    async def send_contact(self, chat_id: Union[Integer, String],
                           phone_number: String,
                           first_name: String,
                           last_name: Optional[String] = None,
                           disable_notification: Optional[Boolean] = None,
                           reply_to_message_id: Optional[Integer] = None,
                           reply_markup: Optional[Union[
                               types.InlineKeyboardMarkup,
                               types.ReplyKeyboardMarkup, Dict, String]] = None) -> types.Message:
        """
        Use this method to send phone contacts. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendcontact

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or
            username of the target channel (in the format @channelusername)
        :param phone_number: String - Contact's phone number
        :param first_name: String - Contact's first name
        :param last_name: String (Optional) - Contact's last name
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional)
            - Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        raw = super(Bot, self).send_contact(chat_id=chat_id, phone_number=phone_number, first_name=first_name,
                                            last_name=last_name, disable_notification=disable_notification,
                                            reply_to_message_id=reply_to_message_id, reply_markup=reply_markup)
        return self.prepare_object(types.Message.deserialize(await raw))

    async def get_user_profile_photos(self, user_id: Integer,
                                      offset: Optional[Integer] = None,
                                      limit: Optional[Integer] = None) -> types.UserProfilePhotos:
        """
        Use this method to get a list of profile pictures for a user. Returns a UserProfilePhotos object.

        Source: https://core.telegram.org/bots/api#getuserprofilephotos

        :param user_id: Integer - Unique identifier of the target user
        :param offset: Integer (Optional) - Sequential number of the first photo to be returned.
            By default, all photos are returned.
        :param limit: Integer (Optional) - Limits the number of photos to be retrieved.
            Values between 1—100 are accepted. Defaults to 100.
        :return: Returns a UserProfilePhotos object.
        """
        raw = super(Bot, self).get_user_profile_photos(user_id=user_id, offset=offset, limit=limit)
        return self.prepare_object(types.UserProfilePhotos.deserialize(await raw))

    async def get_file(self, file_id: String) -> types.File:
        """
        Use this method to get basic info about a file and prepare it for downloading.
            For the moment, bots can download files of up to 20MB in size. On success, a File object is returned.
            The file can then be downloaded via the link https://api.telegram.org/file/bot<token>/<file_path>,
            where <file_path> is taken from the response. It is guaranteed that the link
            will be valid for at least 1 hour. When the link expires,
            a new one can be requested by calling getFile again.

        Note: This function may not preserve the original file name and MIME type.
            You should save the file's MIME type and name (if available) when the File object is received.

        Source: https://core.telegram.org/bots/api#getfile

        :param file_id: String - File identifier to get info about
        :return: On success, a File object is returned.
        """
        raw = super(Bot, self).get_file(file_id=file_id)
        return self.prepare_object(types.File.deserialize(await raw))

    async def get_chat(self, chat_id: Union[Integer, String]) -> types.Chat:
        """
        Use this method to get up to date information about the chat
            (current name of the user for one-on-one conversations, current username of a user, group or channel, etc.).
            Returns a Chat object on success.

        Source: https://core.telegram.org/bots/api#getchat

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username of the
            target supergroup or channel (in the format @channelusername)
        :return: Returns a Chat object on success.
        """
        raw = super(Bot, self).get_chat(chat_id=chat_id)
        return self.prepare_object(types.Chat.deserialize(await raw))

    async def get_chat_administrators(self, chat_id: Union[Integer, String]) -> List[types.ChatMember]:
        """
        Use this method to get a list of administrators in a chat. On success, returns an Array of ChatMember
            objects that contains information about all chat administrators except other bots.
            If the chat is a group or a supergroup and no administrators were appointed,
            only the creator will be returned.

        Source: https://core.telegram.org/bots/api#getchatadministrators

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username of
            the target supergroup or channel (in the format @channelusername)
        :return: On success, returns an Array of ChatMember objects that contains information about all
            chat administrators except other bots.
        """
        raw = super(Bot, self).get_chat_administrators(chat_id=chat_id)
        return [self.prepare_object(types.ChatMember.de_json(raw_chat_member)) for raw_chat_member in await raw]

    async def get_chat_member(self, chat_id: Union[Integer, String], user_id: Integer) -> types.ChatMember:
        """
        Use this method to get information about a member of a chat. Returns a ChatMember object on success.

        Source: https://core.telegram.org/bots/api#getchatmember

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target supergroup or channel (in the format @channelusername)
        :param user_id: Integer - Unique identifier of the target user
        :return: Returns a ChatMember object on success.
        """
        raw = super(Bot, self).get_chat_member(chat_id=chat_id, user_id=user_id)
        return self.prepare_object(types.ChatMember.deserialize(await raw))

    # === Stickers ===
    # https://core.telegram.org/bots/api#stickers

    async def send_sticker(self, chat_id: Union[Integer, String],
                           sticker: Union[io.BytesIO, io.FileIO, String],
                           disable_notification: Optional[Boolean] = None,
                           reply_to_message_id: Optional[Integer] = None,
                           reply_markup: Optional[
                               Union[types.InlineKeyboardMarkup,
                                     types.ReplyKeyboardMarkup, Dict, String]] = None) -> types.Message:
        """
        Use this method to send .webp stickers. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendsticker

        :param chat_id: Union[Integer, String] - Unique identifier for the target chat or username
            of the target channel (in the format @channelusername)
        :param sticker: Union[io.BytesIO, io.FileIO, String] - Sticker to send. Pass a file_id
            as String to send a file that exists on the Telegram servers (recommended),
            pass an HTTP URL as a String for Telegram to get a .webp file from the Internet,
            or upload a new one using multipart/form-data. More info on Sending Files »
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: Union[types.InlineKeyboardMarkup, types.ReplyKeyboardMarkup, Dict, String] (Optional) -
            Additional interface options. A JSON-serialized object for an inline keyboard,
            custom reply keyboard, instructions to remove reply keyboard or to force a reply from the user.
        :return: On success, the sent Message is returned.
        """
        raw = super(Bot, self).send_sticker(chat_id=chat_id, sticker=sticker, disable_notification=disable_notification,
                                            reply_to_message_id=reply_to_message_id, reply_markup=reply_markup)
        return self.prepare_object(types.Message.deserialize(await raw))

    async def get_sticker_set(self, name: String) -> types.StickerSet:
        """
        Use this method to get a sticker set. On success, a StickerSet object is returned.

        Source: https://core.telegram.org/bots/api#getstickerset

        :param name: String - Name of the sticker set
        :return: On success, a StickerSet object is returned.
        """
        raw = super(Bot, self).get_sticker_set(name=name)
        return self.prepare_object(types.StickerSet.deserialize(await raw))

    async def upload_sticker_file(self, user_id: Integer, png_sticker: io.BytesIO) -> types.File:
        """
        Use this method to upload a .png file with a sticker for later use in createNewStickerSet and addStickerToSet
            methods (can be used multiple times). Returns the uploaded File on success.

        Source: https://core.telegram.org/bots/api#uploadstickerfile

        :param user_id: Integer - User identifier of sticker file owner
        :param png_sticker: io.BytesIO - Png image with the sticker, must be up to 512 kilobytes in size,
            dimensions must not exceed 512px, and either width or height must be exactly 512px.
        :return: Returns the uploaded File on success.
        """
        raw = super(Bot, self).upload_sticker_file(user_id=user_id, png_sticker=png_sticker)
        return self.prepare_object(types.File.deserialize(await raw))

    # === Payments ===
    # https://core.telegram.org/bots/api#payments

    async def send_invoice(self, chat_id: Integer,
                           title: String,
                           description: String,
                           payload: String,
                           provider_token: String,
                           start_parameter: String,
                           currency: String,
                           prices: [types.LabeledPrice],
                           photo_url: Optional[String] = None,
                           photo_size: Optional[Integer] = None,
                           photo_width: Optional[Integer] = None,
                           photo_height: Optional[Integer] = None,
                           need_name: Optional[Boolean] = None,
                           need_phone_number: Optional[Boolean] = None,
                           need_email: Optional[Boolean] = None,
                           need_shipping_address: Optional[Boolean] = None,
                           is_flexible: Optional[Boolean] = None,
                           disable_notification: Optional[Boolean] = None,
                           reply_to_message_id: Optional[Integer] = None,
                           reply_markup: Optional[types.InlineKeyboardMarkup] = None) -> types.Message:
        """
        Use this method to send invoices. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendinvoice

        :param chat_id: Integer - Unique identifier for the target private chat
        :param title: String - Product name, 1-32 characters
        :param description: String - Product description, 1-255 characters
        :param payload: String - Bot-defined invoice payload, 1-128 bytes.
            This will not be displayed to the user, use for your internal processes.
        :param provider_token: String - Payments provider token, obtained via Botfather
        :param start_parameter: String - Unique deep-linking parameter that can be used to
            generate this invoice when used as a start parameter
        :param currency: String - Three-letter ISO 4217 currency code, see more on currencies
        :param prices: [types.LabeledPrice] - Price breakdown, a list of components
            (e.g. product price, tax, discount, delivery cost, delivery tax, bonus, etc.)
        :param photo_url: String (Optional) - URL of the product photo for the invoice.
            Can be a photo of the goods or a marketing image for a service.
            People like it better when they see what they are paying for.
        :param photo_size: Integer (Optional) - Photo size
        :param photo_width: Integer (Optional) - Photo width
        :param photo_height: Integer (Optional) - Photo height
        :param need_name: Boolean (Optional) - Pass True, if you require the user's full name to complete the order
        :param need_phone_number: Boolean (Optional) - Pass True, if you require
            the user's phone number to complete the order
        :param need_email: Boolean (Optional) - Pass True, if you require the user's email to complete the order
        :param need_shipping_address: Boolean (Optional) - Pass True, if you require the user's
            shipping address to complete the order
        :param is_flexible: Boolean (Optional) - Pass True, if the final price depends on the shipping method
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: types.InlineKeyboardMarkup (Optional) - A JSON-serialized object for an inline keyboard.
            If empty, one 'Pay total price' button will be shown. If not empty, the first button must be a Pay button.
        :return: On success, the sent Message is returned.
        """
        raw = super(Bot, self).send_invoice(chat_id=chat_id, title=title, description=description, payload=payload,
                                            provider_token=provider_token, start_parameter=start_parameter,
                                            currency=currency, prices=prices, photo_url=photo_url,
                                            photo_size=photo_size, photo_width=photo_width, photo_height=photo_height,
                                            need_name=need_name, need_phone_number=need_phone_number,
                                            need_email=need_email, need_shipping_address=need_shipping_address,
                                            is_flexible=is_flexible, disable_notification=disable_notification,
                                            reply_to_message_id=reply_to_message_id, reply_markup=reply_markup)
        return self.prepare_object(types.Message.deserialize(await raw))

    # === Games ===
    # https://core.telegram.org/bots/api#games

    async def send_game(self, chat_id: Integer,
                        game_short_name: String,
                        disable_notification: Optional[Boolean] = None,
                        reply_to_message_id: Optional[Integer] = None,
                        reply_markup: Optional[types.InlineKeyboardMarkup] = None) -> types.Message:
        """
        Use this method to send a game. On success, the sent Message is returned.

        Source: https://core.telegram.org/bots/api#sendgame

        :param chat_id: Integer - Unique identifier for the target chat
        :param game_short_name: String - Short name of the game, serves as the unique identifier for the game.
            Set up your games via Botfather.
        :param disable_notification: Boolean (Optional) - Sends the message silently.
            Users will receive a notification with no sound.
        :param reply_to_message_id: Integer (Optional) - If the message is a reply, ID of the original message
        :param reply_markup: types.InlineKeyboardMarkup (Optional) - A JSON-serialized object for an inline keyboard.
            If empty, one ‘Play game_title’ button will be shown. If not empty, the first button must launch the game.
        :return: On success, the sent Message is returned.
        """
        raw = super(Bot, self).send_game(chat_id=chat_id, game_short_name=game_short_name,
                                         disable_notification=disable_notification,
                                         reply_to_message_id=reply_to_message_id, reply_markup=reply_markup)
        return self.prepare_object(types.Message.deserialize(await raw))

    async def set_game_score(self, user_id: Integer,
                             score: Integer,
                             force: Optional[Boolean] = None,
                             disable_edit_message: Optional[Boolean] = None,
                             chat_id: Optional[Integer] = None,
                             message_id: Optional[Integer] = None,
                             inline_message_id: Optional[String] = None) -> Union[types.Message, Boolean]:
        """
        Use this method to set the score of the specified user in a game. On success,
            if the message was sent by the bot, returns the edited Message, otherwise returns True.
            Returns an error, if the new score is not greater than the user's current
            score in the chat and force is False.

        Source: https://core.telegram.org/bots/api#setgamescore

        :param user_id: Integer - User identifier
        :param score: Integer - New score, must be non-negative
        :param force: Boolean (Optional) - Pass True, if the high score is allowed to decrease.
            This can be useful when fixing mistakes or banning cheaters
        :param disable_edit_message: Boolean (Optional) - Pass True, if the game message should not be
            automatically edited to include the current scoreboard
        :param chat_id: Integer (Optional) - Required if inline_message_id is not specified.
            Unique identifier for the target chat
        :param message_id: Integer (Optional) - Required if inline_message_id is not specified.
            Identifier of the sent message
        :param inline_message_id: String (Optional) - Required if chat_id and message_id are not specified.
            Identifier of the inline message
        :return: On success, if the message was sent by the bot, returns the edited Message, otherwise returns True.
        """
        raw = await super(Bot, self).set_game_score(user_id=user_id, score=score, force=force,
                                                    disable_edit_message=disable_edit_message, chat_id=chat_id,
                                                    message_id=message_id, inline_message_id=inline_message_id)
        if isinstance(raw, bool):
            return raw
        return self.prepare_object(types.Message.deserialize(raw))
