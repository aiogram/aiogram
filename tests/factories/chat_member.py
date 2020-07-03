import factory

from aiogram.api.types.chat_member import ChatMember, ChatMemberStatus
from tests.factories.user import UserFactory


class ChatMemberFactory(factory.Factory):
    class Meta:
        model = ChatMember

    user = factory.SubFactory(UserFactory)

    status = ChatMemberStatus.ADMINISTRATOR

    def __new__(cls, *args, **kwargs) -> "ChatMemberFactory.Meta.model":
        """
        This is a dirty hack for correct type hints
        See https://github.com/FactoryBoy/factory_boy/issues/468#issuecomment-505646794
        """
        return super().__new__(*args, **kwargs)
