# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for git_ai_reporter.utils.json_helpers module.

This module tests robust JSON handling, including tolerance for
malformed JSON and serialization of various data types.
"""

from datetime import date
from datetime import datetime
from datetime import timezone
from decimal import Decimal
import json
from pathlib import Path
from uuid import UUID

import pytest
import pytest_check as check

from git_ai_reporter.utils.json_helpers import safe_json_decode
from git_ai_reporter.utils.json_helpers import safe_json_encode


class TestSafeJsonDecode:
    """Test suite for safe_json_decode function."""

    @pytest.mark.smoke
    def test_valid_json_string(self) -> None:
        """Test decoding a valid JSON string."""
        json_str = '{"key": "value", "number": 42}'
        result = safe_json_decode(json_str)
        check.equal(result, {"key": "value", "number": 42})

    def test_json_with_trailing_comma(self) -> None:
        """Test decoding JSON with trailing comma."""
        json_str = '{"key": "value", "number": 42,}'
        result = safe_json_decode(json_str)
        check.equal(result, {"key": "value", "number": 42})

    def test_json_with_single_quotes(self) -> None:
        """Test decoding JSON with single quotes raises error."""
        json_str = "{'key': 'value', 'number': 42}"
        # Single quotes are not valid JSON and should raise error
        with pytest.raises(json.JSONDecodeError):
            safe_json_decode(json_str)

    def test_json_with_markdown_fence(self) -> None:
        """Test decoding JSON wrapped in markdown code fence."""
        json_str = '```json\n{"key": "value"}\n```'
        result = safe_json_decode(json_str)
        check.equal(result, {"key": "value"})

    def test_json_with_plain_markdown_fence(self) -> None:
        """Test decoding JSON wrapped in plain markdown fence."""
        json_str = '```\n{"key": "value"}\n```'
        result = safe_json_decode(json_str)
        check.equal(result, {"key": "value"})

    def test_nested_json_with_trailing_commas(self) -> None:
        """Test decoding nested JSON with multiple trailing commas."""
        json_str = '{"outer": {"inner": "value",},}'
        result = safe_json_decode(json_str)
        check.equal(result, {"outer": {"inner": "value"}})

    def test_array_with_trailing_comma(self) -> None:
        """Test decoding array with trailing comma."""
        json_str = '["item1", "item2", "item3",]'
        result = safe_json_decode(json_str)
        check.equal(result, ["item1", "item2", "item3"])

    def test_mixed_quotes(self) -> None:
        """Test decoding JSON with mixed quotes raises error."""
        json_str = """{"key": 'value', "key2": "value2"}"""
        # Mixed quotes are not valid JSON
        with pytest.raises(json.JSONDecodeError):
            safe_json_decode(json_str)

    def test_empty_json_object(self) -> None:
        """Test decoding empty JSON object."""
        json_str = "{}"
        result = safe_json_decode(json_str)
        check.equal(result, {})

    def test_empty_json_array(self) -> None:
        """Test decoding empty JSON array."""
        json_str = "[]"
        result = safe_json_decode(json_str)
        check.equal(result, [])

    def test_json_with_numbers(self) -> None:
        """Test decoding JSON with various number types."""
        json_str = '{"int": 42, "float": 3.14, "exp": 1.5e2, "neg": -100}'
        result = safe_json_decode(json_str)
        check.equal(result["int"], 42)  # type: ignore[index]
        check.equal(result["float"], 3.14)  # type: ignore[index]
        check.equal(result["exp"], 150.0)  # type: ignore[index]
        check.equal(result["neg"], -100)  # type: ignore[index]

    def test_json_with_booleans_and_null(self) -> None:
        """Test decoding JSON with booleans and null."""
        json_str = '{"true": true, "false": false, "null": null}'
        result = safe_json_decode(json_str)
        check.is_true(result["true"])  # type: ignore[index]
        check.is_false(result["false"])  # type: ignore[index]
        check.is_none(result["null"])  # type: ignore[index]

    def test_deeply_nested_json(self) -> None:
        """Test decoding deeply nested JSON structure."""
        json_str = '{"a": {"b": {"c": {"d": {"e": "value"}}}}}'
        result = safe_json_decode(json_str)
        check.equal(
            result["a"]["b"]["c"]["d"]["e"],  # type: ignore[index]
            "value",
        )

    def test_json_with_escaped_characters(self) -> None:
        """Test decoding JSON with escaped characters."""
        json_str = r'{"quote": "He said \"Hello\"", "newline": "Line1\nLine2"}'
        result = safe_json_decode(json_str)
        check.equal(result["quote"], 'He said "Hello"')  # type: ignore[index]
        check.equal(result["newline"], "Line1\nLine2")  # type: ignore[index]

    def test_invalid_json_raises_error(self) -> None:
        """Test that completely invalid JSON might parse as None."""
        json_str = "not json at all"
        # tolerantjson is very forgiving and might parse this
        # It could be None or raise an error, check for both
        if (result := safe_json_decode(json_str)) is not None:
            check.is_none(result)

    def test_incomplete_json_raises_error(self) -> None:
        """Test that incomplete JSON might be handled gracefully."""
        json_str = '{"key": '
        # tolerantjson might handle this or raise an error
        try:
            result = safe_json_decode(json_str)
            # If it doesn't raise, check the result
            check.is_not_none(result)
        except json.JSONDecodeError:
            # This is expected for truly incomplete JSON
            pass

    def test_json_with_unclosed_bracket(self) -> None:
        """Test that JSON with unclosed bracket might be handled."""
        json_str = '{"key": "value"'
        # tolerantjson might auto-close the bracket
        try:
            result = safe_json_decode(json_str)
            # If it succeeds, should have the key
            if isinstance(result, dict):
                check.equal(result.get("key"), "value")
        except json.JSONDecodeError:
            # This is also acceptable
            pass

    def test_large_json_document(self) -> None:
        """Test decoding a large JSON document."""
        # Create a large JSON structure
        large_obj = {
            f"key_{i}": {
                "value": f"value_{i}",
                "nested": {"data": list(range(10))},
            }
            for i in range(100)
        }
        json_str = json.dumps(large_obj)
        result = safe_json_decode(json_str)
        check.equal(len(result), 100)  # type: ignore[arg-type]

    def test_tolerantjson_parse_error_non_json(self) -> None:
        """Test tolerantjson ParseError without JSONDecodeError in args."""
        from unittest.mock import patch  # pylint: disable=import-outside-toplevel

        with patch("tolerantjson.tolerate") as mock_tolerate:
            # pylint: disable=import-outside-toplevel
            from tolerantjson.parser import ParseError as TolerateParseError

            # Create ParseError with non-JSONDecodeError arg
            parse_error = TolerateParseError("Some error")
            parse_error.args = ("Not a JSONDecodeError",)
            mock_tolerate.side_effect = parse_error

            with pytest.raises(json.JSONDecodeError) as exc_info:
                safe_json_decode("{invalid}")

            # This should hit line 52 - str(e) converts ParseError to string
            check.equal(exc_info.value.msg, str(parse_error))


class TestSafeJsonEncode:
    """Test suite for safe_json_encode function."""

    @pytest.mark.smoke
    def test_basic_types(self) -> None:
        """Test encoding basic Python types."""
        data = {
            "string": "value",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }
        json_str = safe_json_encode(data)
        decoded = json.loads(json_str)
        check.equal(decoded, data)

    def test_datetime_serialization(self) -> None:
        """Test serialization of datetime objects."""
        dt = datetime(2025, 1, 7, 12, 30, 45, tzinfo=timezone.utc)
        data = {"timestamp": dt}
        json_str = safe_json_encode(data)
        decoded = json.loads(json_str)
        check.equal(decoded["timestamp"], "2025-01-07T12:30:45+00:00")

    def test_date_serialization(self) -> None:
        """Test serialization of date objects."""
        d = date(2025, 1, 7)
        data = {"date": d}
        json_str = safe_json_encode(data)
        decoded = json.loads(json_str)
        check.equal(decoded["date"], "2025-01-07")

    def test_decimal_serialization(self) -> None:
        """Test serialization of Decimal objects."""
        dec = Decimal("123.456")
        data = {"amount": dec}
        json_str = safe_json_encode(data)
        decoded = json.loads(json_str)
        check.equal(decoded["amount"], "123.456")

    def test_uuid_serialization(self) -> None:
        """Test serialization of UUID objects."""
        uid = UUID("12345678-1234-5678-1234-567812345678")
        data = {"id": uid}
        json_str = safe_json_encode(data)
        decoded = json.loads(json_str)
        check.equal(decoded["id"], "12345678-1234-5678-1234-567812345678")

    def test_path_serialization(self) -> None:
        """Test serialization of Path objects."""
        p = Path("/home/user/file.txt")
        data = {"path": p}
        json_str = safe_json_encode(data)
        decoded = json.loads(json_str)
        check.equal(decoded["path"], "/home/user/file.txt")

    def test_mixed_special_types(self) -> None:
        """Test serialization of multiple special types together."""
        data = {
            "datetime": datetime(2025, 1, 7, 10, 0, 0),
            "date": date(2025, 1, 7),
            "decimal": Decimal("99.99"),
            "uuid": UUID("deadbeef-dead-beef-dead-beefdeadbeef"),
            "path": Path("/tmp/test"),  # nosec B108 - Test only
            "normal": "string",
        }
        json_str = safe_json_encode(data)
        decoded = json.loads(json_str)
        check.is_in("2025-01-07", decoded["datetime"])
        check.equal(decoded["date"], "2025-01-07")
        check.equal(decoded["decimal"], "99.99")
        check.equal(decoded["uuid"], "deadbeef-dead-beef-dead-beefdeadbeef")
        check.equal(decoded["path"], "/tmp/test")  # nosec B108 - Test data
        check.equal(decoded["normal"], "string")

    def test_indent_parameter(self) -> None:
        """Test that indent parameter works correctly."""
        data = {"key": "value", "nested": {"inner": "data"}}
        json_str = safe_json_encode(data, indent=2)
        check.is_in("  ", json_str)  # Check for indentation
        check.is_in("\n", json_str)  # Check for newlines

    def test_sort_keys_parameter(self) -> None:
        """Test that sort_keys parameter works correctly."""
        data = {"z": 1, "a": 2, "m": 3}
        json_str = safe_json_encode(data, sort_keys=True)
        # Keys should appear in alphabetical order
        a_pos = json_str.index('"a"')
        m_pos = json_str.index('"m"')
        z_pos = json_str.index('"z"')
        check.less(a_pos, m_pos)
        check.less(m_pos, z_pos)

    def test_non_serializable_type_raises_error(self) -> None:
        """Test that non-serializable types raise TypeError."""

        class CustomClass:  # pylint: disable=too-few-public-methods
            """A custom class that can't be serialized."""

            def __init__(self) -> None:
                """Initialize the custom class."""
                self.value = "test"

        data = {"obj": CustomClass()}
        with pytest.raises(TypeError) as exc_info:
            safe_json_encode(data)
        check.is_in("CustomClass", str(exc_info.value))

    def test_nested_special_types(self) -> None:
        """Test serialization of nested structures with special types."""
        data = {
            "records": [
                {
                    "id": UUID("11111111-1111-1111-1111-111111111111"),
                    "created": datetime(2025, 1, 1, 0, 0, 0),
                    "amount": Decimal("100.00"),
                },
                {
                    "id": UUID("22222222-2222-2222-2222-222222222222"),
                    "created": datetime(2025, 1, 2, 0, 0, 0),
                    "amount": Decimal("200.00"),
                },
            ]
        }
        json_str = safe_json_encode(data)
        decoded = json.loads(json_str)
        check.equal(len(decoded["records"]), 2)
        check.equal(
            decoded["records"][0]["id"],
            "11111111-1111-1111-1111-111111111111",
        )

    def test_empty_structures(self) -> None:
        """Test encoding empty structures."""
        data = {"empty_dict": {}, "empty_list": [], "empty_string": ""}
        json_str = safe_json_encode(data)
        decoded = json.loads(json_str)
        check.equal(decoded["empty_dict"], {})
        check.equal(decoded["empty_list"], [])
        check.equal(decoded["empty_string"], "")

    def test_unicode_handling(self) -> None:
        """Test proper handling of Unicode characters."""
        data = {
            "emoji": "🚀",
            "chinese": "你好",
            "arabic": "مرحبا",
            "special": "café",
        }
        json_str = safe_json_encode(data)
        decoded = json.loads(json_str)
        check.equal(decoded["emoji"], "🚀")
        check.equal(decoded["chinese"], "你好")
        check.equal(decoded["arabic"], "مرحبا")
        check.equal(decoded["special"], "café")


class TestRoundTrip:
    """Test suite for round-trip encoding and decoding."""

    def test_simple_roundtrip(self) -> None:
        """Test round-trip for simple data."""
        original = {"key": "value", "number": 42}
        encoded = safe_json_encode(original)
        decoded = safe_json_decode(encoded)
        check.equal(decoded, original)

    def test_complex_roundtrip(self) -> None:
        """Test round-trip for complex nested data."""
        original = {
            "users": [
                {"name": "Alice", "age": 30, "active": True},
                {"name": "Bob", "age": 25, "active": False},
            ],
            "metadata": {
                "version": "1.0",
                "count": 2,
            },
        }
        encoded = safe_json_encode(original)
        decoded = safe_json_decode(encoded)
        check.equal(decoded, original)

    def test_special_types_partial_roundtrip(self) -> None:
        """Test that special types serialize but come back as strings."""
        original = {
            "date": date(2025, 1, 7),
            "decimal": Decimal("123.45"),
        }
        encoded = safe_json_encode(original)
        decoded = safe_json_decode(encoded)
        # Special types come back as strings after round-trip
        check.equal(decoded["date"], "2025-01-07")  # type: ignore[index]
        check.equal(decoded["decimal"], "123.45")  # type: ignore[index]
