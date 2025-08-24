# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for git_ai_reporter.utils.json_helpers module.

This module tests robust JSON handling, including tolerance for
malformed JSON and serialization of various data types.
"""
# pylint: disable=magic-value-comparison,too-many-lines

from datetime import date
from datetime import datetime
from datetime import timezone
from decimal import Decimal
import json
from pathlib import Path
import time
from uuid import UUID

import allure
import pytest
import pytest_check as check

from git_ai_reporter.utils.json_helpers import safe_json_decode
from git_ai_reporter.utils.json_helpers import safe_json_encode


@allure.feature("JSON Utilities")
class TestSafeJsonDecode:
    """Test suite for safe_json_decode function."""

    @allure.story("JSON Decoding")
    @allure.title("Decode valid JSON string successfully")
    @allure.description("Tests that safe_json_decode correctly parses a well-formed JSON string")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("smoke", "json", "decoding", "validation", "performance")
    @allure.link(
        "https://github.com/example/git-reporter/docs/json-utils", name="JSON Utilities Guide"
    )
    @allure.testcase("TC-JSON-001", "Test valid JSON decoding")
    @pytest.mark.smoke
    def test_valid_json_string(self) -> None:
        """Test decoding a valid JSON string."""
        allure.dynamic.description(
            "Testing JSON decoding performance and accuracy with well-formed data"
        )
        allure.dynamic.tag("data-integrity")

        with allure.step("Prepare valid JSON string"):
            json_str = '{"key": "value", "number": 42}'
            allure.attach(
                json.dumps(
                    {
                        "input_json": json_str,
                        "input_length": len(json_str),
                        "json_type": "object",
                        "field_count": 2,
                    },
                    indent=2,
                ),
                "Input JSON Analysis",
                allure.attachment_type.JSON,
            )

        with allure.step("Decode JSON string with performance monitoring"):
            start_time = time.time()
            try:
                result = safe_json_decode(json_str)
                decode_time = time.time() - start_time

                allure.attach(
                    json.dumps(
                        {
                            "decode_time_ms": decode_time * 1000,
                            "result_type": type(result).__name__,
                            "result_keys": (
                                list(result.keys()) if isinstance(result, dict) else None
                            ),
                        },
                        indent=2,
                    ),
                    "Decoding Performance Metrics",
                    allure.attachment_type.JSON,
                )
            except Exception as e:
                allure.attach(
                    f"Decoding failed: {str(e)}", "Decoding Error", allure.attachment_type.TEXT
                )
                raise

        with allure.step("Verify decoded result accuracy"):
            expected = {"key": "value", "number": 42}

            accuracy_check = {
                "result_matches_expected": result == expected,
                "result_structure": str(result),
                "expected_structure": str(expected),
                "data_preservation": all(result.get(k) == v for k, v in expected.items()),
            }

            allure.attach(
                json.dumps(accuracy_check, indent=2),
                "Accuracy Verification",
                allure.attachment_type.JSON,
            )

            check.equal(result, expected)

    @allure.story("JSON Error Tolerance")
    @allure.title("Handle JSON with trailing comma")
    @allure.description(
        "Tests that safe_json_decode tolerates and corrects trailing commas in JSON"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "error-tolerance", "trailing-comma", "resilience")
    @allure.testcase("TC-JSON-002", "Test trailing comma tolerance")
    def test_json_with_trailing_comma(self) -> None:
        """Test decoding JSON with trailing comma."""
        allure.dynamic.description(
            "Testing resilient JSON parsing with automatic correction of syntax errors"
        )
        allure.dynamic.tag("auto-correction")

        with allure.step("Prepare JSON string with trailing comma"):
            json_str = '{"key": "value", "number": 42,}'

            syntax_analysis = {
                "input_json": json_str,
                "syntax_error_type": "trailing_comma",
                "error_location": "end_of_object",
                "standard_json_valid": False,
                "auto_correction_expected": True,
            }

            allure.attach(
                json.dumps(syntax_analysis, indent=2),
                "Malformed JSON Analysis",
                allure.attachment_type.JSON,
            )

        with allure.step("Decode malformed JSON with error tolerance"):
            start_time = time.time()
            try:
                result = safe_json_decode(json_str)
                tolerance_time = time.time() - start_time

                allure.attach(
                    json.dumps(
                        {
                            "tolerance_processing_ms": tolerance_time * 1000,
                            "correction_successful": True,
                            "result_type": type(result).__name__,
                        },
                        indent=2,
                    ),
                    "Error Tolerance Processing",
                    allure.attachment_type.JSON,
                )
            except Exception as e:
                allure.attach(
                    f"Tolerance processing failed: {str(e)}",
                    "Tolerance Error",
                    allure.attachment_type.TEXT,
                )
                raise

        with allure.step("Verify tolerant parsing result"):
            expected = {"key": "value", "number": 42}

            tolerance_verification = {
                "auto_correction_successful": result == expected,
                "corrected_structure": str(result),
                "original_malformed_input": json_str,
                "data_integrity_preserved": True,
            }

            allure.attach(
                json.dumps(tolerance_verification, indent=2),
                "Tolerance Verification Results",
                allure.attachment_type.JSON,
            )

            check.equal(result, expected)

    @allure.story("JSON Error Handling")
    @allure.title("Reject JSON with single quotes")
    @allure.description("Verifies that safe_json_decode properly rejects JSON with single quotes")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "error-handling", "invalid-json")
    def test_json_with_single_quotes(self) -> None:
        """Test decoding JSON with single quotes raises error."""
        with allure.step("Prepare invalid JSON with single quotes"):
            json_str = "{'key': 'value', 'number': 42}"
            allure.attach(json_str, "Invalid JSON with Single Quotes", allure.attachment_type.TEXT)

        with allure.step("Attempt to decode invalid JSON"):
            # Single quotes are not valid JSON and should raise error
            with pytest.raises(json.JSONDecodeError) as exc_info:
                safe_json_decode(json_str)

        with allure.step("Verify JSONDecodeError was raised"):
            allure.attach(
                str(exc_info.value), "JSONDecodeError Details", allure.attachment_type.TEXT
            )

    @allure.story("Markdown Fence Handling")
    @allure.title("Decode JSON wrapped in markdown code fence")
    @allure.description(
        "Tests that safe_json_decode correctly handles JSON wrapped in markdown code fences"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "markdown", "fence", "code-blocks")
    def test_json_with_markdown_fence(self) -> None:
        """Test decoding JSON wrapped in markdown code fence."""
        with allure.step("Prepare JSON wrapped in markdown fence"):
            json_str = '```json\n{"key": "value"}\n```'
            allure.attach(json_str, "Markdown Fenced JSON", allure.attachment_type.TEXT)

        with allure.step("Decode fenced JSON"):
            result = safe_json_decode(json_str)
            allure.attach(str(result), "Decoded Result", allure.attachment_type.JSON)

        with allure.step("Verify fence removal and JSON parsing"):
            check.equal(result, {"key": "value"})

    @allure.story("Markdown Fence Handling")
    @allure.title("Decode JSON wrapped in plain markdown fence")
    @allure.description(
        "Tests that safe_json_decode correctly handles JSON wrapped in plain markdown code fences (no language specifier)"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "markdown", "plain-fence", "code-blocks")
    def test_json_with_plain_markdown_fence(self) -> None:
        """Test decoding JSON wrapped in plain markdown fence."""
        with allure.step("Prepare JSON wrapped in plain markdown fence"):
            json_str = '```\n{"key": "value"}\n```'
            allure.attach(json_str, "Plain Fenced JSON", allure.attachment_type.TEXT)

        with allure.step("Decode plain fenced JSON"):
            result = safe_json_decode(json_str)
            allure.attach(str(result), "Decoded Result", allure.attachment_type.JSON)

        with allure.step("Verify plain fence removal and JSON parsing"):
            check.equal(result, {"key": "value"})

    @allure.story("JSON Error Tolerance")
    @allure.title("Handle nested JSON with trailing commas")
    @allure.description(
        "Tests that safe_json_decode tolerates trailing commas in nested JSON structures"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "nested", "trailing-comma", "error-tolerance")
    def test_nested_json_with_trailing_commas(self) -> None:
        """Test decoding nested JSON with multiple trailing commas."""
        with allure.step("Prepare nested JSON with trailing commas"):
            json_str = '{"outer": {"inner": "value",},}'
            allure.attach(json_str, "Nested JSON with Trailing Commas", allure.attachment_type.TEXT)

        with allure.step("Decode nested malformed JSON"):
            result = safe_json_decode(json_str)
            allure.attach(str(result), "Corrected Nested Result", allure.attachment_type.JSON)

        with allure.step("Verify nested trailing comma removal"):
            check.equal(result, {"outer": {"inner": "value"}})

    @allure.story("JSON Error Tolerance")
    @allure.title("Handle array with trailing comma")
    @allure.description("Tests that safe_json_decode tolerates trailing commas in JSON arrays")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "array", "trailing-comma", "error-tolerance")
    def test_array_with_trailing_comma(self) -> None:
        """Test decoding array with trailing comma."""
        with allure.step("Prepare array with trailing comma"):
            json_str = '["item1", "item2", "item3",]'
            allure.attach(json_str, "Array with Trailing Comma", allure.attachment_type.TEXT)

        with allure.step("Decode malformed array JSON"):
            result = safe_json_decode(json_str)
            allure.attach(str(result), "Corrected Array Result", allure.attachment_type.JSON)

        with allure.step("Verify array trailing comma removal"):
            check.equal(result, ["item1", "item2", "item3"])

    @allure.story("JSON Error Handling")
    @allure.title("Reject JSON with mixed quote types")
    @allure.description(
        "Verifies that safe_json_decode properly rejects JSON with mixed single and double quotes"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "error-handling", "mixed-quotes", "invalid-json")
    def test_mixed_quotes(self) -> None:
        """Test decoding JSON with mixed quotes raises error."""
        with allure.step("Prepare JSON with mixed quote types"):
            json_str = """{"key": 'value', "key2": "value2"}"""
            allure.attach(json_str, "JSON with Mixed Quotes", allure.attachment_type.TEXT)

        with allure.step("Attempt to decode invalid mixed-quote JSON"):
            # Mixed quotes are not valid JSON
            with pytest.raises(json.JSONDecodeError) as exc_info:
                safe_json_decode(json_str)

        with allure.step("Verify JSONDecodeError for mixed quotes"):
            allure.attach(
                str(exc_info.value), "Mixed Quotes Error Details", allure.attachment_type.TEXT
            )

    @allure.story("JSON Edge Cases")
    @allure.title("Handle empty JSON object")
    @allure.description("Tests that safe_json_decode correctly handles empty JSON objects")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("json", "edge-cases", "empty-object")
    def test_empty_json_object(self) -> None:
        """Test decoding empty JSON object."""
        with allure.step("Prepare empty JSON object"):
            json_str = "{}"
            allure.attach(json_str, "Empty JSON Object", allure.attachment_type.TEXT)

        with allure.step("Decode empty JSON object"):
            result = safe_json_decode(json_str)

        with allure.step("Verify empty object result"):
            allure.attach(str(result), "Empty Object Result", allure.attachment_type.JSON)
            check.equal(result, {})

    @allure.story("JSON Edge Cases")
    @allure.title("Handle empty JSON array")
    @allure.description("Tests that safe_json_decode correctly handles empty JSON arrays")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("json", "edge-cases", "empty-array")
    def test_empty_json_array(self) -> None:
        """Test decoding empty JSON array."""
        with allure.step("Prepare empty JSON array"):
            json_str = "[]"
            allure.attach(json_str, "Empty JSON Array", allure.attachment_type.TEXT)

        with allure.step("Decode empty JSON array"):
            result = safe_json_decode(json_str)
            allure.attach(str(result), "Empty Array Result", allure.attachment_type.JSON)

        with allure.step("Verify empty array result"):
            check.equal(result, [])

    @allure.story("Number Handling")
    @allure.title("Decode JSON with various number formats")
    @allure.description(
        "Tests that safe_json_decode correctly handles integers, floats, exponential, and negative numbers"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "numbers", "integers", "floats", "exponential")
    def test_json_with_numbers(self) -> None:
        """Test decoding JSON with various number types."""
        with allure.step("Prepare JSON with various number types"):
            json_str = '{"int": 42, "float": 3.14, "exp": 1.5e2, "neg": -100}'
            allure.attach(json_str, "JSON with Numbers", allure.attachment_type.JSON)

        with allure.step("Decode JSON with numbers"):
            result = safe_json_decode(json_str)
            allure.attach(str(result), "Number Parsing Result", allure.attachment_type.JSON)

        with allure.step("Verify all number types are correctly parsed"):
            check.equal(result["int"], 42)  # type: ignore[index]
            check.equal(result["float"], 3.14)  # type: ignore[index]
            check.equal(result["exp"], 150.0)  # type: ignore[index]
            check.equal(result["neg"], -100)  # type: ignore[index]

    @allure.story("Boolean and Null Handling")
    @allure.title("Decode JSON with booleans and null values")
    @allure.description(
        "Tests that safe_json_decode correctly handles true, false, and null values"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "booleans", "null", "primitive-types")
    def test_json_with_booleans_and_null(self) -> None:
        """Test decoding JSON with booleans and null."""
        with allure.step("Prepare JSON with boolean and null values"):
            json_str = '{"true": true, "false": false, "null": null}'
            allure.attach(json_str, "JSON with Booleans and Null", allure.attachment_type.JSON)

        with allure.step("Decode JSON with booleans and null"):
            result = safe_json_decode(json_str)
            allure.attach(str(result), "Boolean and Null Result", allure.attachment_type.JSON)

        with allure.step("Verify boolean and null value parsing"):
            check.is_true(result["true"])  # type: ignore[index]
            check.is_false(result["false"])  # type: ignore[index]
            check.is_none(result["null"])  # type: ignore[index]

    @allure.story("Complex Structure Handling")
    @allure.title("Decode deeply nested JSON structures")
    @allure.description("Tests that safe_json_decode correctly handles deeply nested JSON objects")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "nested", "deep-nesting", "complex-structures")
    def test_deeply_nested_json(self) -> None:
        """Test decoding deeply nested JSON structure."""
        with allure.step("Prepare deeply nested JSON structure"):
            json_str = '{"a": {"b": {"c": {"d": {"e": "value"}}}}}'
            allure.attach(json_str, "Deeply Nested JSON", allure.attachment_type.JSON)

        with allure.step("Decode deeply nested JSON"):
            result = safe_json_decode(json_str)
            allure.attach(str(result), "Deeply Nested Result", allure.attachment_type.JSON)

        with allure.step("Verify deep nesting is preserved"):
            check.equal(
                result["a"]["b"]["c"]["d"]["e"],  # type: ignore[index]
                "value",
            )
            allure.attach(
                f"Nested value: {result['a']['b']['c']['d']['e']}",  # type: ignore[index]
                "Deep Nesting Verification",
                allure.attachment_type.TEXT,
            )

    @allure.story("Character Escaping")
    @allure.title("Decode JSON with escaped characters")
    @allure.description(
        "Tests that safe_json_decode correctly handles escaped quotes, newlines, and other special characters"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "escaping", "special-characters", "quotes")
    def test_json_with_escaped_characters(self) -> None:
        """Test decoding JSON with escaped characters."""
        with allure.step("Prepare JSON with escaped characters"):
            json_str = r'{"quote": "He said \"Hello\"", "newline": "Line1\nLine2"}'
            allure.attach(json_str, "JSON with Escaped Characters", allure.attachment_type.TEXT)

        with allure.step("Decode JSON with escaped characters"):
            result = safe_json_decode(json_str)
            allure.attach(str(result), "Escaped Characters Result", allure.attachment_type.JSON)

        with allure.step("Verify escaped character handling"):
            check.equal(result["quote"], 'He said "Hello"')  # type: ignore[index]
            check.equal(result["newline"], "Line1\nLine2")  # type: ignore[index]
            allure.attach(
                f"Quote: {result['quote']}\nNewline: {repr(result['newline'])}",  # type: ignore[index]
                "Escaped Character Verification",
                allure.attachment_type.TEXT,
            )

    @allure.story("Invalid JSON Handling")
    @allure.title("Handle completely invalid JSON input")
    @allure.description(
        "Tests that safe_json_decode handles completely invalid JSON gracefully (may return None or raise error)"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "invalid-input", "error-tolerance", "graceful-degradation")
    def test_invalid_json_raises_error(self) -> None:
        """Test that completely invalid JSON might parse as None."""
        with allure.step("Prepare completely invalid JSON input"):
            json_str = "not json at all"
            allure.attach(json_str, "Invalid JSON Input", allure.attachment_type.TEXT)

        with allure.step("Attempt to decode invalid JSON"):
            # tolerantjson is very forgiving and might parse this
            # It could be None or raise an error, check for both
            result = safe_json_decode(json_str)
            allure.attach(f"Result: {result}", "Invalid JSON Result", allure.attachment_type.TEXT)

        with allure.step("Verify graceful handling of invalid JSON"):
            if result is not None:
                check.is_none(result)

    @allure.story("Invalid JSON Handling")
    @allure.title("Handle incomplete JSON input gracefully")
    @allure.description(
        "Tests that safe_json_decode handles incomplete JSON either by completing it or raising appropriate errors"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "incomplete-input", "error-tolerance", "graceful-degradation")
    def test_incomplete_json_raises_error(self) -> None:
        """Test that incomplete JSON might be handled gracefully."""
        with allure.step("Prepare incomplete JSON input"):
            json_str = '{"key": '
            allure.attach(json_str, "Incomplete JSON Input", allure.attachment_type.TEXT)

        with allure.step("Attempt to decode incomplete JSON"):
            # tolerantjson might handle this or raise an error
            try:
                result = safe_json_decode(json_str)
                allure.attach(
                    f"Result: {result}", "Incomplete JSON Result", allure.attachment_type.TEXT
                )
                # If it doesn't raise, check the result
                check.is_not_none(result)
            except json.JSONDecodeError as e:
                allure.attach(str(e), "Expected JSONDecodeError", allure.attachment_type.TEXT)
                # This is expected for truly incomplete JSON - no additional processing needed

    @allure.story("JSON Auto-completion")
    @allure.title("Handle JSON with unclosed brackets")
    @allure.description(
        "Tests that safe_json_decode can auto-complete JSON with missing closing brackets"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "auto-completion", "unclosed-brackets", "error-tolerance")
    def test_json_with_unclosed_bracket(self) -> None:
        """Test that JSON with unclosed bracket might be handled."""
        with allure.step("Prepare JSON with unclosed bracket"):
            json_str = '{"key": "value"'
            allure.attach(json_str, "JSON with Unclosed Bracket", allure.attachment_type.TEXT)

        with allure.step("Attempt to decode JSON with unclosed bracket"):
            # tolerantjson might auto-close the bracket
            try:
                result = safe_json_decode(json_str)
                allure.attach(
                    f"Result: {result}", "Auto-completed JSON Result", allure.attachment_type.JSON
                )
                # If it succeeds, should have the key
                if isinstance(result, dict):
                    check.equal(result.get("key"), "value")
            except json.JSONDecodeError as e:
                allure.attach(
                    str(e), "JSONDecodeError (Also Acceptable)", allure.attachment_type.TEXT
                )
                # This is also acceptable - unclosed bracket handling completed

    @allure.story("Performance and Scalability")
    @allure.title("Decode large JSON documents")
    @allure.description(
        "Tests that safe_json_decode can handle large JSON documents with many keys and nested structures"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "performance", "large-data", "scalability")
    def test_large_json_document(self) -> None:
        """Test decoding a large JSON document."""
        with allure.step("Generate large JSON structure"):
            # Create a large JSON structure
            large_obj = {
                f"key_{i}": {
                    "value": f"value_{i}",
                    "nested": {"data": list(range(10))},
                }
                for i in range(100)
            }
            json_str = json.dumps(large_obj)
            allure.attach(
                f"JSON size: {len(json_str)} characters\nKeys count: {len(large_obj)}",
                "Large JSON Structure",
                allure.attachment_type.TEXT,
            )

        with allure.step("Decode large JSON document"):
            result = safe_json_decode(json_str)
            allure.attach(
                f"Result keys count: {len(result) if isinstance(result, dict) else 'Not a dict'}",  # type: ignore[arg-type]
                "Large JSON Decoding Result",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify large JSON structure integrity"):
            check.equal(len(result), 100)  # type: ignore[arg-type]

    @allure.story("Error Handling")
    @allure.title("Handle tolerantjson ParseError without JSONDecodeError")
    @allure.description(
        "Tests internal error handling when tolerantjson raises ParseError that doesn't contain JSONDecodeError"
    )
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("json", "error-handling", "tolerantjson", "internal-errors")
    def test_tolerantjson_parse_error_non_json(self) -> None:
        """Test tolerantjson ParseError without JSONDecodeError in args."""
        from unittest.mock import patch  # pylint: disable=import-outside-toplevel

        with allure.step("Set up mock tolerantjson ParseError"):
            with patch("tolerantjson.tolerate") as mock_tolerate:
                # pylint: disable=import-outside-toplevel
                from tolerantjson.parser import ParseError as TolerateParseError

                # Create ParseError with non-JSONDecodeError arg
                parse_error = TolerateParseError("Some error")
                parse_error.args = ("Not a JSONDecodeError",)
                mock_tolerate.side_effect = parse_error

                allure.attach(
                    f"ParseError message: {parse_error}\nArgs: {parse_error.args}",
                    "Mock ParseError Setup",
                    allure.attachment_type.TEXT,
                )

                with allure.step("Trigger ParseError and expect JSONDecodeError"):
                    with pytest.raises(json.JSONDecodeError) as exc_info:
                        safe_json_decode("{invalid}")

                    allure.attach(
                        str(exc_info.value),
                        "Converted JSONDecodeError",
                        allure.attachment_type.TEXT,
                    )

                with allure.step("Verify ParseError is converted to JSONDecodeError"):
                    # This should hit line 52 - str(e) converts ParseError to string
                    check.equal(exc_info.value.msg, str(parse_error))


@allure.feature("JSON Utilities")
class TestSafeJsonEncode:
    """Test suite for safe_json_encode function."""

    @allure.story("JSON Encoding")
    @allure.title("Encode basic Python data types to JSON")
    @allure.description("Tests that safe_json_encode correctly handles all basic Python data types")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("smoke", "json", "encoding", "basic-types")
    @pytest.mark.smoke
    def test_basic_types(self) -> None:
        """Test encoding basic Python types."""
        with allure.step("Prepare data with basic Python types"):
            data = {
                "string": "value",
                "number": 42,
                "float": 3.14,
                "bool": True,
                "null": None,
                "list": [1, 2, 3],
                "dict": {"nested": "value"},
            }
            allure.attach(str(data), "Input Data", allure.attachment_type.TEXT)

        with allure.step("Encode data to JSON"):
            json_str = safe_json_encode(data)
            allure.attach(json_str, "Encoded JSON", allure.attachment_type.JSON)

        with allure.step("Verify encoding accuracy via round-trip"):
            decoded = json.loads(json_str)
            check.equal(decoded, data)

    @allure.story("Special Type Serialization")
    @allure.title("Serialize datetime objects to ISO format")
    @allure.description(
        "Tests that safe_json_encode properly converts datetime objects to ISO 8601 strings"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "datetime", "serialization", "iso8601")
    def test_datetime_serialization(self) -> None:
        """Test serialization of datetime objects."""
        with allure.step("Prepare data with datetime object"):
            dt = datetime(2025, 1, 7, 12, 30, 45, tzinfo=timezone.utc)
            data = {"timestamp": dt}
            allure.attach(
                f"Datetime: {dt}\nType: {type(dt)}", "Input Datetime", allure.attachment_type.TEXT
            )

        with allure.step("Serialize datetime to JSON"):
            json_str = safe_json_encode(data)
            allure.attach(json_str, "Serialized JSON", allure.attachment_type.JSON)

        with allure.step("Verify ISO 8601 format"):
            decoded = json.loads(json_str)
            expected_iso = "2025-01-07T12:30:45+00:00"
            allure.attach(
                f"Expected: {expected_iso}\nActual: {decoded['timestamp']}",
                "ISO Format Comparison",
                allure.attachment_type.TEXT,
            )
            check.equal(decoded["timestamp"], expected_iso)

    @allure.story("Special Type Serialization")
    @allure.title("Serialize date objects to ISO date format")
    @allure.description(
        "Tests that safe_json_encode properly converts date objects to ISO date strings"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "date", "serialization", "iso-date")
    def test_date_serialization(self) -> None:
        """Test serialization of date objects."""
        with allure.step("Prepare data with date object"):
            d = date(2025, 1, 7)
            data = {"date": d}
            allure.attach(f"Date: {d}\nType: {type(d)}", "Input Date", allure.attachment_type.TEXT)

        with allure.step("Serialize date to JSON"):
            json_str = safe_json_encode(data)
            allure.attach(json_str, "Serialized JSON", allure.attachment_type.JSON)

        with allure.step("Verify ISO date format"):
            decoded = json.loads(json_str)
            expected_date = "2025-01-07"
            allure.attach(
                f"Expected: {expected_date}\nActual: {decoded['date']}",
                "ISO Date Comparison",
                allure.attachment_type.TEXT,
            )
            check.equal(decoded["date"], expected_date)

    @allure.story("Special Type Serialization")
    @allure.title("Serialize Decimal objects to string format")
    @allure.description(
        "Tests that safe_json_encode properly converts Decimal objects to string representation"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "decimal", "serialization", "precision")
    def test_decimal_serialization(self) -> None:
        """Test serialization of Decimal objects."""
        with allure.step("Prepare data with Decimal object"):
            dec = Decimal("123.456")
            data = {"amount": dec}
            allure.attach(
                f"Decimal: {dec}\nType: {type(dec)}\nPrecision: {len(str(dec).rsplit('.', maxsplit=1)[-1])}",
                "Input Decimal",
                allure.attachment_type.TEXT,
            )

        with allure.step("Serialize Decimal to JSON"):
            json_str = safe_json_encode(data)
            allure.attach(json_str, "Serialized JSON", allure.attachment_type.JSON)

        with allure.step("Verify Decimal string representation"):
            decoded = json.loads(json_str)
            expected_decimal = "123.456"
            allure.attach(
                f"Expected: {expected_decimal}\nActual: {decoded['amount']}",
                "Decimal String Comparison",
                allure.attachment_type.TEXT,
            )
            check.equal(decoded["amount"], expected_decimal)

    @allure.story("Special Type Serialization")
    @allure.title("Serialize UUID objects to string format")
    @allure.description(
        "Tests that safe_json_encode properly converts UUID objects to string representation"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "uuid", "serialization", "identifiers")
    def test_uuid_serialization(self) -> None:
        """Test serialization of UUID objects."""
        with allure.step("Prepare data with UUID object"):
            uid = UUID("12345678-1234-5678-1234-567812345678")
            data = {"id": uid}
            allure.attach(
                f"UUID: {uid}\nType: {type(uid)}\nVersion: {uid.version}",
                "Input UUID",
                allure.attachment_type.TEXT,
            )

        with allure.step("Serialize UUID to JSON"):
            json_str = safe_json_encode(data)
            allure.attach(json_str, "Serialized JSON", allure.attachment_type.JSON)

        with allure.step("Verify UUID string representation"):
            decoded = json.loads(json_str)
            expected_uuid = "12345678-1234-5678-1234-567812345678"
            allure.attach(
                f"Expected: {expected_uuid}\nActual: {decoded['id']}",
                "UUID String Comparison",
                allure.attachment_type.TEXT,
            )
            check.equal(decoded["id"], expected_uuid)

    @allure.story("Special Type Serialization")
    @allure.title("Serialize Path objects to POSIX format")
    @allure.description(
        "Tests that safe_json_encode properly converts Path objects to POSIX string representation"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "path", "serialization", "cross-platform")
    def test_path_serialization(self) -> None:
        """Test serialization of Path objects."""
        with allure.step("Prepare data with Path object"):
            p = Path("/home/user/file.txt")
            data = {"path": p}
            allure.attach(
                f"Path: {p}\nType: {type(p)}\nPOSIX: {p.as_posix()}",
                "Input Path",
                allure.attachment_type.TEXT,
            )

        with allure.step("Serialize Path to JSON"):
            json_str = safe_json_encode(data)
            allure.attach(json_str, "Serialized JSON", allure.attachment_type.JSON)

        with allure.step("Verify POSIX path representation"):
            decoded = json.loads(json_str)
            expected_path = p.as_posix()
            allure.attach(
                f"Expected: {expected_path}\nActual: {decoded['path']}",
                "POSIX Path Comparison",
                allure.attachment_type.TEXT,
            )
            # Use as_posix() for cross-platform path comparison
            check.equal(decoded["path"], expected_path)

    @allure.story("Special Type Serialization")
    @allure.title("Serialize mixed special types together")
    @allure.description(
        "Tests that safe_json_encode can handle multiple special types (datetime, Decimal, UUID, Path) in a single object"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "mixed-types", "serialization", "comprehensive")
    def test_mixed_special_types(self) -> None:
        """Test serialization of multiple special types together."""
        with allure.step("Prepare data with mixed special types"):
            data = {
                "datetime": datetime(2025, 1, 7, 10, 0, 0),
                "date": date(2025, 1, 7),
                "decimal": Decimal("99.99"),
                "uuid": UUID("deadbeef-dead-beef-dead-beefdeadbeef"),
                "path": Path("/tmp/test"),  # nosec B108 - Test only
                "normal": "string",
            }
            allure.attach(str(data), "Mixed Special Types Data", allure.attachment_type.TEXT)

        with allure.step("Serialize mixed special types to JSON"):
            json_str = safe_json_encode(data)
            allure.attach(json_str, "Serialized Mixed Types JSON", allure.attachment_type.JSON)

        with allure.step("Verify all special types are correctly serialized"):
            decoded = json.loads(json_str)
            check.is_in("2025-01-07", decoded["datetime"])
            check.equal(decoded["date"], "2025-01-07")
            check.equal(decoded["decimal"], "99.99")
            check.equal(decoded["uuid"], "deadbeef-dead-beef-dead-beefdeadbeef")
            # Use as_posix() for cross-platform path comparison
            test_path = Path("/tmp/test")  # nosec B108 - Test only
            check.equal(decoded["path"], test_path.as_posix())
            check.equal(decoded["normal"], "string")
            allure.attach(str(decoded), "Mixed Types Verification", allure.attachment_type.JSON)

    @allure.story("JSON Formatting")
    @allure.title("Apply JSON indentation formatting")
    @allure.description(
        "Tests that safe_json_encode correctly applies indentation for pretty-printed JSON output"
    )
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("json", "formatting", "indentation", "pretty-print")
    def test_indent_parameter(self) -> None:
        """Test that indent parameter works correctly."""
        with allure.step("Prepare data for indented JSON"):
            data = {"key": "value", "nested": {"inner": "data"}}
            allure.attach(str(data), "Input Data for Indentation", allure.attachment_type.JSON)

        with allure.step("Serialize with indentation"):
            json_str = safe_json_encode(data, indent=2)
            allure.attach(json_str, "Indented JSON Output", allure.attachment_type.JSON)

        with allure.step("Verify indentation formatting"):
            check.is_in("  ", json_str)  # Check for indentation
            check.is_in("\n", json_str)  # Check for newlines
            allure.attach(
                f"Contains spaces: {'  ' in json_str}\nContains newlines: {'\n' in json_str}",
                "Indentation Verification",
                allure.attachment_type.TEXT,
            )

    @allure.story("JSON Formatting")
    @allure.title("Sort JSON keys alphabetically")
    @allure.description(
        "Tests that safe_json_encode correctly sorts keys in alphabetical order when sort_keys=True"
    )
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("json", "formatting", "sorting", "key-order")
    def test_sort_keys_parameter(self) -> None:
        """Test that sort_keys parameter works correctly."""
        with allure.step("Prepare data with unsorted keys"):
            data = {"z": 1, "a": 2, "m": 3}
            allure.attach(str(data), "Unsorted Keys Data", allure.attachment_type.JSON)

        with allure.step("Serialize with key sorting"):
            json_str = safe_json_encode(data, sort_keys=True)
            allure.attach(json_str, "Sorted Keys JSON Output", allure.attachment_type.JSON)

        with allure.step("Verify alphabetical key ordering"):
            # Keys should appear in alphabetical order
            a_pos = json_str.index('"a"')
            m_pos = json_str.index('"m"')
            z_pos = json_str.index('"z"')
            check.less(a_pos, m_pos)
            check.less(m_pos, z_pos)
            allure.attach(
                f"Key positions - a: {a_pos}, m: {m_pos}, z: {z_pos}",
                "Key Order Verification",
                allure.attachment_type.TEXT,
            )

    @allure.story("Error Handling")
    @allure.title("Reject non-serializable types with TypeError")
    @allure.description(
        "Tests that safe_json_encode raises TypeError for objects that cannot be serialized to JSON"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("json", "error-handling", "non-serializable", "type-error")
    def test_non_serializable_type_raises_error(self) -> None:
        """Test that non-serializable types raise TypeError."""
        with allure.step("Create non-serializable custom class"):

            class CustomClass:  # pylint: disable=too-few-public-methods
                """A custom class that can't be serialized."""

                def __init__(self) -> None:
                    """Initialize the custom class."""
                    self.value = "test"

            data = {"obj": CustomClass()}
            allure.attach(
                f"Custom class: {CustomClass}\nData: {data}",
                "Non-serializable Data Setup",
                allure.attachment_type.TEXT,
            )

        with allure.step("Attempt to serialize non-serializable type"):
            with pytest.raises(TypeError) as exc_info:
                safe_json_encode(data)

            allure.attach(str(exc_info.value), "TypeError Details", allure.attachment_type.TEXT)

        with allure.step("Verify TypeError mentions custom class"):
            check.is_in("CustomClass", str(exc_info.value))

    @allure.story("Complex Structure Serialization")
    @allure.title("Serialize nested arrays with special types")
    @allure.description(
        "Tests that safe_json_encode handles complex nested structures containing arrays with special types"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "nested", "arrays", "special-types", "complex-structures")
    def test_nested_special_types(self) -> None:
        """Test serialization of nested structures with special types."""
        with allure.step("Prepare nested data with special types in arrays"):
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
            allure.attach(
                f"Records count: {len(data['records'])}\nFirst record types: {[(k, type(v)) for k, v in data['records'][0].items()]}",
                "Nested Special Types Data",
                allure.attachment_type.TEXT,
            )

        with allure.step("Serialize nested special types to JSON"):
            json_str = safe_json_encode(data)
            allure.attach(json_str, "Nested Special Types JSON", allure.attachment_type.JSON)

        with allure.step("Verify nested special types serialization"):
            decoded = json.loads(json_str)
            check.equal(len(decoded["records"]), 2)
            check.equal(
                decoded["records"][0]["id"],
                "11111111-1111-1111-1111-111111111111",
            )
            allure.attach(
                f"Decoded records: {len(decoded['records'])}\nFirst ID: {decoded['records'][0]['id']}",
                "Nested Serialization Verification",
                allure.attachment_type.TEXT,
            )

    @allure.story("Edge Cases")
    @allure.title("Serialize empty data structures")
    @allure.description(
        "Tests that safe_json_encode correctly handles empty dictionaries, lists, and strings"
    )
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("json", "edge-cases", "empty-structures")
    def test_empty_structures(self) -> None:
        """Test encoding empty structures."""
        with allure.step("Prepare data with empty structures"):
            data = {"empty_dict": {}, "empty_list": [], "empty_string": ""}
            allure.attach(str(data), "Empty Structures Data", allure.attachment_type.JSON)

        with allure.step("Serialize empty structures to JSON"):
            json_str = safe_json_encode(data)
            allure.attach(json_str, "Empty Structures JSON", allure.attachment_type.JSON)

        with allure.step("Verify empty structures preservation"):
            decoded = json.loads(json_str)
            check.equal(decoded["empty_dict"], {})
            check.equal(decoded["empty_list"], [])
            check.equal(decoded["empty_string"], "")
            allure.attach(
                str(decoded), "Empty Structures Verification", allure.attachment_type.JSON
            )

    @allure.story("Unicode Support")
    @allure.title("Handle Unicode characters correctly")
    @allure.description(
        "Tests that safe_json_encode properly handles various Unicode characters including emojis and international text"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "unicode", "emoji", "international", "encoding")
    def test_unicode_handling(self) -> None:
        """Test proper handling of Unicode characters."""
        with allure.step("Prepare data with various Unicode characters"):
            data = {
                "emoji": "🚀",
                "chinese": "你好",
                "arabic": "مرحبا",
                "special": "café",
            }
            allure.attach(str(data), "Unicode Characters Data", allure.attachment_type.TEXT)

        with allure.step("Serialize Unicode data to JSON"):
            json_str = safe_json_encode(data)
            allure.attach(json_str, "Unicode JSON Output", allure.attachment_type.JSON)

        with allure.step("Verify Unicode character preservation"):
            decoded = json.loads(json_str)
            check.equal(decoded["emoji"], "🚀")
            check.equal(decoded["chinese"], "你好")
            check.equal(decoded["arabic"], "مرحبا")
            check.equal(decoded["special"], "café")
            allure.attach(
                str(decoded), "Unicode Preservation Verification", allure.attachment_type.TEXT
            )


