"""
- TelegramAPIError
    - ValidationError
    - Throttled
    - BadRequest
        - MessageError
            - MessageNotModified
            - MessageToForwardNotFound
            - MessageIdInvalid
            - MessageToDeleteNotFound
            - MessageToPinNotFound
            - MessageIdentifierNotSpecified
            - MessageTextIsEmpty
            - MessageCantBeEdited
            - MessageCantBeDeleted
            - MessageCantBeForwarded
            - MessageToEditNotFound
            - MessageToReplyNotFound
            - ToMuchMessages
        - PollError
            - PollCantBeStopped
            - PollHasAlreadyClosed
            - PollsCantBeSentToPrivateChats
            - PollSizeError
                - PollMustHaveMoreOptions
                - PollCantHaveMoreOptions
                - PollsOptionsLengthTooLong
                - PollOptionsMustBeNonEmpty
                - PollQuestionMustBeNonEmpty
            - MessageWithPollNotFound (with MessageError)
            - MessageIsNotAPoll (with MessageError)
        - ObjectExpectedAsReplyMarkup
        - InlineKeyboardExpected
        - ChatNotFound
        - ChatDescriptionIsNotModified
        - InvalidQueryID
        - InvalidPeerID
        - InvalidHTTPUrlContent
        - ButtonURLInvalid
        - URLHostIsEmpty
        - StartParamInvalid
        - ButtonDataInvalid
        - FileIsTooBig
        - WrongFileIdentifier
        - GroupDeactivated
        - BadWebhook
            - WebhookRequireHTTPS
            - BadWebhookPort
            - BadWebhookAddrInfo
            - BadWebhookNoAddressAssociatedWithHostname
        - NotFound
            - MethodNotKnown
        - PhotoAsInputFileRequired
        - InvalidStickersSet
        - NoStickerInRequest
        - ChatAdminRequired
        - NeedAdministratorRightsInTheChannel
        - MethodNotAvailableInPrivateChats
        - CantDemoteChatCreator
        - CantRestrictSelf
        - NotEnoughRightsToRestrict
        - PhotoDimensions
        - UnavailableMembers
        - TypeOfFileMismatch
        - WrongRemoteFileIdSpecified
        - PaymentProviderInvalid
        - CurrencyTotalAmountInvalid
        - CantParseUrl
        - UnsupportedUrlProtocol
        - CantParseEntities
        - ResultIdDuplicate
        - MethodIsNotAvailable
    - ConflictError
        - TerminatedByOtherGetUpdates
        - CantGetUpdates
    - Unauthorized
        - BotKicked
        - BotBlocked
        - UserDeactivated
        - CantInitiateConversation
        - CantTalkWithBots
    - NetworkError
    - RetryAfter
    - MigrateToChat
    - RestartingTelegram

- AIOGramWarning
    - TimeoutWarning
"""
import time

# TODO: Use exceptions detector from `aiograph`.
# TODO: aiogram.utils.exceptions.BadRequest: Bad request: can't parse entities: unsupported start tag "function" at byte offset 0
# TODO: aiogram.utils.exceptions.TelegramAPIError: Gateway Timeout

_PREFIXES = ['error: ', '[error]: ', 'bad request: ', 'conflict: ', 'not found: ']


def _clean_message(text):
    for prefix in _PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix):]
    return (text[0].upper() + text[1:]).strip()


class TelegramAPIError(Exception):
    def __init__(self, message=None):
        super(TelegramAPIError, self).__init__(_clean_message(message))


class _MatchErrorMixin:
    match = ''
    text = None

    __subclasses = []

    def __init_subclass__(cls, **kwargs):
        super(_MatchErrorMixin, cls).__init_subclass__(**kwargs)
        # cls.match = cls.match.lower() if cls.match else ''
        if not hasattr(cls, f"_{cls.__name__}__group"):
            cls.__subclasses.append(cls)

    @classmethod
    def check(cls, message) -> bool:
        """
        Compare pattern with message

        :param message: always must be in lowercase
        :return: bool
        """
        return cls.match.lower() in message

    @classmethod
    def detect(cls, description):
        description = description.lower()
        for err in cls.__subclasses:
            if err is cls:
                continue
            if err.check(description):
                raise err(cls.text or description)
        raise cls(description)


class AIOGramWarning(Warning):
    pass


class TimeoutWarning(AIOGramWarning):
    pass


class FSMStorageWarning(AIOGramWarning):
    pass


class ValidationError(TelegramAPIError):
    pass


class BadRequest(TelegramAPIError, _MatchErrorMixin):
    __group = True


class MessageError(BadRequest):
    __group = True


class MessageNotModified(MessageError):
    """
    Will be raised when you try to set new text is equals to current text.
    """
    match = 'message is not modified'


class MessageToForwardNotFound(MessageError):
    """
    Will be raised when you try to forward very old or deleted or unknown message.
    """
    match = 'message to forward not found'


class MessageIdInvalid(MessageError):
    text = 'Invalid message id'
    match = 'message_id_invalid'


class MessageToDeleteNotFound(MessageError):
    """
    Will be raised when you try to delete very old or deleted or unknown message.
    """
    match = 'message to delete not found'


