from math import ceil
import typing
import uuid

from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.types.page_selection_location import PageSelectionLocation

MAX_MESSAGE_LENGTH = 4096
PAGE_DEFAULT = 0
LIMIT_DEFAULT = 10


def split_text(text: str, length: int = MAX_MESSAGE_LENGTH) -> typing.List[str]:
    """
    Split long text

    :param text:
    :param length:
    :return: list of parts
    :rtype: :obj:`typing.List[str]`
    """
    return [text[i:i + length] for i in range(0, len(text), length)]


def safe_split_text(text: str, length: int = MAX_MESSAGE_LENGTH) -> typing.List[str]:
    """
    Split long text

    :param text:
    :param length:
    :return:
    """
    # TODO: More informative description

    temp_text = text
    parts = []
    while temp_text:
        if len(temp_text) > length:
            try:
                split_pos = temp_text[:length].rindex(' ')
            except ValueError:
                split_pos = length
            if split_pos < length // 4 * 3:
                split_pos = length
            parts.append(temp_text[:split_pos])
            temp_text = temp_text[split_pos:].lstrip()
        else:
            parts.append(temp_text)
            break
    return parts


def index_of_first_element_on_page(page: int = PAGE_DEFAULT, limit: int = LIMIT_DEFAULT) -> int:
    """
    Index of first element on page

    :param page: int number of page (default: 0)
    :param limit: int items per page (default: 10)
    :return: int index of first element on page
    """
    return page * limit


def index_of_last_element_on_page(page: int = PAGE_DEFAULT, limit: int = LIMIT_DEFAULT) -> int:
    """
    Index of last element on page

    :param page: int number of page (default: 0)
    :param limit: int items per page (default: 10)
    :return: int index of last element on page
    """
    return index_of_first_element_on_page(page=page, limit=limit) + limit


def paginate(data: typing.Iterable, page: int = PAGE_DEFAULT, limit: int = LIMIT_DEFAULT) -> typing.Iterable:
    """
    Slice data over pages

    :param data: any iterable object
    :type data: :obj:`typing.Iterable`
    :param page: number of page
    :type page: :obj:`int`
    :param limit: items per page
    :type limit: :obj:`int`
    :return: sliced object
    :rtype: :obj:`typing.Iterable`
    """
    return data[index_of_first_element_on_page(page=page, limit=limit):
                index_of_last_element_on_page(page=page, limit=limit)]


