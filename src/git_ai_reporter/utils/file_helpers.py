# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Helper functions for file processing and text extraction."""

import json
import logging
from pathlib import Path
from typing import Final

from bs4 import BeautifulSoup
import markdown

from . import json_helpers

_logger = logging.getLogger(__name__)

# Constants
FILE_EXT_JSON: Final[str] = ".json"
FILE_EXT_MD: Final[str] = ".md"


def _extract_string_values_from_json(
    data: dict[str, object] | list[object] | str | float | bool | None,
) -> list[str]:
    """Recursively extracts all string values from a JSON object."""
    strings = []
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                strings.append(f"{key}: {value}")
            elif isinstance(value, (dict, list)):
                strings.extend(_extract_string_values_from_json(value))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                strings.extend(_extract_string_values_from_json(item))
    return strings


def extract_text_from_file(file_path: Path) -> str:
    """Extract clean text content from a file, handling JSON, HTML, MD, and TXT.

    Args:
        file_path: The path to the file to process.

    Returns:
        The extracted text content as a single string. Returns an empty
        string if the file cannot be read or processed.
    """
    extracted_content = ""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        suffix = file_path.suffix.lower()

        if suffix == FILE_EXT_JSON:
            try:
                data = json_helpers.safe_json_decode(content)
                extracted_content = (
                    ". ".join(_extract_string_values_from_json(data))
                    if isinstance(data, (dict, list))
                    else content
                )
            except json.JSONDecodeError:
                _logger.warning("Could not parse JSON from %s; treating as plain text.", file_path)
                extracted_content = content
        elif suffix in {".html", ".htm"}:
            soup = BeautifulSoup(content, "html.parser")
            for element in soup(["script", "style"]):
                element.decompose()
            extracted_content = " ".join(soup.stripped_strings)
        elif suffix == FILE_EXT_MD:
            html = markdown.markdown(content)
            soup = BeautifulSoup(html, "html.parser")
            extracted_content = " ".join(soup.stripped_strings)
        else:
            extracted_content = content
    except (OSError, UnicodeDecodeError) as e:
        _logger.warning("Could not process file %s: %s", file_path, e)
        extracted_content = ""
    return extracted_content
