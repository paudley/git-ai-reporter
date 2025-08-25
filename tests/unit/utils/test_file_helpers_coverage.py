# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Additional unit tests for file_helpers module to improve coverage."""

import json
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import allure
import pytest_check as check

from git_ai_reporter.utils.file_helpers import (
    _extract_string_values_from_json,
)  # pylint: disable=import-private-name
from git_ai_reporter.utils.file_helpers import extract_text_from_file


@allure.epic("Test Coverage")
@allure.feature("File Helpers Coverage")
@allure.story("Text Extraction Operations")
class TestFileHelpers:
    """Test suite for file_helpers functions to improve coverage."""

    @allure.title("Extract text from JSON file")
    @allure.description(
        "Tests text extraction from JSON files by parsing and extracting string values"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("file-io", "coverage", "json", "text-extraction")
    def test_extract_text_from_file_json(self, tmp_path: Path) -> None:
        """Test extract_text_from_file with JSON file."""
        with allure.step("Create test JSON file with nested data"):
            json_file = tmp_path / "test.json"
            json_data = {"key": "value", "nested": {"data": "content"}}
            json_file.write_text(json.dumps(json_data))

        with allure.step("Extract text from JSON file"):
            result = extract_text_from_file(json_file)

        with allure.step("Verify extracted text contains expected values"):
            check.is_in("value", result)
            check.is_in("content", result)

    @allure.title("Extract text from markdown file")
    @allure.description(
        "Tests text extraction from markdown files by reading content as plain text"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("file-io", "coverage", "markdown", "text-extraction")
    def test_extract_text_from_file_markdown(self, tmp_path: Path) -> None:
        """Test extract_text_from_file with markdown file."""
        with allure.step("Create test markdown file with formatted content"):
            md_file = tmp_path / "test.md"
            md_content = "# Header\n\nThis is **bold** text with [link](http://example.com)."
            md_file.write_text(md_content)

        with allure.step("Extract text from markdown file"):
            result = extract_text_from_file(md_file)

        with allure.step("Verify extracted text contains expected content"):
            check.is_in("Header", result)
            check.is_in("bold", result)

    @allure.title("Handle nonexistent file gracefully")
    @allure.description(
        "Tests that extract_text_from_file returns empty string for nonexistent files"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("file-io", "coverage", "error-handling", "nonexistent-file")
    def test_extract_text_from_file_nonexistent(self, tmp_path: Path) -> None:
        """Test extract_text_from_file with nonexistent file."""
        with allure.step("Define path to nonexistent file"):
            nonexistent = tmp_path / "nonexistent.txt"

        with allure.step("Attempt to extract text from nonexistent file"):
            result = extract_text_from_file(nonexistent)

        with allure.step("Verify empty string is returned"):
            check.equal(result, "")

    @allure.title("Handle unsupported file types")
    @allure.description(
        "Tests that extract_text_from_file returns content as-is for unsupported file types"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("file-io", "coverage", "unsupported-type", "plain-text")
    def test_extract_text_from_file_unsupported_type(self, tmp_path: Path) -> None:
        """Test extract_text_from_file with unsupported file type."""
        with allure.step("Create plain text file"):
            txt_file = tmp_path / "test.txt"
            content = "Plain text content"
            txt_file.write_text(content)

        with allure.step("Extract text from plain text file"):
            result = extract_text_from_file(txt_file)

        with allure.step("Verify content is returned as-is"):
            check.equal(result, content)  # Returns content as-is for unsupported types

    @allure.title("Handle invalid JSON gracefully")
    @allure.description(
        "Tests that extract_text_from_file falls back to plain text for invalid JSON"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("file-io", "coverage", "json", "error-handling", "fallback")
    def test_extract_text_from_file_invalid_json(self, tmp_path: Path) -> None:
        """Test extract_text_from_file with invalid JSON."""
        with allure.step("Create file with invalid JSON content"):
            json_file = tmp_path / "invalid.json"
            invalid_content = "{invalid json}"
            json_file.write_text(invalid_content)

        with allure.step("Extract text from invalid JSON file"):
            result = extract_text_from_file(json_file)

        with allure.step("Verify fallback to plain text content"):
            check.equal(result, invalid_content)  # Falls back to plain text

    @allure.title("Extract string values from simple JSON data")
    @allure.description("Tests extraction of string key-value pairs from simple JSON structure")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("json", "coverage", "string-extraction", "simple-data")
    def test_extract_string_values_from_json_simple(self) -> None:
        """Test _extract_string_values_from_json with simple data."""
        with allure.step("Create simple JSON data with mixed types"):
            data = {"key": "value", "number": 42, "bool": True}

        with allure.step("Extract string values from JSON data"):
            result = _extract_string_values_from_json(data)

        with allure.step("Verify only string values are extracted"):
            check.is_in("key: value", result)
            check.equal(len(result), 1)  # Only the string value should be included

    @allure.title("Extract string values from nested JSON data")
    @allure.description("Tests extraction of string values from complex nested JSON structures")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("json", "coverage", "string-extraction", "nested-data")
    def test_extract_string_values_from_json_nested(self) -> None:
        """Test _extract_string_values_from_json with nested data."""
        with allure.step("Create nested JSON data with multiple levels"):
            data = {
                "level1": {"level2": {"text": "nested value", "array": ["item1", "item2", 123]}},
                "top_level": "top value",
            }

        with allure.step("Extract string values from nested JSON data"):
            result = _extract_string_values_from_json(data)

        with allure.step("Verify both nested and top-level strings are extracted"):
            check.is_in("text: nested value", result)
            check.is_in("top_level: top value", result)
            # Array strings are not formatted as key:value but the function doesn't handle arrays of strings

    @allure.title("Extract string values from array JSON data")
    @allure.description("Tests extraction behavior with array data containing mixed types")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "coverage", "string-extraction", "array-data")
    def test_extract_string_values_from_json_array(self) -> None:
        """Test _extract_string_values_from_json with array data."""
        with allure.step("Create array data with mixed types including nested dict"):
            data = ["string1", "string2", 42, True, {"nested": "value"}]

        with allure.step("Extract string values from array JSON data"):
            result = _extract_string_values_from_json(data)

        with allure.step("Verify only dict values are captured, not array strings"):
            # Array strings are not captured, only dict values are
            check.is_in("nested: value", result)

    @allure.title("Handle empty JSON data structures")
    @allure.description("Tests extraction behavior with various empty data structures")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "coverage", "string-extraction", "empty-data", "edge-cases")
    def test_extract_string_values_from_json_empty(self) -> None:
        """Test _extract_string_values_from_json with empty data."""
        with allure.step("Extract from empty dict, list, and string"):
            result1 = _extract_string_values_from_json({})
            result2 = _extract_string_values_from_json([])
            result3 = _extract_string_values_from_json("")

        with allure.step("Verify all return empty lists"):
            check.equal(result1, [])
            check.equal(result2, [])
            check.equal(result3, [])

    @allure.title("Filter non-string types from JSON data")
    @allure.description(
        "Tests that only string values are extracted and non-string types are filtered out"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("json", "coverage", "string-extraction", "type-filtering")
    def test_extract_string_values_from_json_non_string_types(self) -> None:
        """Test _extract_string_values_from_json filters non-string types."""
        with allure.step("Create JSON data with various data types"):
            data = {
                "string": "valid",
                "number": 123,
                "float": 45.67,
                "bool": False,
                "null": None,
                "array_mixed": ["string_val", 789, None, True],
            }

        with allure.step("Extract string values from mixed-type JSON data"):
            result = _extract_string_values_from_json(data)

        with allure.step("Verify only string values are included"):
            check.is_in("string: valid", result)
            # Check that non-string values are not included
            for val in result:
                check.is_instance(val, str)

    @allure.title("Handle file read errors gracefully")
    @allure.description(
        "Tests that extract_text_from_file returns empty string when file read fails"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("file-io", "coverage", "error-handling", "read-error")
    @patch("builtins.open", side_effect=OSError("File read error"))
    def test_extract_text_from_file_read_error(self, _mock_open: Mock, tmp_path: Path) -> None:
        """Test extract_text_from_file handles read errors."""
        with allure.step("Create file that will fail on read attempt"):
            json_file = tmp_path / "error.json"
            json_file.touch()  # Create file but reading will fail

        with allure.step("Attempt to extract text from problematic file"):
            result = extract_text_from_file(json_file)

        with allure.step("Verify empty string is returned on read error"):
            check.equal(result, "")
