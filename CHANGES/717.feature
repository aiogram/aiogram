Improved description of filters resolving error.
For example when you try to pass wrong type of argument to the filter but don't know why filter is not resolved now you can get error like this:

.. code-block:: python3

    aiogram.exceptions.FiltersResolveError: Unknown keyword filters: {'content_types'}
      Possible cases:
      - 1 validation error for ContentTypesFilter
        content_types
          Invalid content types {'42'} is not allowed here (type=value_error)
