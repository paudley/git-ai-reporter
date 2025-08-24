# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for git_ai_reporter.utils.file_helpers module.

This module tests file processing and text extraction utilities.
"""

import json
import logging
from pathlib import Path
from unittest.mock import patch

import allure
import pytest
import pytest_check as check

from git_ai_reporter.utils.file_helpers import extract_text_from_file


@allure.feature("File Processing Utilities")
class TestExtractTextFromFile:
    """Test suite for extract_text_from_file function."""

    @allure.story("Text Extraction")
    @allure.title("Extract text from plain text file")
    @allure.description("Tests that plain text files are read correctly with all content preserved")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("file-processing", "text-extraction", "plain-text")
    def test_extract_text_from_plain_text_file(self, temp_dir: Path) -> None:
        """Test extracting text from a plain text file."""
        with allure.step("Create plain text file with multi-line content"):
            file_path = temp_dir / "test.txt"
            content = "This is plain text content.\nWith multiple lines."
            file_path.write_text(content)
            allure.attach(content, "Original Text Content", allure.attachment_type.TEXT)

        with allure.step("Extract text from plain text file"):
            result = extract_text_from_file(file_path)

        with allure.step("Verify extracted content matches original"):
            allure.attach(result, "Extracted Text Content", allure.attachment_type.TEXT)
            check.equal(result, content)

    @allure.story("JSON Processing")
    @allure.title("Extract structured text from JSON file")
    @allure.description(
        "Tests that JSON files are parsed and converted to human-readable text format"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("file-processing", "json", "structured-data")
    def test_extract_text_from_json_file(self, temp_dir: Path) -> None:
        """Test extracting text from a JSON file."""
        with allure.step("Create JSON file with nested structure"):
            file_path = temp_dir / "test.json"
            data = {
                "name": "John Doe",
                "age": 30,
                "address": {"street": "123 Main St", "city": "Anytown"},
                "hobbies": ["reading", "coding"],
            }
            json_content = json.dumps(data)
            file_path.write_text(json_content)
            allure.attach(json_content, "Original JSON Content", allure.attachment_type.JSON)

        with allure.step("Extract and parse JSON to readable text"):
            result = extract_text_from_file(file_path)
            allure.attach(result, "Extracted Readable Text", allure.attachment_type.TEXT)

        with allure.step("Verify key-value pairs are extracted"):
            check.is_in("name: John Doe", result)
            check.is_in("street: 123 Main St", result)
            check.is_in("city: Anytown", result)

    @allure.story("Markdown Processing")
    @allure.title("Extract text content from Markdown file")
    @allure.description(
        "Tests that Markdown files are parsed and text content is extracted with formatting elements preserved"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("file-processing", "markdown", "text-extraction")
    def test_extract_text_from_markdown_file(self, temp_dir: Path) -> None:
        """Test extracting text from a Markdown file."""
        with allure.step("Create Markdown file with various formatting elements"):
            file_path = temp_dir / "test.md"
            content = """# Heading 1

This is a paragraph with **bold** and *italic* text.

## Heading 2

- List item 1
- List item 2

