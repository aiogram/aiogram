=======
Filters
=======

Basics
======

Filter factory greatly simplifies the reuse of filters when registering handlers.

Filters factory
===============

.. autoclass:: aiogram.dispatcher.filters.FiltersFactory
    :members:
    :show-inheritance:

Builtin filters
===============
``aiogram`` has some builtin filters. Here you can see all of them:

Command
-------

.. autoclass:: aiogram.dispatcher.filters.Command
    :members:
    :show-inheritance:

CommandStart
------------

.. autoclass:: aiogram.dispatcher.filters.CommandStart
    :members:
    :show-inheritance:

CommandHelp
-----------

.. autoclass:: aiogram.dispatcher.filters.CommandHelp
    :members:
    :show-inheritance:

CommandSettings
---------------

.. autoclass:: aiogram.dispatcher.filters.CommandSettings
    :members:
    :show-inheritance:


CommandPrivacy
--------------

.. autoclass:: aiogram.dispatcher.filters.CommandPrivacy
    :members:
    :show-inheritance:


Text
----

.. autoclass:: aiogram.dispatcher.filters.Text
    :members:
    :show-inheritance:


HashTag
-------

.. autoclass:: aiogram.dispatcher.filters.HashTag
    :members:
    :show-inheritance:


Regexp
------

.. autoclass:: aiogram.dispatcher.filters.Regexp
    :members:
    :show-inheritance:


RegexpCommandsFilter
--------------------

.. autoclass:: aiogram.dispatcher.filters.RegexpCommandsFilter
    :members:
    :show-inheritance:


ContentTypeFilter
-----------------

.. autoclass:: aiogram.dispatcher.filters.ContentTypeFilter
    :members:
    :show-inheritance:

IsSenderContact
---------------

.. autoclass:: aiogram.dispatcher.filters.IsSenderContact
    :members:
    :show-inheritance:

StateFilter
-----------

.. autoclass:: aiogram.dispatcher.filters.StateFilter
    :members:
    :show-inheritance:


ExceptionsFilter
----------------

.. autoclass:: aiogram.dispatcher.filters.ExceptionsFilter
    :members:
    :show-inheritance:


IDFilter
--------

.. autoclass:: aiogram.dispatcher.filters.builtin.IDFilter
    :members:
    :show-inheritance:


AdminFilter
-----------

.. autoclass:: aiogram.dispatcher.filters.AdminFilter
    :members:
    :show-inheritance:


IsReplyFilter
-------------

.. autoclass:: aiogram.dispatcher.filters.IsReplyFilter
    :members:
    :show-inheritance:


ForwardedMessageFilter
----------------------

.. autoclass:: aiogram.dispatcher.filters.ForwardedMessageFilter
    :members:
    :show-inheritance:


ChatTypeFilter
--------------

.. autoclass:: aiogram.dispatcher.filters.ChatTypeFilter
    :members:
    :show-inheritance:
    

MediaGroupFilter
-------------

.. autoclass:: aiogram.dispatcher.filters.MediaGroupFilter
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
.. autoclass:: aiogram.dispatcher.filters.AbstractFilter
    :members:
    :show-inheritance:

Filter
------
.. autoclass:: aiogram.dispatcher.filters.Filter
    :members:
    :show-inheritance:

BoundFilter
-----------
.. autoclass:: aiogram.dispatcher.filters.BoundFilter
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

