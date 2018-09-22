import platform
import sys

import aiohttp

import aiogram
from aiogram.utils import json


class SysInfo:
    @property
    def os(self):
        return platform.platform()

    @property
    def python_implementation(self):
        return platform.python_implementation()

    @property
    def python(self):
        return sys.version.replace('\n', '')

    @property
    def aiogram(self):
        return aiogram.__version__

    @property
    def api(self):
        return aiogram.__api_version__

    @property
    def uvloop(self):
        try:
            import uvloop
        except ImportError:
            return
        return uvloop.__version__

    @property
    def ujson(self):
        try:
            import ujson
        except ImportError:
            return
        return ujson.__version__

    @property
    def rapidjson(self):
        try:
            import rapidjson
        except ImportError:
            return
        return rapidjson.__version__

    @property
    def aiohttp(self):
        return aiohttp.__version__

    def collect(self):
        yield f'{self.python_implementation}: {self.python}'
        yield f'OS: {self.os}'
        yield f'aiogram: {self.aiogram}'
        yield f'aiohttp: {self.aiohttp}'

        uvloop = self.uvloop
        if uvloop:
            yield f'uvloop: {uvloop}'

        yield f'JSON mode: {json.mode}'

        rapidjson = self.rapidjson
        if rapidjson:
            yield f'rapidjson: {rapidjson}'
        ujson = self.ujson
        if ujson:
            yield f'ujson: {ujson}'

    def __str__(self):
        return '\n'.join(self.collect())


if __name__ == '__main__':
    print(SysInfo())
