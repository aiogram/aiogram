import factory

from aiogram.api.types import Chat
from aiogram.api.types.chat import ChatType
from tests.factories import sequences


class ChatFactory(factory.Factory):
    class Meta:
        model = Chat

    id = None  # lazy attribute
    first_name = sequences.first_name
    last_name = sequences.last_name
    username = sequences.username
    type = ChatType.PRIVATE

    @factory.lazy_attribute_sequence
    def id(self, n):
        _id = n
        if self.type is ChatType.CHANNEL:
            _id = -_id
        return _id

    @factory.lazy_attribute_sequence
    def title(self, n):
        if self.type is ChatType.CHANNEL:
            return f"Title #{n}"

    def __new__(cls, *args, **kwargs) -> "ChatFactory.Meta.model":
        """
        This is a dirty hack for correct type hints
        See https://github.com/FactoryBoy/factory_boy/issues/468#issuecomment-505646794
        """
        return super().__new__(*args, **kwargs)