[Link text](https://example.com)
"""
            file_path.write_text(content)
            allure.attach(content, "Original Markdown Content", allure.attachment_type.TEXT)

        with allure.step("Extract text content from Markdown file"):
            result = extract_text_from_file(file_path)
            allure.attach(result, "Extracted Text Content", allure.attachment_type.TEXT)

        with allure.step("Verify Markdown elements are preserved in extracted text"):
            check.is_in("Heading 1", result)
            check.is_in("This is a paragraph with", result)
            check.is_in("bold", result)
            check.is_in("italic", result)
            check.is_in("List item 1", result)
            check.is_in("Link text", result)

    @allure.story("HTML Processing")
    @allure.title("Extract clean text content from HTML file")
    @allure.description(
        "Tests that HTML files are parsed to extract clean text content while filtering out script and style elements"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("file-processing", "html", "text-extraction", "content-filtering")
    def test_extract_text_from_html_file(self, temp_dir: Path) -> None:
        """Test extracting text from an HTML file."""
        with allure.step("Create HTML file with mixed content including scripts and styles"):
            file_path = temp_dir / "test.html"
            content = """<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <style>body { color: blue; }</style>
    <script>console.log('test');</script>
</head>
<body>
    <h1>Main Heading</h1>
    <p>This is a <strong>paragraph</strong> with <em>emphasis</em>.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
</body>
</html>"""
            file_path.write_text(content)
            allure.attach(content, "Original HTML Content", allure.attachment_type.HTML)

        with allure.step("Extract clean text content from HTML"):
            result = extract_text_from_file(file_path)
            allure.attach(result, "Extracted Clean Text", allure.attachment_type.TEXT)

        with allure.step("Verify text content is extracted correctly"):
            check.is_in("Test Page", result)
            check.is_in("Main Heading", result)
            check.is_in("paragraph", result)
            check.is_in("emphasis", result)
            check.is_in("Item 1", result)

        with allure.step("Verify script and style content is filtered out"):
            # Should not include script or style content
            check.is_not_in("console.log", result)
            check.is_not_in("color: blue", result)

    @allure.story("Error Handling")
    @allure.title("Handle malformed JSON files gracefully")
    @allure.description(
        "Tests that malformed JSON files are handled gracefully by falling back to plain text processing with appropriate warnings"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("file-processing", "error-handling", "json", "fallback")
    def test_extract_text_from_malformed_json(
        self,
        temp_dir: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test extracting text from a malformed JSON file."""
        with allure.step("Create malformed JSON file"):
            file_path = temp_dir / "malformed.json"
            content = "{'not': 'valid json'"
            file_path.write_text(content)
            allure.attach(content, "Malformed JSON Content", allure.attachment_type.TEXT)

        with allure.step("Attempt to extract text with warning capture"):
            with caplog.at_level(logging.WARNING):
                result = extract_text_from_file(file_path)

            allure.attach(result, "Fallback Text Result", allure.attachment_type.TEXT)
            allure.attach(caplog.text, "Captured Log Messages", allure.attachment_type.TEXT)

        with allure.step("Verify fallback to plain text processing"):
            # Should fall back to treating as plain text
            check.equal(result, content)

        with allure.step("Verify appropriate warning was logged"):
            check.is_in("Could not parse JSON", caplog.text)

    @allure.story("JSON Processing")
    @allure.title("Extract text from deeply nested JSON structures")
    @allure.description(
        "Tests that deeply nested JSON objects are properly parsed and text content is extracted from all levels"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("file-processing", "json", "nested-structures")
    def test_extract_text_from_nested_json(self, temp_dir: Path) -> None:
        """Test extracting text from deeply nested JSON."""
        with allure.step("Create deeply nested JSON structure"):
            file_path = temp_dir / "nested.json"
            data = {
                "level1": {
                    "level2": {
                        "level3": {"message": "Deep value", "items": ["a", "b", "c"]},
                    },
                },
            }
            json_content = json.dumps(data)
            file_path.write_text(json_content)
            allure.attach(json_content, "Nested JSON Structure", allure.attachment_type.JSON)

        with allure.step("Extract text from nested JSON"):
            result = extract_text_from_file(file_path)
            allure.attach(result, "Extracted Text from Nested JSON", allure.attachment_type.TEXT)

        with allure.step("Verify deeply nested values are extracted"):
            check.is_in("message: Deep value", result)

    @allure.story("JSON Processing")
    @allure.title("Extract text from JSON array structures")
    @allure.description(
        "Tests that JSON arrays are properly parsed and text content is extracted from all array elements"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("file-processing", "json", "array-processing")
    def test_extract_text_from_json_array(self, temp_dir: Path) -> None:
        """Test extracting text from JSON array."""
        with allure.step("Create JSON array with multiple objects"):
            file_path = temp_dir / "array.json"
            data = [
                {"id": 1, "name": "First"},
                {"id": 2, "name": "Second"},
                {"id": 3, "name": "Third"},
            ]
            json_content = json.dumps(data)
            file_path.write_text(json_content)
            allure.attach(json_content, "JSON Array Content", allure.attachment_type.JSON)

        with allure.step("Extract text from JSON array"):
            result = extract_text_from_file(file_path)
            allure.attach(result, "Extracted Array Text", allure.attachment_type.TEXT)

        with allure.step("Verify all array elements are processed"):
            check.is_in("name: First", result)
            check.is_in("name: Second", result)
            check.is_in("name: Third", result)

    @allure.story("Error Handling")
    @allure.title("Handle nonexistent files gracefully")
    @allure.description(
        "Tests that attempting to process nonexistent files is handled gracefully with appropriate error logging"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("file-processing", "error-handling", "nonexistent-file")
    def test_extract_text_from_nonexistent_file(
        self,
        temp_dir: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test extracting text from a nonexistent file."""
        with allure.step("Define path to nonexistent file"):
            file_path = temp_dir / "nonexistent.txt"
            allure.attach(str(file_path), "Nonexistent File Path", allure.attachment_type.TEXT)

        with allure.step("Attempt to extract text from nonexistent file"):
            with caplog.at_level(logging.WARNING):
                result = extract_text_from_file(file_path)

            allure.attach(result, "Result from Nonexistent File", allure.attachment_type.TEXT)
            allure.attach(caplog.text, "Captured Log Messages", allure.attachment_type.TEXT)

        with allure.step("Verify empty result is returned"):
            check.equal(result, "")

        with allure.step("Verify appropriate error was logged"):
            check.is_in("Could not process file", caplog.text)

    @allure.story("Error Handling")
    @allure.title("Handle Unicode decode errors gracefully")
    @allure.description(
        "Tests that files with encoding issues are handled gracefully without crashing the application"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("file-processing", "error-handling", "encoding", "unicode")
    def test_extract_text_with_unicode_decode_error(self, temp_dir: Path) -> None:
        """Test handling of files with encoding issues."""
        with allure.step("Create binary file with invalid UTF-8 data"):
            file_path = temp_dir / "binary.dat"
            # Write binary data that can't be decoded as UTF-8
            binary_data = b"\x80\x81\x82\x83\x84"
            file_path.write_bytes(binary_data)
            allure.attach(str(binary_data), "Binary Data Content", allure.attachment_type.TEXT)

        with allure.step("Extract text from binary file with encoding issues"):
            # Should handle gracefully with errors='ignore'
            result = extract_text_from_file(file_path)
            allure.attach(result, "Result from Binary File", allure.attachment_type.TEXT)

        with allure.step("Verify function handles encoding errors gracefully"):
            check.is_not_none(result)

    @allure.story("Edge Cases")
    @allure.title("Extract text from empty file")
    @allure.description(
        "Tests that empty files are handled correctly and return empty strings without errors"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("file-processing", "edge-cases", "empty-file")
    def test_extract_text_from_empty_file(self, temp_dir: Path) -> None:
        """Test extracting text from an empty file."""
        with allure.step("Create empty text file"):
            file_path = temp_dir / "empty.txt"
            file_path.write_text("")
            allure.attach("(empty file)", "Empty File Content", allure.attachment_type.TEXT)

        with allure.step("Extract text from empty file"):
            result = extract_text_from_file(file_path)
            allure.attach(
                result if result else "(empty result)",
                "Extraction Result",
                allure.attachment_type.TEXT,
            )

        with allure.step("Verify empty string is returned"):
            check.equal(result, "")

    @allure.story("JSON Processing")
    @allure.title("Extract text from JSON with only numeric values")
    @allure.description(
        "Tests that JSON files containing only numeric values are handled correctly without string content"
    )
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("file-processing", "json", "numeric-data")
    def test_extract_text_from_json_with_no_strings(self, temp_dir: Path) -> None:
        """Test extracting text from JSON with only numbers."""
        with allure.step("Create JSON file with only numeric values"):
            file_path = temp_dir / "numbers.json"
            data = {"count": 42, "values": [1, 2, 3], "nested": {"number": 3.14}}
            json_content = json.dumps(data)
            file_path.write_text(json_content)
            allure.attach(json_content, "Numeric JSON Content", allure.attachment_type.JSON)

        with allure.step("Extract text from numeric JSON"):
            result = extract_text_from_file(file_path)
            allure.attach(result, "Extracted Text from Numeric JSON", allure.attachment_type.TEXT)

        with allure.step("Verify function handles numeric-only JSON"):
            # Should return empty string or minimal content when no strings
            check.is_not_none(result)

    @allure.story("JSON Processing")
    @allure.title("Extract text from JSON with null values")
    @allure.description(
        "Tests that JSON files containing null values are handled correctly and valid text content is extracted"
    )
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("file-processing", "json", "null-values")
    def test_extract_text_from_json_with_null_values(self, temp_dir: Path) -> None:
        """Test extracting text from JSON with null values."""
        with allure.step("Create JSON file with mixed null and valid values"):
            file_path = temp_dir / "nulls.json"
            data = {"name": "Test", "value": None, "items": [None, "item", None]}
            json_content = json.dumps(data)
            file_path.write_text(json_content)
            allure.attach(json_content, "JSON with Null Values", allure.attachment_type.JSON)

        with allure.step("Extract text from JSON with null values"):
            result = extract_text_from_file(file_path)
            allure.attach(result, "Extracted Text with Nulls", allure.attachment_type.TEXT)

        with allure.step("Verify valid text content is extracted"):
            check.is_in("name: Test", result)

        with allure.step("Verify null values are handled gracefully"):
            # Should handle null values gracefully
            pass

    @allure.story("HTML Processing")
    @allure.title("Extract text from .htm file extension")
    @allure.description(
        "Tests that .htm files (alternate HTML extension) are processed correctly like .html files"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("file-processing", "html", "file-extensions")
    def test_extract_text_from_htm_file(self, temp_dir: Path) -> None:
        """Test extracting text from .htm file (alternate HTML extension)."""
        with allure.step("Create .htm file with HTML content"):
            file_path = temp_dir / "test.htm"
            content = "<html><body><p>HTM content</p></body></html>"
            file_path.write_text(content)
            allure.attach(content, "HTM File Content", allure.attachment_type.HTML)

        with allure.step("Extract text from .htm file"):
            result = extract_text_from_file(file_path)
            allure.attach(result, "Extracted HTM Text", allure.attachment_type.TEXT)

        with allure.step("Verify HTM content is extracted correctly"):
            check.is_in("HTM content", result)

    @allure.story("File Extension Handling")
    @allure.title("Handle case-insensitive file extensions")
    @allure.description(
        "Tests that file extension matching works correctly regardless of case (e.g., .JSON vs .json)"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("file-processing", "file-extensions", "case-insensitive")
    def test_extract_text_case_insensitive_extension(self, temp_dir: Path) -> None:
        """Test that file extension matching is case-insensitive."""
        with allure.step("Create file with uppercase .JSON extension"):
            file_path = temp_dir / "test.JSON"
            data = {"key": "value"}
            json_content = json.dumps(data)
            file_path.write_text(json_content)
            allure.attach(
                json_content, "Uppercase Extension JSON Content", allure.attachment_type.JSON
            )

        with allure.step("Extract text from uppercase extension file"):
            result = extract_text_from_file(file_path)
            allure.attach(
                result, "Extracted Text from Uppercase Extension", allure.attachment_type.TEXT
            )

        with allure.step("Verify case-insensitive extension handling"):
            check.is_in("key: value", result)

    @allure.story("Markdown Processing")
    @allure.title("Extract text from complex Markdown with code blocks and tables")
    @allure.description(
        "Tests that complex Markdown files with code blocks, tables, and blockquotes are processed correctly"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("file-processing", "markdown", "code-blocks", "tables")
    def test_extract_text_complex_markdown(self, temp_dir: Path) -> None:
        """Test extracting text from complex Markdown with code blocks."""
        with allure.step("Create complex Markdown file with various elements"):
            file_path = temp_dir / "complex.md"
            content = """# Main Title

```python
def code():
    return "This is code"
```

Regular text here.

| Table | Header |
|-------|--------|
| Cell1 | Cell2  |

> Blockquote text
"""
            file_path.write_text(content)
            allure.attach(content, "Complex Markdown Content", allure.attachment_type.TEXT)

        with allure.step("Extract text from complex Markdown"):
            result = extract_text_from_file(file_path)
            allure.attach(result, "Extracted Complex Markdown Text", allure.attachment_type.TEXT)

        with allure.step("Verify all Markdown elements are preserved"):
            check.is_in("Main Title", result)
            check.is_in("Regular text here", result)
            check.is_in("Table", result)
            check.is_in("Header", result)
            check.is_in("Blockquote text", result)

    @allure.story("Error Handling")
    @allure.title("Handle file permission errors gracefully")
    @allure.description(
        "Tests that permission errors are handled gracefully with appropriate error logging and empty result"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("file-processing", "error-handling", "permissions")
    def test_extract_text_with_permission_error(
        self,
        temp_dir: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test handling of permission errors."""
        with allure.step("Create test file and simulate permission error"):
            file_path = temp_dir / "test.txt"
            file_path.write_text("content")
            allure.attach(str(file_path), "Test File Path", allure.attachment_type.TEXT)

        with allure.step("Attempt to read file with mocked permission error"):
            with patch.object(Path, "read_text", side_effect=PermissionError("Access denied")):
                with caplog.at_level(logging.WARNING):
                    result = extract_text_from_file(file_path)

                allure.attach(result, "Result from Permission Error", allure.attachment_type.TEXT)
                allure.attach(
                    caplog.text, "Captured Permission Error Logs", allure.attachment_type.TEXT
                )

        with allure.step("Verify empty result on permission error"):
            check.equal(result, "")

        with allure.step("Verify permission error was logged"):
            check.is_in("Could not process file", caplog.text)

    @allure.story("JSON Processing")
    @allure.title("Extract text from JSON primitive string value")
    @allure.description(
        "Tests that JSON files containing just a primitive string value are handled correctly"
    )
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("file-processing", "json", "primitive-values")
    def test_extract_text_from_json_primitive(self, temp_dir: Path) -> None:
        """Test extracting text from JSON with primitive value."""
        with allure.step("Create JSON file with primitive string value"):
            file_path = temp_dir / "primitive.json"
            content = '"just a string"'
            file_path.write_text(content)
            allure.attach(content, "Primitive JSON Content", allure.attachment_type.JSON)

        with allure.step("Extract text from primitive JSON"):
            result = extract_text_from_file(file_path)
            allure.attach(result, "Extracted Primitive Text", allure.attachment_type.TEXT)

        with allure.step("Verify primitive string value is returned correctly"):
            check.equal(result, '"just a string"')

    @allure.story("JSON Processing")
    @allure.title("Extract text from JSON primitive number value")
    @allure.description(
        "Tests that JSON files containing just a primitive number value are handled correctly"
    )
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("file-processing", "json", "primitive-values", "numeric")
    def test_extract_text_from_json_number(self, temp_dir: Path) -> None:
        """Test extracting text from JSON with just a number."""
        with allure.step("Create JSON file with primitive number value"):
            file_path = temp_dir / "number.json"
            content = "42"
            file_path.write_text(content)
            allure.attach(content, "Number JSON Content", allure.attachment_type.JSON)

        with allure.step("Extract text from number JSON"):
            result = extract_text_from_file(file_path)
            allure.attach(result, "Extracted Number Text", allure.attachment_type.TEXT)

        with allure.step("Verify primitive number value is returned correctly"):
            check.equal(result, "42")

    @allure.story("File Extension Handling")
    @allure.title("Handle unknown file extensions as plain text")
    @allure.description(
        "Tests that files with unknown extensions are treated as plain text and processed correctly"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("file-processing", "file-extensions", "unknown-types", "fallback")
    def test_extract_text_unknown_extension(self, temp_dir: Path) -> None:
        """Test extracting text from file with unknown extension."""
        with allure.step("Create file with unknown extension"):
            file_path = temp_dir / "test.xyz"
            content = "Unknown file type content"
            file_path.write_text(content)
            allure.attach(content, "Unknown Extension File Content", allure.attachment_type.TEXT)

        with allure.step("Extract text from unknown extension file"):
            result = extract_text_from_file(file_path)
            allure.attach(
                result, "Extracted Text from Unknown Extension", allure.attachment_type.TEXT
            )

        with allure.step("Verify unknown extension files are treated as plain text"):
            check.equal(result, content)