class InlineButtonsPaginator:
    BUTTONS_TEXT_CORO = typing.Optional[typing.Callable[[int, int], typing.Awaitable[typing.List[str]]]]
    INLINE_KEYBOARD_BUTTON_GENERATOR = typing.AsyncGenerator[InlineKeyboardButton, None]

    def __init__(self, bot: Bot, dispatcher: Dispatcher, chat_id: int,
                 text: typing.Union[str, typing.Callable[[int], str]],
                 buttons: typing.Callable[[int], typing.AsyncGenerator[InlineKeyboardButton, None]],
                 first_page_button_text: str = '⏮', last_page_button_text: str = '⏭',
                 previous_page_button_text: str = '◀️', next_page_button_text: str = '▶️',
                 page_selection_location: PageSelectionLocation = PageSelectionLocation.BOTTOM,
                 send_message_args: typing.Tuple = (),
                 send_message_kwargs: typing.Optional[typing.Mapping[str, typing.Any]] = None,
                 edit_message_args: typing.Tuple = (),
                 edit_message_kwargs: typing.Optional[typing.Mapping[str, typing.Any]] = None):
        """
        Construct InlineButtonsPaginator

        :param bot: Bot bot object
        :param dispatcher: Dispatcher dispatcher object
        :param chat_id: int chat id
        :param text: Union[str, Callable[[int], str]] text of messages or function, that accepts page index and \
        returns text of messages
        :param buttons: Callable[[int], AsyncGenerator[InlineKeyboardButton, None]] coroutine, that accepts index \
        of page and asynchronously yields inline buttons
        :param first_page_button_text: str first page button text (default: '⏮')
        :param last_page_button_text: str last page button text (default: '⏭')
        :param previous_page_button_text: str previous page button text (default: '◀')
        :param next_page_button_text: str next page button text (default: '▶️')
        :param page_selection_location: PageSelectionLocation (default: PageSelectionLocation.BOTTOM)
        :param send_message_args: Tuple positional arguments to send_message (default: ())
        :param send_message_kwargs: Mapping keyword arguments to send_message (default: None)
        :param edit_message_args: Tuple positional arguments to edit_message (default: ())
        :param edit_message_kwargs: Mapping keyword arguments to edit_message (default: None)
        """
        self.bot = bot
        self.dispatcher = dispatcher
        self.chat_id = chat_id
        self.text = text
        self.buttons = buttons
        self.first_page_button_text = first_page_button_text
        self.last_page_button_text = last_page_button_text
        self.previous_page_button_text = previous_page_button_text
        self.next_page_button_text = next_page_button_text
        self.page_selection_location = page_selection_location
        self.send_message_args = send_message_args
        self.send_message_kwargs = send_message_kwargs or {}
        self.edit_message_args = edit_message_args
        self.edit_message_kwargs = edit_message_kwargs or {}
        self._page_count_uuid = str(uuid.uuid4())
        self._page_selection_callback_data_uuid = str(uuid.uuid4())
        self.dispatcher.register_callback_query_handler(callback=self._page_selection_button_callback,
                                                        func=self._callback_query_func,
                                                        state='*')

    def _callback_query_func(self, callback_query: CallbackQuery) -> bool:
        return callback_query.data.startswith(self._page_selection_callback_data_uuid)

    async def _page_selection_button_callback(self, callback_query: CallbackQuery) -> None:
        page = int(callback_query.data.replace(self._page_selection_callback_data_uuid, ''))
        await self.send_buttons_message(page=page)

    @staticmethod
    async def buttons_helper(page: int, limit: int,
                             callback_data_func: typing.Callable[[typing.Optional[int], typing.Optional[str]], str],
                             callback_data_prefix: str, buttons_texts: typing.Optional[typing.Collection[str]] = None,
                             buttons_texts_coro: BUTTONS_TEXT_CORO = None) -> INLINE_KEYBOARD_BUTTON_GENERATOR:
        """
        Buttons generator helper

        :param page: int index of page
        :param limit: int button count on page
        :param callback_data_func: Callable[[typing.Optional[int], typing.Optional[str]], str] function, that accepts \
                button index or button text and returns button callback data
        :param callback_data_prefix: str prefix of callback data
        :param buttons_texts: Optional[Collection[str]] buttons texts (default: None)
        :param buttons_texts_coro: Optional[Callable[[int, int], Awaitable[List[str]]]] buttons texts coroutine, that \
                accepts page and limit and returns list of buttons texts (default: None)
        """
        if buttons_texts is None and buttons_texts_coro is None:
            raise ValueError("You should specify either buttons_texts or buttons_texts_coro")
        elif buttons_texts is not None and buttons_texts_coro is not None:
            raise ValueError("You should specify only buttons_texts or buttons_texts_coro")
        if buttons_texts is not None:
            buttons_texts = paginate(data=buttons_texts, page=page, limit=limit)
        else:
            buttons_texts = await buttons_texts_coro(page, limit)
            if not buttons_texts:
                return
        for i, button_text in zip(range(index_of_first_element_on_page(page=page, limit=limit),
                                        index_of_last_element_on_page(page=page, limit=limit)),
                                  buttons_texts):
            callback_data = f'{callback_data_prefix}{callback_data_func(i, button_text)}'
            yield InlineKeyboardButton(text=button_text, callback_data=callback_data)

    async def send_buttons_message(self, page: int = 0,
                                   page_count: typing.Optional[int] = None) -> typing.Optional[Message]:
        """
        :param page: int page index (default: 0)
        :param page_count: Optional[int] page count (default: None)
        """
        data = await self.dispatcher.storage.get_data(chat=self.chat_id)
        if page_count is None:
            page_count = data.get(self._page_count_uuid)
            if page_count is None:
                raise ValueError("page_count was never passed as argument")
        else:
            data[self._page_count_uuid] = page_count
        text = self.text if isinstance(self.text, str) else self.text(page)
        page_selection_buttons = []
        if page > 0:
            first_page_previous_page_buttons = [
                InlineKeyboardButton(text=self.first_page_button_text,
                                     callback_data=f'{self._page_selection_callback_data_uuid}0'),
                InlineKeyboardButton(text=self.previous_page_button_text,
                                     callback_data=f'{self._page_selection_callback_data_uuid}{page - 1}')
            ]
            page_selection_buttons += first_page_previous_page_buttons
        if page < page_count - 1:
            first_page_previous_page_buttons = [
                InlineKeyboardButton(text=self.next_page_button_text,
                                     callback_data=f'{self._page_selection_callback_data_uuid}{page + 1}'),
                InlineKeyboardButton(text=self.last_page_button_text,
                                     callback_data=f'{self._page_selection_callback_data_uuid}{page_count - 1}'),
            ]
            page_selection_buttons += first_page_previous_page_buttons
        keyboard = InlineKeyboardMarkup()
        if self.page_selection_location in [PageSelectionLocation.TOP, PageSelectionLocation.TOP_AND_BOTTOM]:
            keyboard.row(*page_selection_buttons)
        async for button in self.buttons(page):
            keyboard.add(button)
        if self.page_selection_location in [PageSelectionLocation.BOTTOM, PageSelectionLocation.TOP_AND_BOTTOM]:
            keyboard.row(*page_selection_buttons)
        message_id = data.get(self._page_selection_callback_data_uuid)
        if message_id is not None:
            self.edit_message_kwargs.update(chat_id=self.chat_id, text=text, reply_markup=keyboard)
            message = await self.bot.edit_message_text(message_id=message_id,
                                                       *self.edit_message_args,
                                                       **self.edit_message_kwargs)
        else:
            self.send_message_kwargs.update(chat_id=self.chat_id, text=text, reply_markup=keyboard)
            message = await self.bot.send_message(*self.send_message_args, **self.send_message_kwargs)
        data[self._page_selection_callback_data_uuid] = message.message_id
        await self.dispatcher.storage.set_data(chat=self.chat_id, data=data)
        return message