class MessageToPinNotFound(MessageError):
    """
    Will be raised when you try to pin deleted or unknown message.
    """
    match = 'message to pin not found'


class MessageToReplyNotFound(MessageError):
    """
    Will be raised when you try to reply to very old or deleted or unknown message.
    """
    match = 'Reply message not found'


class MessageIdentifierNotSpecified(MessageError):
    match = 'message identifier is not specified'


class MessageTextIsEmpty(MessageError):
    match = 'Message text is empty'


class MessageCantBeEdited(MessageError):
    match = 'message can\'t be edited'


class MessageCantBeDeleted(MessageError):
    match = 'message can\'t be deleted'


class MessageCantBeForwarded(MessageError):
    match = 'message can\'t be forwarded'


class MessageToEditNotFound(MessageError):
    match = 'message to edit not found'


class MessageIsTooLong(MessageError):
    match = 'message is too long'


class ToMuchMessages(MessageError):
    """
    Will be raised when you try to send media group with more than 10 items.
    """
    match = 'Too much messages to send as an album'


class ObjectExpectedAsReplyMarkup(BadRequest):
    match = 'object expected as reply markup'


class InlineKeyboardExpected(BadRequest):
    match = 'inline keyboard expected'


class PollError(BadRequest):
    __group = True


class PollCantBeStopped(PollError):
    match = "poll can't be stopped"


class PollHasAlreadyBeenClosed(PollError):
    match = 'poll has already been closed'


class PollsCantBeSentToPrivateChats(PollError):
    match = "polls can't be sent to private chats"


class PollSizeError(PollError):
    __group = True


class PollMustHaveMoreOptions(PollSizeError):
    match = "poll must have at least 2 option"


class PollCantHaveMoreOptions(PollSizeError):
    match = "poll can't have more than 10 options"


class PollOptionsMustBeNonEmpty(PollSizeError):
    match = "poll options must be non-empty"


class PollQuestionMustBeNonEmpty(PollSizeError):
    match = "poll question must be non-empty"


class PollOptionsLengthTooLong(PollSizeError):
    match = "poll options length must not exceed 100"


class PollQuestionLengthTooLong(PollSizeError):
    match = "poll question length must not exceed 255"


class PollCanBeRequestedInPrivateChatsOnly(PollError):
    match = "Poll can be requested in private chats only"


class MessageWithPollNotFound(PollError, MessageError):
    """
    Will be raised when you try to stop poll with message without poll
    """
    match = 'message with poll to stop not found'


class MessageIsNotAPoll(PollError, MessageError):
    """
    Will be raised when you try to stop poll with message without poll
    """
    match = 'message is not a poll'


class ChatNotFound(BadRequest):
    match = 'chat not found'


class ChatIdIsEmpty(BadRequest):
    match = 'chat_id is empty'


class InvalidUserId(BadRequest):
    match = 'user_id_invalid'
    text = 'Invalid user id'


class ChatDescriptionIsNotModified(BadRequest):
    match = 'chat description is not modified'


class InvalidQueryID(BadRequest):
    match = 'query is too old and response timeout expired or query id is invalid'


class InvalidPeerID(BadRequest):
    match = 'PEER_ID_INVALID'
    text = 'Invalid peer ID'


class InvalidHTTPUrlContent(BadRequest):
    match = 'Failed to get HTTP URL content'


class ButtonURLInvalid(BadRequest):
    match = 'BUTTON_URL_INVALID'
    text = 'Button URL invalid'


class URLHostIsEmpty(BadRequest):
    match = 'URL host is empty'


class StartParamInvalid(BadRequest):
    match = 'START_PARAM_INVALID'
    text = 'Start param invalid'


class ButtonDataInvalid(BadRequest):
    match = 'BUTTON_DATA_INVALID'
    text = 'Button data invalid'


class FileIsTooBig(BadRequest):
    match = 'File is too big'


class WrongFileIdentifier(BadRequest):
    match = 'wrong file identifier/HTTP URL specified'


class GroupDeactivated(BadRequest):
    match = 'Group chat was deactivated'


class PhotoAsInputFileRequired(BadRequest):
    """
    Will be raised when you try to set chat photo from file ID.
    """
    match = 'Photo should be uploaded as an InputFile'


class InvalidStickersSet(BadRequest):
    match = 'STICKERSET_INVALID'
    text = 'Stickers set is invalid'


class NoStickerInRequest(BadRequest):
    match = 'there is no sticker in the request'


class ChatAdminRequired(BadRequest):
    match = 'CHAT_ADMIN_REQUIRED'
    text = 'Admin permissions is required!'


class NeedAdministratorRightsInTheChannel(BadRequest):
    match = 'need administrator rights in the channel chat'
    text = 'Admin permissions is required!'


class NotEnoughRightsToPinMessage(BadRequest):
    match = 'not enough rights to pin a message'


class MethodNotAvailableInPrivateChats(BadRequest):
    match = 'method is available only for supergroups and channel'


class CantDemoteChatCreator(BadRequest):
    match = 'can\'t demote chat creator'


