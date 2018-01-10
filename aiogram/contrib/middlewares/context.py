from aiogram import types
from aiogram.dispatcher import ctx
from aiogram.dispatcher.middlewares import BaseMiddleware

OBJ_KEY = '_context_data'


class ContextMiddleware(BaseMiddleware):
    """
    Allow to store data at all of lifetime of Update object
    """

    async def on_pre_process_update(self, update: types.Update):
        """
        Start of Update lifetime

        :param update:
        :return:
        """
        self._configure_update(update)

    async def on_post_process_update(self, update: types.Update, result):
        """
        On finishing of processing update

        :param update:
        :param result:
        :return:
        """
        if OBJ_KEY in update.conf:
            del update.conf[OBJ_KEY]

    def _configure_update(self, update: types.Update = None):
        """
        Setup data storage

        :param update:
        :return:
        """
        obj = update.conf[OBJ_KEY] = {}
        return obj

    def _get_dict(self):
        """
        Get data from update stored in current context

        :return:
        """
        update = ctx.get_update()
        obj = update.conf.get(OBJ_KEY, None)
        if obj is None:
            obj = self._configure_update(update)
        return obj

    def __getitem__(self, item):
        """
        Item getter

        :param item:
        :return:
        """
        return self._get_dict()[item]

    def __setitem__(self, key, value):
        """
        Item setter

        :param key:
        :param value:
        :return:
        """
        data = self._get_dict()
        data[key] = value

    def __iter__(self):
        """
        Iterate over dict

        :return:
        """
        return self._get_dict().__iter__()

    def keys(self):
        """
        Iterate over dict keys

        :return:
        """
        return self._get_dict().keys()

    def values(self):
        """
        Iterate over dict values

        :return:
        """
        return self._get_dict().values()

    def get(self, key, default=None):
        """
        Get item from dit or return default value

        :param key:
        :param default:
        :return:
        """
        return self._get_dict().get(key, default)

    def export(self):
        """
        Export all data s dict

        :return:
        """
        return self._get_dict()
