# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Additional unit tests for file_helpers module to improve coverage."""

import json
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest_check as check

from git_ai_reporter.utils.file_helpers import \
    _extract_string_values_from_json  # pylint: disable=import-private-name
from git_ai_reporter.utils.file_helpers import extract_text_from_file


class TestFileHelpers:
    """Test suite for file_helpers functions to improve coverage."""

    def test_extract_text_from_file_json(self, tmp_path: Path) -> None:
        """Test extract_text_from_file with JSON file."""
        json_file = tmp_path / "test.json"
        json_data = {"key": "value", "nested": {"data": "content"}}
        json_file.write_text(json.dumps(json_data))

        result = extract_text_from_file(json_file)
        check.is_in("value", result)
        check.is_in("content", result)

    def test_extract_text_from_file_markdown(self, tmp_path: Path) -> None:
        """Test extract_text_from_file with markdown file."""
        md_file = tmp_path / "test.md"
        md_content = "# Header\n\nThis is **bold** text with [link](http://example.com)."
        md_file.write_text(md_content)

        result = extract_text_from_file(md_file)
        check.is_in("Header", result)
        check.is_in("bold", result)

    def test_extract_text_from_file_nonexistent(self, tmp_path: Path) -> None:
        """Test extract_text_from_file with nonexistent file."""
        nonexistent = tmp_path / "nonexistent.txt"

        result = extract_text_from_file(nonexistent)
        check.equal(result, "")

    def test_extract_text_from_file_unsupported_type(self, tmp_path: Path) -> None:
        """Test extract_text_from_file with unsupported file type."""
        txt_file = tmp_path / "test.txt"
        content = "Plain text content"
        txt_file.write_text(content)

        result = extract_text_from_file(txt_file)
        check.equal(result, content)  # Returns content as-is for unsupported types

    def test_extract_text_from_file_invalid_json(self, tmp_path: Path) -> None:
        """Test extract_text_from_file with invalid JSON."""
        json_file = tmp_path / "invalid.json"
        invalid_content = "{invalid json}"
        json_file.write_text(invalid_content)

        result = extract_text_from_file(json_file)
        check.equal(result, invalid_content)  # Falls back to plain text

    def test_extract_string_values_from_json_simple(self) -> None:
        """Test _extract_string_values_from_json with simple data."""
        data = {"key": "value", "number": 42, "bool": True}

        result = _extract_string_values_from_json(data)
        check.is_in("key: value", result)
        check.equal(len(result), 1)  # Only the string value should be included

    def test_extract_string_values_from_json_nested(self) -> None:
        """Test _extract_string_values_from_json with nested data."""
        data = {
            "level1": {"level2": {"text": "nested value", "array": ["item1", "item2", 123]}},
            "top_level": "top value",
        }

        result = _extract_string_values_from_json(data)
        check.is_in("text: nested value", result)
        check.is_in("top_level: top value", result)
        # Array strings are not formatted as key:value but the function doesn't handle arrays of strings

    def test_extract_string_values_from_json_array(self) -> None:
        """Test _extract_string_values_from_json with array data."""
        data = ["string1", "string2", 42, True, {"nested": "value"}]

        result = _extract_string_values_from_json(data)
        # Array strings are not captured, only dict values are
        check.is_in("nested: value", result)

    def test_extract_string_values_from_json_empty(self) -> None:
        """Test _extract_string_values_from_json with empty data."""
        result1 = _extract_string_values_from_json({})
        result2 = _extract_string_values_from_json([])
        result3 = _extract_string_values_from_json("")

        check.equal(result1, [])
        check.equal(result2, [])
        check.equal(result3, [])

    def test_extract_string_values_from_json_non_string_types(self) -> None:
        """Test _extract_string_values_from_json filters non-string types."""
        data = {
            "string": "valid",
            "number": 123,
            "float": 45.67,
            "bool": False,
            "null": None,
            "array_mixed": ["string_val", 789, None, True],
        }

        result = _extract_string_values_from_json(data)
        check.is_in("string: valid", result)
        # Check that non-string values are not included
        for val in result:
            check.is_instance(val, str)

    @patch("builtins.open", side_effect=OSError("File read error"))
    def test_extract_text_from_file_read_error(self, _mock_open: Mock, tmp_path: Path) -> None:
        """Test extract_text_from_file handles read errors."""
        json_file = tmp_path / "error.json"
        json_file.touch()  # Create file but reading will fail

        result = extract_text_from_file(json_file)
        check.equal(result, "")
