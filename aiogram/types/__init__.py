import json


class Serializable:
    def to_json(self):
        """
        Returns a JSON string representation of this class.

        This function must be overridden by subclasses.
        :return: a JSON formatted string.
        """
        raise NotImplementedError


class Deserializable:
    """
    Subclasses of this class are guaranteed to be able to be created from a json-style dict or json formatted string.
    All subclasses of this class must override de_json.
    """

    @property
    def bot(self):
        if not hasattr(self, '_bot'):
            raise AttributeError('object is not configured for bot.')
        return getattr(self, '_bot')

    @bot.setter
    def bot(self, bot):
        setattr(self, '_bot', bot)

    def to_json(self):
        return getattr(self, 'data', {})

    @classmethod
    def de_json(cls, data):
        """
        Returns an instance of this class from the given json dict or string.

        This function must be overridden by subclasses.
        :return: an instance of this class created from the given json dict or string.
        """
        raise NotImplementedError

    @staticmethod
    def check_json(data):
        """
        Checks whether json_type is a dict or a string. If it is already a dict, it is returned as-is.
        If it is not, it is converted to a dict by means of json.loads(json_type)
        :param data:
        :return:
        """

        if isinstance(data, dict):
            return data
        elif isinstance(data, str):
            return json.loads(data)
        else:
            raise ValueError("data should be a json dict or string.")

    def __str__(self):
        return json.dumps(self.to_json())
