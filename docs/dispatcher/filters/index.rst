================
Filtering events
================

Filters is needed for routing updates to the specific handler.
Searching of handler is always stops on first match set of filters are pass. 

*aiogram* has some builtin useful filters.

Builtin filters
===============

Here is list of builtin filters:

.. toctree::
    :maxdepth: 1

    command
    content_types
    text
    exception

Or you can do :ref:`✨ some magic <magic-filters>`

Own filters specification
=========================

Filters can be:

- Asynchronous function (:code:`async def my_filter(*args, **kwargs): pass`)

- Synchronous function (:code:`def my_filter(*args, **kwargs): pass`)

- Anonymous function (:code:`lambda event: True`)

- Any awaitable object

- Subclass of :ref:`BaseFilter <filters-base>`

Filters should return bool or dict. 
If the dictionary is passed as result of filter - resulted data will be propagated to the next 
filters and handler as keywords arguments.

Writing bound filters
=====================

.. autoclass:: aiogram.dispatcher.filters.base.BaseFilter
    :members: __call__
    :member-order: bysource
    :undoc-members: False

For example if you need to make simple text filter:

.. code-block:: python

    from aiogram.filters import BaseFilter


    class MyText(BaseFilter):
        my_text: str

        async def __call__(self, message: Message) -> bool:
            return message.text == self.my_text


    router.message.bind_filter(MyText)

    @router.message(my_text="hello")
    async def my_handler(message: Message): ...

.. note::

    Bound filters is always recursive propagates to the nested routers.
