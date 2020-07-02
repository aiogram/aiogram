import importlib

import aiogram


def test_file_deleted():
    try:
        major, minor, _ = aiogram.__version__.split(".")
    except ValueError:  # raised if version is major.minor
        major, minor = aiogram.__version__.split(".")
    if major == "2" and int(minor) >= 11:
        mongo_aiomongo = importlib.util.find_spec("aiogram.contrib.fsm_storage.mongo_aiomongo")
        assert mongo_aiomongo is False, "Remove aiogram.contrib.fsm_storage.mongo_aiomongo file, and replace storage " \
                          "in aiogram.contrib.fsm_storage.mongo with storage " \
                          "from aiogram.contrib.fsm_storage.mongo_motor"
