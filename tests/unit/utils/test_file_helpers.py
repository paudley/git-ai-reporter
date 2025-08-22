# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Unit tests for git_ai_reporter.utils.file_helpers module.

This module tests file processing and text extraction utilities.
"""

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_check as check

from git_ai_reporter.utils.file_helpers import extract_text_from_file


class TestExtractTextFromFile:
    """Test suite for extract_text_from_file function."""

    def test_extract_text_from_plain_text_file(self, temp_dir: Path) -> None:
        """Test extracting text from a plain text file."""
        file_path = temp_dir / "test.txt"
        content = "This is plain text content.\nWith multiple lines."
        file_path.write_text(content)

        result = extract_text_from_file(file_path)
        check.equal(result, content)

    def test_extract_text_from_json_file(self, temp_dir: Path) -> None:
        """Test extracting text from a JSON file."""
        file_path = temp_dir / "test.json"
        data = {
            "name": "John Doe",
            "age": 30,
            "address": {"street": "123 Main St", "city": "Anytown"},
            "hobbies": ["reading", "coding"],
        }
        file_path.write_text(json.dumps(data))

        result = extract_text_from_file(file_path)
        check.is_in("name: John Doe", result)
        check.is_in("street: 123 Main St", result)
        check.is_in("city: Anytown", result)

    def test_extract_text_from_markdown_file(self, temp_dir: Path) -> None:
        """Test extracting text from a Markdown file."""
        file_path = temp_dir / "test.md"
        content = """# Heading 1

This is a paragraph with **bold** and *italic* text.

## Heading 2

- List item 1
- List item 2

