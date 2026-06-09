.. _Filtering events:

================
Filtering events
================

Filters is needed for routing updates to the specific handler.
Searching of handler is always stops on first match set of filters are pass.
By default, all handlers has empty set of filters, so all updates will be passed to first handler that has empty set of filters.

*aiogram* has some builtin useful filters or you can write own filters.

Builtin filters
===============

Here is list of builtin filters:

.. toctree::
    :maxdepth: 1

    command
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

.. _combining-filters:

Combining Filters
=================

In general, all filters can be combined in two ways


Recommended way
---------------

If you specify multiple filters in a row, it will be checked with an "and" condition:

.. code-block:: python

    @<router>.message(F.text.startswith("show"), F.text.endswith("example"))


Also, if you want to use two alternative ways to run the same handler ("or" condition)
you can register the handler twice or more times as you like

.. code-block:: python

    @<router>.message(F.text == "hi")
    @<router>.message(CommandStart())


Also sometimes you will need to invert the filter result, for example you have an *IsAdmin* filter
and you want to check if the user is not an admin

.. code-block:: python

    @<router>.message(~IsAdmin())


Another possible way
--------------------

An alternative way is to combine using special functions (:func:`and_f`, :func:`or_f`, :func:`invert_f` from :code:`aiogram.filters` module):

.. code-block:: python

    and_f(F.text.startswith("show"), F.text.endswith("example"))
    or_f(F.text(text="hi"), CommandStart())
    invert_f(IsAdmin())
    and_f(<A>, or_f(<B>, <C>))