class CantRestrictSelf(BadRequest):
    match = "can't restrict self"
    text = "Admin can't restrict self."


class NotEnoughRightsToRestrict(BadRequest):
    match = 'not enough rights to restrict/unrestrict chat member'


class PhotoDimensions(BadRequest):
    match = 'PHOTO_INVALID_DIMENSIONS'
    text = 'Invalid photo dimensions'


class UnavailableMembers(BadRequest):
    match = 'supergroup members are unavailable'


class TypeOfFileMismatch(BadRequest):
    match = 'type of file mismatch'


class WrongRemoteFileIdSpecified(BadRequest):
    match = 'wrong remote file id specified'


class PaymentProviderInvalid(BadRequest):
    match = 'PAYMENT_PROVIDER_INVALID'
    text = 'payment provider invalid'


class CurrencyTotalAmountInvalid(BadRequest):
    match = 'currency_total_amount_invalid'
    text = 'currency total amount invalid'


class BadWebhook(BadRequest):
    __group = True


class WebhookRequireHTTPS(BadWebhook):
    match = 'HTTPS url must be provided for webhook'
    text = 'bad webhook: ' + match


class BadWebhookPort(BadWebhook):
    match = 'Webhook can be set up only on ports 80, 88, 443 or 8443'
    text = 'bad webhook: ' + match


class BadWebhookAddrInfo(BadWebhook):
    match = 'getaddrinfo: Temporary failure in name resolution'
    text = 'bad webhook: ' + match


class BadWebhookNoAddressAssociatedWithHostname(BadWebhook):
    match = 'failed to resolve host: no address associated with hostname'


class CantParseUrl(BadRequest):
    match = 'can\'t parse URL'


class UnsupportedUrlProtocol(BadRequest):
    match = 'unsupported URL protocol'


class CantParseEntities(BadRequest):
    match = 'can\'t parse entities'


class ResultIdDuplicate(BadRequest):
    match = 'result_id_duplicate'
    text = 'Result ID duplicate'


class BotDomainInvalid(BadRequest):
    match = 'bot_domain_invalid'
    text = 'Invalid bot domain'


class MethodIsNotAvailable(BadRequest):
    match = "Method is available only for supergroups"


class CantRestrictChatOwner(BadRequest):
    """
    Raises when bot restricts the chat owner
    """
    match = 'Can\'t remove chat owner'


class UserIsAnAdministratorOfTheChat(BadRequest):
    """
    Raises when bot restricts the chat admin
    """
    match = 'User is an administrator of the chat'


class NotFound(TelegramAPIError, _MatchErrorMixin):
    __group = True


class MethodNotKnown(NotFound):
    match = 'method not found'


class ConflictError(TelegramAPIError, _MatchErrorMixin):
    __group = True


class TerminatedByOtherGetUpdates(ConflictError):
    match = 'terminated by other getUpdates request'
    text = 'Terminated by other getUpdates request; ' \
           'Make sure that only one bot instance is running'


class CantGetUpdates(ConflictError):
    match = 'can\'t use getUpdates method while webhook is active'


class Unauthorized(TelegramAPIError, _MatchErrorMixin):
    __group = True


class BotKicked(Unauthorized):
    match = 'bot was kicked from'


class BotBlocked(Unauthorized):
    match = 'bot was blocked by the user'


class UserDeactivated(Unauthorized):
    match = 'user is deactivated'


class CantInitiateConversation(Unauthorized):
    match = 'bot can\'t initiate conversation with a user'


class CantTalkWithBots(Unauthorized):
    match = 'bot can\'t send messages to bots'


class NetworkError(TelegramAPIError):
    pass


class RestartingTelegram(TelegramAPIError):
    def __init__(self):
        super(RestartingTelegram, self).__init__('The Telegram Bot API service is restarting. Wait few second.')


class RetryAfter(TelegramAPIError):
    def __init__(self, retry_after):
        super(RetryAfter, self).__init__(f"Flood control exceeded. Retry in {retry_after} seconds.")
        self.timeout = retry_after


class MigrateToChat(TelegramAPIError):
    def __init__(self, chat_id):
        super(MigrateToChat, self).__init__(f"The group has been migrated to a supergroup. New id: {chat_id}.")
        self.migrate_to_chat_id = chat_id


class Throttled(TelegramAPIError):
    def __init__(self, **kwargs):
        from ..dispatcher.storage import DELTA, EXCEEDED_COUNT, KEY, LAST_CALL, RATE_LIMIT, RESULT
        self.key = kwargs.pop(KEY, '<None>')
        self.called_at = kwargs.pop(LAST_CALL, time.time())
        self.rate = kwargs.pop(RATE_LIMIT, None)
        self.result = kwargs.pop(RESULT, False)
        self.exceeded_count = kwargs.pop(EXCEEDED_COUNT, 0)
        self.delta = kwargs.pop(DELTA, 0)
        self.user = kwargs.pop('user', None)
        self.chat = kwargs.pop('chat', None)

    def __str__(self):
        return f"Rate limit exceeded! (Limit: {self.rate} s, " \
            f"exceeded: {self.exceeded_count}, " \
            f"time delta: {round(self.delta, 3)} s)"
