# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Custom Allure Plugin Wrapper for pytest.

This plugin resolves the conflict between allure-pytest and allure-pytest-bdd
by selectively enabling the appropriate plugin based on test type.
"""

import argparse
from collections.abc import Callable
import os
from pathlib import Path
import shutil

from pytest import Config
from pytest import Parser

# Constants
LINK_PATTERN_PARTS = 2
BDD_DIRECTORY_NAME = "bdd"


def _create_label_type(type_name, legal_values: set = None) -> Callable[[str], set[tuple]]:
    """Create a label type parser for allure options.

    Args:
        type_name: The type of label
        legal_values: Set of legal values for this type (optional)

    Returns:
        A function that parses label type strings
    """
    if legal_values is None:
        legal_values = set()

    def a_label_type(string):
        # Import allure here to avoid issues during option parsing
        try:
            import allure  # pylint: disable=import-outside-toplevel
            from allure_commons.types import LabelType  # pylint: disable=import-outside-toplevel
        except ImportError:
            return set()

        atoms = set(string.split(","))
        if type_name is LabelType.SEVERITY:
            if not atoms <= legal_values:
                raise argparse.ArgumentTypeError(
                    f"Illegal {type_name} values: {', '.join(atoms - legal_values)}, "
                    f"only [{', '.join(legal_values)}] are allowed"
                )
            return {(type_name, allure.severity_level(atom)) for atom in atoms}
        return {(type_name, atom) for atom in atoms}

    return a_label_type


def _create_custom_field_type(string: str) -> list[tuple[str, str]]:
    """Parse custom field type string.

    Args:
        string: String in format 'type_name=value1,value2'

    Returns:
        List of tuples (type_name, value)
    """
    type_name, values = string.split("=", 1)
    atoms = set(values.split(","))
    return [(type_name, atom) for atom in atoms]


def _create_link_pattern(string: str) -> list[str]:
    """Parse link pattern string.

    Args:
        string: String in format 'link_type:link_pattern'

    Returns:
        List with pattern components

    Raises:
        ArgumentTypeError: If pattern format is invalid
    """
    pattern = string.split(":", 1)
    if not pattern[0]:
        raise argparse.ArgumentTypeError("Link type is mandatory.")

    if len(pattern) != LINK_PATTERN_PARTS:
        raise argparse.ArgumentTypeError("Link pattern is mandatory")
    return pattern


def _add_basic_allure_options(parser: Parser) -> None:
    """Add basic Allure options to parser.

    Args:
        parser: Pytest argument parser
    """
    # Add all the options that allure-pytest expects
    parser.getgroup("reporting").addoption(
        "--alluredir",
        action="store",
        dest="allure_report_dir",
        metavar="DIR",
        default=None,
        help="Generate Allure report in the specified directory (may not exist)",
    )

    parser.getgroup("reporting").addoption(
        "--clean-alluredir",
        action="store_true",
        dest="clean_alluredir",
        help="Clean alluredir folder if it exists",
    )

    parser.getgroup("reporting").addoption(
        "--allure-no-capture",
        action="store_false",
        dest="attach_capture",
        help="Do not attach pytest captured logging/stdout/stderr to report",
    )

    parser.getgroup("reporting").addoption(
        "--inversion",
        action="store",
        dest="inversion",
        default=False,
        help="Run tests not in testplan",
    )


def _add_allure_filter_options(parser: Parser) -> None:
    """Add Allure filter options to parser.

    Args:
        parser: Pytest argument parser
    """
    try:
        import allure  # pylint: disable=import-outside-toplevel
        from allure_commons.types import LabelType  # pylint: disable=import-outside-toplevel

        severities = [x.value for x in list(allure.severity_level)]
        formatted_severities = ", ".join(severities)

        parser.getgroup("general").addoption(
            "--allure-severities",
            action="store",
            dest="allure_severities",
            metavar="SEVERITIES_SET",
            default={},
            type=_create_label_type(LabelType.SEVERITY, legal_values=set(severities)),
            help=f"""Comma-separated list of severity names.
                                         Tests only with these severities will be run.
                                         Possible values are: {formatted_severities}.""",
        )

        parser.getgroup("general").addoption(
            "--allure-epics",
            action="store",
            dest="allure_epics",
            metavar="EPICS_SET",
            default={},
            type=_create_label_type(LabelType.EPIC),
            help="""Comma-separated list of epic names.
                                         Run tests that have at least one of the specified feature labels.""",
        )

        parser.getgroup("general").addoption(
            "--allure-features",
            action="store",
            dest="allure_features",
            metavar="FEATURES_SET",
            default={},
            type=_create_label_type(LabelType.FEATURE),
            help="""Comma-separated list of feature names.
                                         Run tests that have at least one of the specified feature labels.""",
        )

        parser.getgroup("general").addoption(
            "--allure-stories",
            action="store",
            dest="allure_stories",
            metavar="STORIES_SET",
            default={},
            type=_create_label_type(LabelType.STORY),
            help="""Comma-separated list of story names.
                                         Run tests that have at least one of the specified story labels.""",
        )

        parser.getgroup("general").addoption(
            "--allure-ids",
            action="store",
            dest="allure_ids",
            metavar="IDS_SET",
            default={},
            type=_create_label_type(LabelType.ID),
            help="""Comma-separated list of IDs.
                                         Run tests that have at least one of the specified id labels.""",
        )

        parser.getgroup("general").addoption(
            "--allure-label",
            action="append",
            dest="allure_labels",
            metavar="LABELS_SET",
            default=[],
            type=_create_custom_field_type,
            help="""List of labels to run in format label_name=value1,value2.
                                         "Run tests that have at least one of the specified labels.""",
        )

        parser.getgroup("general").addoption(
            "--allure-link-pattern",
            action="append",
            dest="allure_link_pattern",
            metavar="LINK_TYPE:LINK_PATTERN",
            default=[],
            type=_create_link_pattern,
            help="""Url pattern for link type. Allows short links in test,
                                         like 'issue-1'. Text will be formatted to full url with python
                                         str.format().""",
        )
    except ImportError:
        _add_fallback_allure_options(parser)


