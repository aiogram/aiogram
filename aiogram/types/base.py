import datetime
import json
import time


def deserialize(deserializable, data):
    """
    Deserialize object if have data

    :param deserializable: :class:`aiogram.types.Deserializable` 
    :param data: 
    :return: 
    """
    if data:
        return deserializable.de_json(data)


def deserialize_array(deserializable, array):
    """
    Deserialize array of objects

    :param deserializable: 
    :param array: 
    :return: 
    """
    if array:
        return [deserialize(deserializable, item) for item in array]


class Serializable:
    """
    Subclasses of this class are guaranteed to be able to be created from a json-style dict.
    """

    def to_json(self):
        """
        Returns a JSON representation of this class.

        :return: dict
        """
        return {k: v.to_json() if hasattr(v, 'to_json') else v for k, v in self.__dict__.items() if
                not k.startswith('_')}


class Deserializable:
    """
    Subclasses of this class are guaranteed to be able to be created from a json-style dict or json formatted string.
    All subclasses of this class must override de_json.
    """

    def to_json(self):
        result = {}
        for name, attr in self.__dict__.items():
            if not attr or name in ['_bot', '_parent']:
                continue
            if hasattr(attr, 'to_json'):
                attr = getattr(attr, 'to_json')()
            elif isinstance(attr, datetime.datetime):
                attr = int(time.mktime(attr.timetuple()))
            result[name] = attr
        return result

    @property
    def bot(self) -> 'Bot':
        """
        Bot instance
        """
        if not hasattr(self, '_bot'):
            raise AttributeError(f"{self.__class__.__name__} is not configured.")
        return getattr(self, '_bot')

    @bot.setter
    def bot(self, bot):
        setattr(self, '_bot', bot)
        for name, attr in self.__dict__.items():
            if hasattr(attr, 'de_json'):
                attr.bot = bot

    @property
    def parent(self):
        """
        Parent object
        """
        return getattr(self, '_parent', None)

    @parent.setter
    def parent(self, value):
        setattr(self, '_parent', value)
        for name, attr in self.__dict__.items():
            if name.startswith('_'):
                continue
            if hasattr(attr, 'de_json'):
                attr.parent = self

    @classmethod
    def de_json(cls, raw_data):
        """
        Returns an instance of this class from the given json dict or string.

        This function must be overridden by subclasses.
        :return: an instance of this class created from the given json dict or string.
        """
        raise NotImplementedError

    @staticmethod
    def check_json(raw_data) -> dict:
        """
        Checks whether json_type is a dict or a string. If it is already a dict, it is returned as-is.
        If it is not, it is converted to a dict by means of json.loads(json_type)
        :param raw_data:
        :return:
        """

        if isinstance(raw_data, dict):
            return raw_data
        elif isinstance(raw_data, str):
            return json.loads(raw_data)
        else:
            raise ValueError("data should be a json dict or string.")

    def __str__(self):
        return str(self.to_json())

    def __repr__(self):
        return str(self)

    @classmethod
    def deserialize(cls, obj):
        if isinstance(obj, list):
            return deserialize_array(cls, obj)
        return deserialize(cls, obj)
