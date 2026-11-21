"""Canonical form of a Bot API HTTP request body, shared by every request side (A-09, D-15).

Stdlib only, like ``trace.py``: side scripts load it by path, from the directory of
``--trace-module``. ``tests/test_differential_request.py`` checks the imports.

:func:`canonical_request` turns ``(content type, body)`` into two values:

- ``resolved``: encoding-independent params. JSON bodies are decoded; form fields (urlencoded or
  multipart) are decoded as JSON where they parse, so ``"100"`` and ``100`` agree. A JSON-body
  string value gets the same treatment, which keeps the rule symmetric. Every ``attach://<key>``
  is replaced by the file part it names, as ``{"file": {filename, sha256, content_type}}``; a file
  part nobody references stays under its own field name. The attach keys are random in 3.x, so
  they never reach the record.
- ``encoding``: ``json`` / ``urlencoded`` / ``multipart``, the media type, and the field order,
  with file parts renamed ``file#<n>`` in body order.
"""

from __future__ import annotations

import hashlib
import json
import urllib.parse
from email.message import Message
from email.parser import BytesHeaderParser
from typing import Any

ATTACH = "attach://"


def _decode(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


def _headers(content_type: str) -> Message:
    return BytesHeaderParser().parsebytes(f"Content-Type: {content_type}\r\n\r\n".encode())


def _multipart(boundary: str, body: bytes) -> list[tuple[str, Message, bytes]]:
    """``(name, headers, payload)`` per part, in body order."""
    delimiter = b"--" + boundary.encode("latin-1")
    parts = []
    for chunk in body.split(delimiter)[1:]:
        if chunk.startswith(b"--"):  # closing delimiter
            break
        head, _, payload = chunk.removeprefix(b"\r\n").partition(b"\r\n\r\n")
        headers = BytesHeaderParser().parsebytes(head + b"\r\n\r\n")
        name = headers.get_param("name", header="content-disposition")
        parts.append((str(name), headers, payload.removesuffix(b"\r\n")))
    return parts


def _attach(value: Any, files: dict[str, Any], used: set[str]) -> Any:
    if isinstance(value, str) and value.startswith(ATTACH) and value[len(ATTACH) :] in files:
        used.add(value[len(ATTACH) :])
        return files[value[len(ATTACH) :]]
    if isinstance(value, dict):
        return {key: _attach(item, files, used) for key, item in value.items()}
    if isinstance(value, list):
        return [_attach(item, files, used) for item in value]
    return value


def canonical_request(content_type: str, body: bytes) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return ``(resolved, encoding)`` for one request body; see the module docstring."""
    headers = _headers(content_type)
    media_type = headers.get_content_type()
    files: dict[str, Any] = {}
    order: list[str] = []
    if media_type == "application/json":
        kind = "json"
        params = {key: _decode(value) for key, value in json.loads(body or b"{}").items()}
        order = list(params)
    elif media_type == "multipart/form-data":
        kind = "multipart"
        params = {}
        for name, part, payload in _multipart(str(headers.get_param("boundary")), body):
            filename = part.get_filename()
            if filename is None:
                params[name] = _decode(payload.decode("utf-8"))
                order.append(name)
                continue
            files[name] = {
                "file": {
                    "filename": filename,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "content_type": part.get_content_type(),
                }
            }
            order.append(f"file#{len(files) - 1}")
    elif media_type == "application/x-www-form-urlencoded":
        kind = "urlencoded"
        pairs = urllib.parse.parse_qsl(body.decode("ascii"), keep_blank_values=True)
        params = {key: _decode(value) for key, value in pairs}
        order = [key for key, _ in pairs]
    else:
        msg = f"unsupported request content type {content_type!r}"
        raise ValueError(msg)
    used: set[str] = set()
    resolved = _attach(params, files, used)
    resolved.update((name, file) for name, file in files.items() if name not in used)
    return resolved, {"encoding": kind, "content_type": media_type, "fields": order}