def _add_fallback_allure_options(parser: Parser) -> None:
    """Add fallback Allure options when allure is not available.

    Args:
        parser: Pytest argument parser
    """
    # If allure not available, add dummy options to prevent errors
    parser.getgroup("general").addoption(
        "--allure-severities", action="store", dest="allure_severities", default={}
    )
    parser.getgroup("general").addoption(
        "--allure-epics", action="store", dest="allure_epics", default={}
    )
    parser.getgroup("general").addoption(
        "--allure-features", action="store", dest="allure_features", default={}
    )
    parser.getgroup("general").addoption(
        "--allure-stories", action="store", dest="allure_stories", default={}
    )
    parser.getgroup("general").addoption(
        "--allure-ids", action="store", dest="allure_ids", default={}
    )
    parser.getgroup("general").addoption(
        "--allure-label", action="append", dest="allure_labels", default=[]
    )
    parser.getgroup("general").addoption(
        "--allure-link-pattern", action="append", dest="allure_link_pattern", default=[]
    )


def pytest_addoption(parser: Parser) -> None:
    """Add --alluredir option for unified Allure reporting.

    Args:
        parser: Pytest argument parser.
    """
    _add_basic_allure_options(parser)
    _add_allure_filter_options(parser)


def pytest_configure(config: Config) -> None:
    """Configure Allure reporting by enabling appropriate plugins.

    Args:
        config: Pytest configuration object.
    """
    if not (allure_dir := config.getoption("allure_report_dir", None)):
        return  # No Allure reporting requested

    # Clean directory if requested
    if config.getoption("clean_alluredir", False):
        if os.path.exists(allure_dir):
            shutil.rmtree(allure_dir)

    # Create directory
    os.makedirs(allure_dir, exist_ok=True)

    # Check what test types we have
    has_bdd_tests = _check_for_bdd_tests()
    has_regular_tests = _check_for_regular_tests()

    # Enable appropriate plugin based on test types
    if has_bdd_tests and not has_regular_tests:
        # Only BDD tests - use allure-pytest-bdd
        _enable_bdd_plugin(config, allure_dir)
    elif has_regular_tests and not has_bdd_tests:
        # Only regular tests - use allure-pytest
        _enable_standard_plugin(config, allure_dir)
    else:
        # Mixed tests - use allure-pytest (should handle both)
        _enable_standard_plugin(config, allure_dir)


