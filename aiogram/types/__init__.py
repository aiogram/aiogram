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
    def check_json(data) -> dict:
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

    def __repr__(self):
        return str(self)