[Link text](https://example.com)
"""
        file_path.write_text(content)

        result = extract_text_from_file(file_path)
        check.is_in("Heading 1", result)
        check.is_in("This is a paragraph with", result)
        check.is_in("bold", result)
        check.is_in("italic", result)
        check.is_in("List item 1", result)
        check.is_in("Link text", result)

    def test_extract_text_from_html_file(self, temp_dir: Path) -> None:
        """Test extracting text from an HTML file."""
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

        result = extract_text_from_file(file_path)
        check.is_in("Test Page", result)
        check.is_in("Main Heading", result)
        check.is_in("paragraph", result)
        check.is_in("emphasis", result)
        check.is_in("Item 1", result)
        # Should not include script or style content
        check.is_not_in("console.log", result)
        check.is_not_in("color: blue", result)

    def test_extract_text_from_malformed_json(
        self,
        temp_dir: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test extracting text from a malformed JSON file."""
        file_path = temp_dir / "malformed.json"
        content = "{'not': 'valid json'"
        file_path.write_text(content)

        with caplog.at_level(logging.WARNING):
            result = extract_text_from_file(file_path)

        # Should fall back to treating as plain text
        check.equal(result, content)
        check.is_in("Could not parse JSON", caplog.text)

    def test_extract_text_from_nested_json(self, temp_dir: Path) -> None:
        """Test extracting text from deeply nested JSON."""
        file_path = temp_dir / "nested.json"
        data = {
            "level1": {
                "level2": {
                    "level3": {"message": "Deep value", "items": ["a", "b", "c"]},
                },
            },
        }
        file_path.write_text(json.dumps(data))

        result = extract_text_from_file(file_path)
        check.is_in("message: Deep value", result)

    def test_extract_text_from_json_array(self, temp_dir: Path) -> None:
        """Test extracting text from JSON array."""
        file_path = temp_dir / "array.json"
        data = [
            {"id": 1, "name": "First"},
            {"id": 2, "name": "Second"},
            {"id": 3, "name": "Third"},
        ]
        file_path.write_text(json.dumps(data))

        result = extract_text_from_file(file_path)
        check.is_in("name: First", result)
        check.is_in("name: Second", result)
        check.is_in("name: Third", result)

    def test_extract_text_from_nonexistent_file(
        self,
        temp_dir: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test extracting text from a nonexistent file."""
        file_path = temp_dir / "nonexistent.txt"

        with caplog.at_level(logging.WARNING):
            result = extract_text_from_file(file_path)

        check.equal(result, "")
        check.is_in("Could not process file", caplog.text)

    def test_extract_text_with_unicode_decode_error(self, temp_dir: Path) -> None:
        """Test handling of files with encoding issues."""
        file_path = temp_dir / "binary.dat"
        # Write binary data that can't be decoded as UTF-8
        file_path.write_bytes(b"\x80\x81\x82\x83\x84")

        # Should handle gracefully with errors='ignore'
        result = extract_text_from_file(file_path)
        check.is_not_none(result)

    def test_extract_text_from_empty_file(self, temp_dir: Path) -> None:
        """Test extracting text from an empty file."""
        file_path = temp_dir / "empty.txt"
        file_path.write_text("")

        result = extract_text_from_file(file_path)
        check.equal(result, "")

    def test_extract_text_from_json_with_no_strings(self, temp_dir: Path) -> None:
        """Test extracting text from JSON with only numbers."""
        file_path = temp_dir / "numbers.json"
        data = {"count": 42, "values": [1, 2, 3], "nested": {"number": 3.14}}
        file_path.write_text(json.dumps(data))

        result = extract_text_from_file(file_path)
        # Should return empty string or minimal content when no strings
        check.is_not_none(result)

    def test_extract_text_from_json_with_null_values(self, temp_dir: Path) -> None:
        """Test extracting text from JSON with null values."""
        file_path = temp_dir / "nulls.json"
        data = {"name": "Test", "value": None, "items": [None, "item", None]}
        file_path.write_text(json.dumps(data))

        result = extract_text_from_file(file_path)
        check.is_in("name: Test", result)
        # Should handle null values gracefully

    def test_extract_text_from_htm_file(self, temp_dir: Path) -> None:
        """Test extracting text from .htm file (alternate HTML extension)."""
        file_path = temp_dir / "test.htm"
        content = "<html><body><p>HTM content</p></body></html>"
        file_path.write_text(content)

        result = extract_text_from_file(file_path)
        check.is_in("HTM content", result)

    def test_extract_text_case_insensitive_extension(self, temp_dir: Path) -> None:
        """Test that file extension matching is case-insensitive."""
        file_path = temp_dir / "test.JSON"
        data = {"key": "value"}
        file_path.write_text(json.dumps(data))

        result = extract_text_from_file(file_path)
        check.is_in("key: value", result)

    def test_extract_text_complex_markdown(self, temp_dir: Path) -> None:
        """Test extracting text from complex Markdown with code blocks."""
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

        result = extract_text_from_file(file_path)
        check.is_in("Main Title", result)
        check.is_in("Regular text here", result)
        check.is_in("Table", result)
        check.is_in("Header", result)
        check.is_in("Blockquote text", result)

    def test_extract_text_with_permission_error(
        self,
        temp_dir: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test handling of permission errors."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("content")

        with patch.object(Path, "read_text", side_effect=PermissionError("Access denied")):
            with caplog.at_level(logging.WARNING):
                result = extract_text_from_file(file_path)

        check.equal(result, "")
        check.is_in("Could not process file", caplog.text)

    def test_extract_text_from_json_primitive(self, temp_dir: Path) -> None:
        """Test extracting text from JSON with primitive value."""
        file_path = temp_dir / "primitive.json"
        file_path.write_text('"just a string"')

        result = extract_text_from_file(file_path)
        check.equal(result, '"just a string"')

    def test_extract_text_from_json_number(self, temp_dir: Path) -> None:
        """Test extracting text from JSON with just a number."""
        file_path = temp_dir / "number.json"
        file_path.write_text("42")

        result = extract_text_from_file(file_path)
        check.equal(result, "42")

    def test_extract_text_unknown_extension(self, temp_dir: Path) -> None:
        """Test extracting text from file with unknown extension."""
        file_path = temp_dir / "test.xyz"
        content = "Unknown file type content"
        file_path.write_text(content)

        result = extract_text_from_file(file_path)
        check.equal(result, content)