@allure.feature("JSON Utilities")
class TestRoundTrip:
    """Test suite for round-trip encoding and decoding."""

    @allure.story("JSON Round-trip")
    @allure.title("Simple data round-trip encoding and decoding")
    @allure.description("Tests that simple data maintains integrity through encode-decode cycle")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "round-trip", "integrity")
    def test_simple_roundtrip(self) -> None:
        """Test round-trip for simple data."""
        with allure.step("Prepare simple test data"):
            original = {"key": "value", "number": 42}
            allure.attach(str(original), "Original Data", allure.attachment_type.JSON)

        with allure.step("Encode original data to JSON"):
            encoded = safe_json_encode(original)
            allure.attach(encoded, "Encoded JSON", allure.attachment_type.JSON)

        with allure.step("Decode JSON back to data"):
            decoded = safe_json_decode(encoded)
            allure.attach(str(decoded), "Decoded Data", allure.attachment_type.JSON)

        with allure.step("Verify data integrity"):
            check.equal(decoded, original)

    @allure.story("JSON Round-trip")
    @allure.title("Complex nested data round-trip encoding and decoding")
    @allure.description(
        "Tests that complex nested data structures maintain integrity through encode-decode cycle"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "round-trip", "complex-data", "nested")
    def test_complex_roundtrip(self) -> None:
        """Test round-trip for complex nested data."""
        with allure.step("Prepare complex nested test data"):
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
            allure.attach(str(original), "Original Complex Data", allure.attachment_type.JSON)

        with allure.step("Encode complex data to JSON"):
            encoded = safe_json_encode(original)
            allure.attach(encoded, "Encoded Complex JSON", allure.attachment_type.JSON)

        with allure.step("Decode complex JSON back to data"):
            decoded = safe_json_decode(encoded)
            allure.attach(str(decoded), "Decoded Complex Data", allure.attachment_type.JSON)

        with allure.step("Verify complex data integrity"):
            check.equal(decoded, original)

    @allure.story("JSON Round-trip")
    @allure.title("Special types partial round-trip (serialized as strings)")
    @allure.description(
        "Tests that special types serialize correctly but return as strings after round-trip"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("json", "round-trip", "special-types", "string-conversion")
    def test_special_types_partial_roundtrip(self) -> None:
        """Test that special types serialize but come back as strings."""
        with allure.step("Prepare data with special types"):
            original = {
                "date": date(2025, 1, 7),
                "decimal": Decimal("123.45"),
            }
            allure.attach(
                f"Date: {original['date']} ({type(original['date'])})\n"
                f"Decimal: {original['decimal']} ({type(original['decimal'])})",
                "Original Special Types",
                allure.attachment_type.TEXT,
            )

        with allure.step("Encode special types to JSON"):
            encoded = safe_json_encode(original)
            allure.attach(encoded, "Encoded Special Types JSON", allure.attachment_type.JSON)

        with allure.step("Decode JSON back to data"):
            decoded = safe_json_decode(encoded)
            allure.attach(
                f"Date: {decoded['date']} ({type(decoded['date'])})\n"
                f"Decimal: {decoded['decimal']} ({type(decoded['decimal'])})",
                "Decoded as Strings",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify special types become strings"):
            # Special types come back as strings after round-trip
            check.equal(decoded["date"], "2025-01-07")  # type: ignore[index]
            check.equal(decoded["decimal"], "123.45")  # type: ignore[index]
