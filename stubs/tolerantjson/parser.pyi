# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Type stubs for the tolerantjson.parser module."""

from typing import Any

class ParseError(Exception):
    """Exception raised during parsing in the tolerantjson.parser module."""

    args: tuple[Any, ...]

    def __init__(self, *args: Any) -> None: ...
