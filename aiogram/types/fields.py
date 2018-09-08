import abc
import datetime

__all__ = ('BaseField', 'Field', 'ListField', 'DateTimeField', 'TextField', 'ListOfLists')


class BaseField(metaclass=abc.ABCMeta):
    """
    Base field (prop)
    """

    def __init__(self, *, base=None, default=None, alias=None, on_change=None):
        """
        Init prop

        :param base: class for child element
        :param default: default value
        :param alias: alias name (for e.g. field 'from' has to be named 'from_user'
                      as 'from' is a builtin Python keyword
        :param on_change: callback will be called when value is changed
        """
        self.base_object = base
        self.default = default
        self.alias = alias
        self.on_change = on_change

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
        Get value for the current object instance

        :param instance:
        :return:
        """
        return instance.values.get(self.alias, self.default)

    def set_value(self, instance, value, parent=None):
        """
        Set prop value

        :param instance:
        :param value:
        :param parent:
        :return:
        """
        self.resolve_base(instance)
        value = self.deserialize(value, parent)
        instance.values[self.alias] = value
        self._trigger_changed(instance, value)

    def _trigger_changed(self, instance, value):
        if not self.on_change and instance is not None:
            return
        callback = getattr(instance, self.on_change)
        callback(value)

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
    def deserialize(self, value, parent=None):
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
        if self.base_object is not None and hasattr(value, 'to_python'):
            return value.to_python()
        return value

    def deserialize(self, value, parent=None):
        if isinstance(value, dict) \
                and self.base_object is not None \
                and not hasattr(value, 'base_object') \
                and not hasattr(value, 'to_python'):
            return self.base_object(conf={'parent': parent}, **value)
        return value


class ListField(Field):
    """
    Field contains list ob objects
    """

    def __init__(self, *args, **kwargs):
        default = kwargs.pop('default', None)
        if default is None:
            default = []

        super(ListField, self).__init__(*args, default=default, **kwargs)

    def serialize(self, value):
        result = []
        serialize = super(ListField, self).serialize
        for item in value:
            result.append(serialize(item))
        return result

    def deserialize(self, value, parent=None):
        result = []
        deserialize = super(ListField, self).deserialize
        for item in value:
            result.append(deserialize(item, parent=parent))
        return result


class ListOfLists(Field):
    def serialize(self, value):
        result = []
        serialize = super(ListOfLists, self).serialize
        for row in value:
            row_result = []
            for item in row:
                row_result.append(serialize(item))
            result.append(row_result)
        return result

    def deserialize(self, value, parent=None):
        result = []
        deserialize = super(ListOfLists, self).deserialize
        if hasattr(value, '__iter__'):
            for row in value:
                row_result = []
                for item in row:
                    row_result.append(deserialize(item, parent=parent))
                result.append(row_result)
        return result


class DateTimeField(Field):
    """
    In this field st_ored datetime

    in: unixtime
    out: datetime
    """

    def serialize(self, value: datetime.datetime):
        return round(value.timestamp())

    def deserialize(self, value, parent=None):
        return datetime.datetime.fromtimestamp(value)


class TextField(Field):
    def __init__(self, *, prefix=None, suffix=None, default=None, alias=None):
        super(TextField, self).__init__(default=default, alias=alias)
        self.prefix = prefix
        self.suffix = suffix

    def serialize(self, value):
        if value is None:
            return value
        if self.prefix:
            value = self.prefix + value
        if self.suffix:
            value += self.suffix
        return value

    def deserialize(self, value, parent=None):
        if value is not None and not isinstance(value, str):
            raise TypeError(f"Field '{self.alias}' should be str not {type(value).__name__}")
        return value
