import factory

from aiogram.api.types.chat_member import ChatMemberStatus, ChatMember
from tests.factories.user import UserFactory


class ChatMemberFactory(factory.Factory):
    class Meta: 
        model = ChatMember
        
    user = factory.SubFactory(UserFactory)

    status = ChatMemberStatus.ADMINISTRATOR
