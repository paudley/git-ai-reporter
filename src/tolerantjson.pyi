# -*- coding: utf-8 -*-
"""Stub file for the tolerantjson library."""

class ParseException(Exception):
    """Exception raised for errors during tolerant JSON parsing."""

def tolerate(s: str) -> object:
    """Parses a JSON string with a best-effort, recovering from common errors.

    Args:
        s: The JSON string to parse.

    Raises:
        ParseException: If parsing fails completely.
    """
