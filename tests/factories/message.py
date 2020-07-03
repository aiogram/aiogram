from datetime import datetime

import factory

from aiogram.api.types import Message
from tests.factories import sequences
from tests.factories.chat import ChatFactory
from tests.factories.user import UserFactory


class MessageFactory(factory.Factory):
    class Meta:
        model = Message

    message_id = sequences.id_
    from_user = factory.SubFactory(UserFactory)
    chat = factory.SubFactory(ChatFactory)
    text = factory.Sequence(lambda n: f"Message text #{n}")

    date = factory.LazyFunction(lambda _: datetime.now().toordinal())

    def __new__(cls, *args, **kwargs) -> "MessageFactory.Meta.model":
        """
        This is a dirty hack for correct type hints
        See https://github.com/FactoryBoy/factory_boy/issues/468#issuecomment-505646794
        """
        return super().__new__(*args, **kwargs)
