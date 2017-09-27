import io as _io
from typing import TypeVar as _TypeVar

from . import base
from . import fields

__all__ = (
    'base', 'fields',
    'InputFile', 'String', 'Integer', 'Float', 'Boolean'
)

# Binding of builtin types
InputFile = _TypeVar('InputFile', _io.BytesIO, _io.FileIO, str)
String = _TypeVar('String', bound=str)
Integer = _TypeVar('Integer', bound=int)
Float = _TypeVar('Float', bound=float)
Boolean = _TypeVar('Boolean', bound=bool)
