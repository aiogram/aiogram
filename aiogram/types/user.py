try:
    import babel
except ImportError:
    babel = None

from .base import Deserializable


class User(Deserializable):
    """
    This object represents a Telegram user or bot.
    
    https://core.telegram.org/bots/api#user
    """
    def __init__(self, id, first_name, last_name, username, language_code):
        self.id: int = id
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.username: str = username
        self.language_code: str = language_code

    @classmethod
    def de_json(cls, raw_data: str or dict) -> 'User':
        raw_data = cls.check_json(raw_data)

        id = raw_data.get('id')
        first_name = raw_data.get('first_name')
        last_name = raw_data.get('last_name')
        username = raw_data.get('username')
        language_code = raw_data.get('language_code')

        return User(id, first_name, last_name, username, language_code)

    @property
    def full_name(self):
        """
        You can get full name of user.

        :return: str
        """
        full_name = self.first_name
        if self.last_name:
            full_name += ' ' + self.last_name
        return full_name

    @property
    def mention(self):
        """
        You can get menthion to user (If user have username, otherwise return full name)

        :return: str
        """
        if self.username:
            return '@' + self.username
        return self.full_name

    @property
    def locale(self) -> 'babel.core.Locale' or None:
        """
        This property require `Babel <https://pypi.python.org/pypi/Babel>`_ module

        :return: :class:`babel.core.Locale`
        :raise: ImportError: when babel is not installed.
        """
        if not babel:
            raise ImportError('Babel is not installed!')
        if not self.language_code:
            return None
        if not hasattr(self, '_locale'):
            setattr(self, '_locale', babel.core.Locale.parse(self.language_code, sep='-'))
        return getattr(self, '_locale')

    async def get_user_profile_photos(self, offset=None, limit=None):
        return await self.bot.get_user_profile_photos(self.id, offset, limit)
