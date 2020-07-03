import factory
from datetime import datetime

from tests.factories import sequences
from tests.factories.chat import ChatFactory
from tests.factories.user import UserFactory


class MessageFactory(factory.Factory):
    message_id = sequences.id_
    from_user = factory.SubFactory(UserFactory)
    chat = factory.SubFactory(ChatFactory)
    text = factory.Sequence(lambda n: f"Message text #{n}")

    date = factory.LazyFunction(lambda _: datetime.now().toordinal())
