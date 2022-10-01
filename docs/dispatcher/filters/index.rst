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
    text
    chat_member_updated
    magic_filters
    magic_data
    callback_data
    exception

Writing own filters
=========================

Filters can be:

- Asynchronous function (:code:`async def my_filter(*args, **kwargs): pass`)
- Synchronous function (:code:`def my_filter(*args, **kwargs): pass`)
- Anonymous function (:code:`lambda event: True`)
- Any awaitable object
- Subclass of :class:`aiogram.filters.base.Filter`
- Instances of :ref:`MagicFilter <magic-filters>`

and should return bool or dict.
If the dictionary is passed as result of filter - resulted data will be propagated to the next
filters and handler as keywords arguments.

Base class for own filters
--------------------------

.. autoclass:: aiogram.filters.base.Filter
    :members: __call__,update_handler_flags
    :member-order: bysource
    :undoc-members: False

Own filter example
------------------

For example if you need to make simple text filter:

.. literalinclude:: ../../../examples/own_filter.py
