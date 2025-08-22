# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Type stubs for the tolerantjson library."""

from typing import Any

class ParseException(Exception):
    """Exception raised when tolerantjson cannot parse the input."""

    args: tuple[Any, ...]

    def __init__(self, *args: Any) -> None: ...

def tolerate(json_string: str) -> Any:
    """Parse a JSON string with tolerance for common errors.

    Args:
        json_string: The JSON string to parse.

    Returns:
        The parsed Python object (typically a dict or list).

    Raises:
        ParseException: If the string cannot be parsed even with tolerance.
    """
    ...
