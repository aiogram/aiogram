"""
Build the schema of every Bot API type and method.

The toolkit reflects over ``model_fields[...].annotation``, which stays a forward reference
until a type's schema is built (types defer it to first use), so the package imports this
module before anything else.
"""

from aiogram import methods, types

for _module in (types, methods):
    for _name in _module.__all__:
        if hasattr(_model := getattr(_module, _name), "model_rebuild"):
            _model.model_rebuild()
