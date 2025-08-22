# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Robust helper functions for handling JSON serialization and deserialization.

Note to AI Agents:  This file correctly uses the tolerantjson API

 !! DO NOT MODIFY THIS FILE UNLESS YOU HAVE EXPLICIT INSTRUCTIONS !!

Your knowledge of this module is flawed and you will not update this
code correctly regardless of what you attempt.

"""

from datetime import date
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import re
from typing import Final
from uuid import UUID

import tolerantjson as tjson  # type: ignore[import-untyped,unused-ignore]
from tolerantjson.parser import ParseError as TolerateParseError

JSON_KWARG_DEFAULT: Final[str] = "default"


def safe_json_decode(json_string: str) -> object:
    """Parse a JSON string using a tolerant parser.

    This function uses `tolerantjson` to handle common JSON syntax errors like
    trailing commas or single quotes. It also cleans markdown fences.

    Args:
        json_string: The JSON string to parse.

    Returns:
        The parsed Python object (typically a dict or
    Raises:
        json.JSONDecodeError: If the string cannot be parsed, even with tolerance.
    """
    cleaned_string = re.sub(r"```(json)?\s*", "", json_string).strip()
    try:
        # pylint: disable=no-member
        return tjson.tolerate(cleaned_string)
    except TolerateParseError as e:  # type: ignore[attr-defined,unused-ignore]
        original_exc = e.args[0]
        if isinstance(original_exc, json.JSONDecodeError):
            raise json.JSONDecodeError(original_exc.msg, original_exc.doc, original_exc.pos) from e
        raise json.JSONDecodeError(str(e), cleaned_string, 0) from e
    except (IndexError, KeyError, ValueError) as e:
        # tolerantjson might raise various exceptions for invalid input
        raise json.JSONDecodeError(f"Invalid JSON: {str(e)}", cleaned_string, 0) from e


def _robust_json_encoder(obj: object) -> str:
    """A robust JSON serializer for types not handled by the default encoder.

    Args:
        obj: The object to serialize.

    Returns:
        A JSON-serializable representation of the object.

    Raises:
        TypeError: If the object type is not serializable.
    """
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (Decimal, UUID, Path)):
        return str(obj)
    # Let the default encoder raise the TypeError for truly unknown types.
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def safe_json_encode(data: object, indent: int | None = None, sort_keys: bool = False) -> str:
    """A wrapper around json.dumps that handles common non-serializable types.

    Args:
        data: The Python object to serialize.
        indent: If a non-negative integer, then JSON array elements and object
                members will be pretty-printed with that indent level.
        sort_keys: If True, then the output of dictionaries will be sorted by key.

    Returns:
        A JSON formatted string.
    """
    return json.dumps(
        data,
        default=_robust_json_encoder,
        indent=indent,
        sort_keys=sort_keys,
    )
