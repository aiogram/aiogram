import abc
import datetime

__all__ = ('BaseField', 'Field', 'ListField', 'DateTimeField')


class BaseField(metaclass=abc.ABCMeta):
    """
    Base field (prop)
    """

    def __init__(self, *, base=None, default=None, alias=None):
        """
        Init prop

        :param base: class for child element
        :param default: default value
        :param alias: alias name (for e.g. field named 'from'  must be has name 'from_user'
                      ('from' is builtin Python keyword)
        """
        self.base_object = base
        self.default = default
        self.alias = alias

    def __set_name__(self, owner, name):
        if self.alias is None:
            self.alias = name

    def resolve_base(self, instance):
        if self.base_object is None or hasattr(self.base_object, 'telegram_types'):
            return
        elif isinstance(self.base_object, str):
            self.base_object = instance.telegram_types.get(self.base_object)

    def get_value(self, instance):
        """
        Get value for current object instance

        :param instance:
        :return:
        """
        return instance.values.get(self.alias)

    def set_value(self, instance, value):
        """
        Set prop value

        :param instance:
        :param value:
        :return:
        """
        self.resolve_base(instance)
        value = self.deserialize(value)
        instance.values[self.alias] = value

    def __get__(self, instance, owner):
        return self.get_value(instance)

    def __set__(self, instance, value):
        self.set_value(instance, value)

    @abc.abstractmethod
    def serialize(self, value):
        """
        Serialize value to python

        :param value:
        :return:
        """
        pass

    @abc.abstractmethod
    def deserialize(self, value):
        """Deserialize python object value to TelegramObject value"""
        pass

    def export(self, instance):
        """
        Alias for `serialize` but for current Object instance

        :param instance:
        :return:
        """
        return self.serialize(self.get_value(instance))


class Field(BaseField):
    """
    Simple field
    """

    def serialize(self, value):
        if self.base_object is not None:
            return value.to_python()
        return value

    def deserialize(self, value):
        if self.base_object is not None and not hasattr(value, 'base_object'):
            return self.base_object(**value)
        return value


class ListField(Field):
    """
    Field contains list ob objects
    """

    def serialize(self, value):
        result = []
        serialize = super(ListField, self).serialize
        for item in value:
            result.append(serialize(item))
        return result

    def deserialize(self, value):
        result = []
        deserialize = super(ListField, self).deserialize
        for item in value:
            result.append(deserialize(item))
        return result


class DateTimeField(BaseField):
    """
    In this field stored datetime

    in: unixtime
    out: datetime
    """

    def serialize(self, value: datetime.datetime):
        return round(value.timestamp())

    def deserialize(self, value):
        return datetime.datetime.fromtimestamp(value)
