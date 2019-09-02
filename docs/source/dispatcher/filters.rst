=======
Filters
=======

Basics
======

Filter factory greatly simplifies the reuse of filters when registering handlers.

Filters factory
===============

.. autoclass:: aiogram.dispatcher.filters.factory.FiltersFactory
    :members:
    :show-inheritance:

Builtin filters
===============
``aiogram`` has some builtin filters. Here you can see all of them:

Command
-------

.. autoclass:: aiogram.dispatcher.filters.builtin.Command
    :members:
    :show-inheritance:

CommandStart
------------

.. autoclass:: aiogram.dispatcher.filters.builtin.CommandStart
    :members:
    :show-inheritance:

CommandHelp
-----------

.. autoclass:: aiogram.dispatcher.filters.builtin.CommandHelp
    :members:
    :show-inheritance:

CommandSettings
---------------

.. autoclass:: aiogram.dispatcher.filters.builtin.CommandSettings
    :members:
    :show-inheritance:


CommandPrivacy
--------------

.. autoclass:: aiogram.dispatcher.filters.builtin.CommandPrivacy
    :members:
    :show-inheritance:


Text
----

.. autoclass:: aiogram.dispatcher.filters.builtin.Text
    :members:
    :show-inheritance:


HashTag
-------

.. autoclass:: aiogram.dispatcher.filters.builtin.HashTag
    :members:
    :show-inheritance:


Regexp
------

.. autoclass:: aiogram.dispatcher.filters.builtin.Regexp
    :members:
    :show-inheritance:


RegexpCommandsFilter
--------------------

.. autoclass:: aiogram.dispatcher.filters.builtin.RegexpCommandsFilter
    :members:
    :show-inheritance:


ContentTypeFilter
-----------------

.. autoclass:: aiogram.dispatcher.filters.builtin.ContentTypeFilter
    :members:
    :show-inheritance:


StateFilter
-----------

.. autoclass:: aiogram.dispatcher.filters.builtin.StateFilter
    :members:
    :show-inheritance:


ExceptionsFilter
----------------

.. autoclass:: aiogram.dispatcher.filters.builtin.ExceptionsFilter
    :members:
    :show-inheritance:


IDFilter
----------------

.. autoclass:: aiogram.dispatcher.filters.builtin.IDFilter
    :members:
    :show-inheritance:


AdminFilter
----------------

.. autoclass:: aiogram.dispatcher.filters.builtin.AdminFilter
    :members:
    :show-inheritance:


Making own filters (Custom filters)
===================================

Own filter can be:

- any callable object
- any async function
- any anonymous function (Example: ``lambda msg: msg.text == 'spam'``)
- Subclass of :obj:`AbstractFilter`,  :obj:`Filter` or :obj:`BoundFilter`


AbstractFilter
--------------
.. autoclass:: aiogram.dispatcher.filters.filters.AbstractFilter
    :members:
    :show-inheritance:

Filter
------
.. autoclass:: aiogram.dispatcher.filters.filters.Filter
    :members:
    :show-inheritance:

BoundFilter
-----------
.. autoclass:: aiogram.dispatcher.filters.filters.BoundFilter
    :members:
    :show-inheritance:


.. code-block:: python

    class ChatIdFilter(BoundFilter):
        key = 'chat_id'

        def __init__(self, chat_id: typing.Union[typing.Iterable, int]):
            if isinstance(chat_id, int):
                chat_id = [chat_id]
            self.chat_id = chat_id

        def check(self, message: types.Message) -> bool:
            return message.chat.id in self.chat_id


    dp.filters_factory.bind(ChatIdFilter, event_handlers=[dp.message_handlers])
