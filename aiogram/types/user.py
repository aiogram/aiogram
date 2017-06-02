import babel

from .base import Deserializable


class User(Deserializable):
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
        full_name = self.first_name
        if self.last_name:
            full_name += ' ' + self.last_name
        return full_name

    @property
    def mention(self):
        if self.username:
            return '@' + self.username
        return self.full_name

    @property
    def locale(self) -> babel.core.Locale or None:
        if not self.language_code:
            return None
        if not hasattr(self, '_locale'):
            setattr(self, '_locale', babel.core.Locale.parse(self.language_code, sep='-'))
        return getattr(self, '_locale')