def _check_for_bdd_tests() -> bool:
    """Check if there are BDD tests in the test suite.

    Returns:
        True if BDD tests are found, False otherwise.
    """
    # Check for BDD directories
    test_root = Path("tests")
    if (test_root / BDD_DIRECTORY_NAME).exists():
        return True

    # Check for .feature files
    for root, _, files in os.walk("tests"):
        if any(f.endswith(".feature") for f in files):
            return True

    # Check for pytest-bdd imports in test files
    bdd_patterns = (
        "from pytest_bdd import",
        "import pytest_bdd",
        "@scenario",
        "@given",
        "@when",
        "@then",
    )

    for root, _, files in os.walk("tests"):
        for file in files:
            if file.endswith(".py"):
                try:
                    file_path = Path(root) / file
                    content = file_path.read_text("utf-8")
                    if any(pattern in content for pattern in bdd_patterns):
                        return True
                except (OSError, UnicodeDecodeError):
                    continue

    return False


def _check_for_regular_tests() -> bool:
    """Check if there are regular (non-BDD) tests in the test suite.

    Returns:
        True if regular tests are found, False otherwise.
    """
    # Look for test files outside BDD directories
    for root, _, files in os.walk("tests"):
        # Skip BDD directories
        if BDD_DIRECTORY_NAME in root.lower():
            continue

        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                return True

    return True  # Assume regular tests exist if not proven otherwise


def _enable_bdd_plugin(config: Config, allure_dir: str) -> None:
    """Enable allure-pytest-bdd plugin.

    Args:
        config: Pytest configuration object.
        allure_dir: Directory for Allure results.
    """
    try:
        # Import and configure allure-pytest-bdd
        import allure_pytest_bdd.plugin  # pylint: disable=import-outside-toplevel

        # Set all the alluredir options that the plugin expects
        config.option.allure_report_dir = allure_dir
        config.option.alluredir = allure_dir  # Backward compatibility
        config.option.clean_alluredir = config.getoption("clean_alluredir", False)
        config.option.attach_capture = config.getoption("attach_capture", True)
        config.option.inversion = config.getoption("inversion", False)

        # Set filter options
        config.option.allure_severities = config.getoption("allure_severities", {})
        config.option.allure_epics = config.getoption("allure_epics", {})
        config.option.allure_features = config.getoption("allure_features", {})
        config.option.allure_stories = config.getoption("allure_stories", {})
        config.option.allure_ids = config.getoption("allure_ids", {})
        config.option.allure_labels = config.getoption("allure_labels", [])
        config.option.allure_link_pattern = config.getoption("allure_link_pattern", [])

        # Call the plugin's configuration
        if hasattr(allure_pytest_bdd.plugin, "pytest_configure"):
            allure_pytest_bdd.plugin.pytest_configure(config)

        # Register the plugin if not already registered
        if not config.pluginmanager.is_registered(allure_pytest_bdd.plugin):
            config.pluginmanager.register(allure_pytest_bdd.plugin, "allure_pytest_bdd")

    except ImportError:
        pass  # Plugin not available


def _enable_standard_plugin(config: Config, allure_dir: str) -> None:
    """Enable allure-pytest plugin.

    Args:
        config: Pytest configuration object.
        allure_dir: Directory for Allure results.
    """
    try:
        # Import and configure allure-pytest
        import allure_pytest.plugin  # pylint: disable=import-outside-toplevel

        # Set all the alluredir options that the plugin expects
        config.option.allure_report_dir = allure_dir
        config.option.alluredir = allure_dir  # Backward compatibility
        config.option.clean_alluredir = config.getoption("clean_alluredir", False)
        config.option.attach_capture = config.getoption("attach_capture", True)
        config.option.inversion = config.getoption("inversion", False)

        # Set filter options
        config.option.allure_severities = config.getoption("allure_severities", {})
        config.option.allure_epics = config.getoption("allure_epics", {})
        config.option.allure_features = config.getoption("allure_features", {})
        config.option.allure_stories = config.getoption("allure_stories", {})
        config.option.allure_ids = config.getoption("allure_ids", {})
        config.option.allure_labels = config.getoption("allure_labels", [])
        config.option.allure_link_pattern = config.getoption("allure_link_pattern", [])

        # Call the plugin's configuration
        if hasattr(allure_pytest.plugin, "pytest_configure"):
            allure_pytest.plugin.pytest_configure(config)

        # Register the plugin if not already registered
        if not config.pluginmanager.is_registered(allure_pytest.plugin):
            config.pluginmanager.register(allure_pytest.plugin, "allure_pytest")

    except ImportError:
        pass  # Plugin not available
