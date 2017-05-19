from aiogram.types import Deserializable


class Chat(Deserializable):
    __slots__ = ('id', 'type', 'title', 'username', 'first_name', 'last_name', 'all_members_are_administrators')

    def __init__(self, data, id, type, title, username, first_name, last_name, all_members_are_administrators):
        self.data = data

        self.id: int = id
        self.type: str = type
        self.title: str = title
        self.username: str = username
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.all_members_are_administrators: bool = all_members_are_administrators

    @classmethod
    def de_json(cls, data) -> 'Chat':
        """
        id	Integer	Unique identifier for this chat. This number may be greater than 32 bits and some programming languages may have difficulty/silent defects in interpreting it. But it is smaller than 52 bits, so a signed 64 bit integer or double-precision float type are safe for storing this identifier.
        type	String	Type of chat, can be either “private”, “group”, “supergroup” or “channel”
        title	String	Optional. Title, for supergroups, channels and group chats
        username	String	Optional. Username, for private chats, supergroups and channels if available
        first_name	String	Optional. First name of the other party in a private chat
        last_name	String	Optional. Last name of the other party in a private chat
        all_members_are_administrators	Boolean	Optional. True if a group has ‘All Members Are Admins’ enabled.
        :param data: 
        :return: 
        """
        data = cls.check_json(data)

        id: int = data.get('id')
        type: str = data.get('type')
        title: str = data.get('title')
        username: str = data.get('username')
        first_name: str = data.get('first_name')
        last_name: str = data.get('last_name')
        all_members_are_administrators: bool = data.get('all_members_are_administrators', False)

        return Chat(data, id, type, title, username, first_name, last_name, all_members_are_administrators)

    async def send_message(self, text):
        self.bot.send_message(self.id, text)


class ChatType:
    PRIVATE = 'private'
    GROUP = 'group'
    SUPER_GROUP = 'supergroup'
    CHANNEL = 'channel'
