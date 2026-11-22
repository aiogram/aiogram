########
Storages
########

Storages out of the box
=======================

MemoryStorage
-------------

.. autoclass:: aiogram.fsm.storage.memory.MemoryStorage
    :members: __init__
    :member-order: bysource

RedisStorage
------------

.. autoclass:: aiogram.fsm.storage.redis.RedisStorage
    :members: __init__, from_url
    :member-order: bysource

MongoStorage
------------

.. autoclass:: aiogram.fsm.storage.pymongo.PyMongoStorage
    :members: __init__, from_url
    :member-order: bysource

.. autoclass:: aiogram.fsm.storage.mongo.MongoStorage
    :members: __init__, from_url
    :member-order: bysource

KeyBuilder
------------

Keys inside Redis and Mongo storages can be customized via key builders:

.. autoclass:: aiogram.fsm.storage.base.KeyBuilder
    :members:
    :member-order: bysource

.. autoclass:: aiogram.fsm.storage.base.DefaultKeyBuilder
    :members:
    :member-order: bysource


Writing own storages
====================

.. autoclass:: aiogram.fsm.storage.base.BaseStorage
    :members:
    :member-order: bysource

Records and batches
-------------------

:meth:`BaseStorage.get_records <aiogram.fsm.storage.base.BaseStorage.get_records>` and
:meth:`BaseStorage.apply_writes <aiogram.fsm.storage.base.BaseStorage.apply_writes>` read and write
several keys at once. A storage that implements only the abstract methods gets working fallbacks;
override them to read or write in one round trip.

.. autoclass:: aiogram.fsm.storage.base.StorageRecord
    :members:

.. autoclass:: aiogram.fsm.storage.base.StorageWrite
    :members:

.. autodata:: aiogram.fsm.storage.base.UNCHANGED
    :no-value:
