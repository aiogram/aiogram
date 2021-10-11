########
Storages
########

Storages out of the box
=======================

MemoryStorage
-------------

.. autoclass:: aiogram.dispatcher.fsm.storage.memory.MemoryStorage
    :members: __init__
    :member-order: bysource

RedisStorage
------------

.. autoclass:: aiogram.dispatcher.fsm.storage.redis.RedisStorage
    :members: __init__, from_url
    :member-order: bysource

Keys inside storage can be customized via key builders:

.. autoclass:: aiogram.dispatcher.fsm.storage.redis.KeyBuilder
    :members:
    :member-order: bysource

.. autoclass:: aiogram.dispatcher.fsm.storage.redis.DefaultKeyBuilder
    :members:
    :member-order: bysource


Writing own storages
====================

.. autoclass:: aiogram.dispatcher.fsm.storage.base.BaseStorage
    :members:
    :member-order: bysource
