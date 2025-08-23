# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

Feature: Pre-Release Process
    As a project maintainer
    I want to generate release-ready documentation before tagging a version
    So that I can prepare comprehensive release artifacts automatically

    Background:
        Given I have a git repository with commits
        And I have configured my Gemini API key
        And the repository has an existing NEWS.md file
        And the repository has an existing CHANGELOG.txt file

    Scenario: Generate documentation for upcoming release
        Given I have commits in the [Unreleased] section of CHANGELOG.txt:
            | category | item                                    |
            | Added    | New user authentication system          |
            | Fixed    | Memory leak in data processing pipeline |
            | Changed  | Updated API endpoints for v2 compliance |
        And I want to prepare for version "1.2.3" release
        When I run git-ai-reporter with --pre-release "1.2.3"
        Then NEWS.md should contain "Released v1.2.3 🚀" in the latest week header
        And CHANGELOG.txt should have a new section "## [v1.2.3]"
        And the [v1.2.3] section should contain all unreleased changes
        And a new empty [Unreleased] section should be created
        And the release date should match today's date

    Scenario: Pre-release documentation with comprehensive changes
        Given I have a repository with commits from the last week:
            | message                               | category | files           |
            | feat: Add OAuth2 integration          | Added    | src/auth.py     |
            | fix: Resolve database connection bug  | Fixed    | src/db.py       |
            | perf: Optimize query performance      | Changed  | src/queries.py  |
            | security: Fix XSS vulnerability       | Security | src/views.py    |
        When I run git-ai-reporter with --pre-release "2.0.0"
        Then NEWS.md should reflect the release as completed
        And the week header should show "Released v2.0.0 🚀"
        And CHANGELOG.txt should move all changes to [v2.0.0] section
        And all four change categories should be properly organized
        And the version date should be today's date

    Scenario: Pre-release with no unreleased changes
        Given the CHANGELOG.txt has an empty [Unreleased] section:
            """
            ## [Unreleased]
            
            *No unreleased changes yet.*
            """
        When I run git-ai-reporter with --pre-release "1.0.1"
        Then CHANGELOG.txt should create section [v1.0.1] with minimal content
        And the section should indicate patch-level changes only
        And NEWS.md should reflect a maintenance release
        And the new [Unreleased] section should be properly formatted

    Scenario: Pre-release preserves existing version history
        Given CHANGELOG.txt contains previous versions:
            | version | date       | changes                    |
            | 1.1.0   | 2025-01-15 | Major feature additions    |
            | 1.0.0   | 2025-01-01 | Initial stable release     |
        And I have new unreleased changes
        When I run git-ai-reporter with --pre-release "1.2.0"
        Then the new [v1.2.0] section should be added at the top
        And all existing version sections should remain unchanged
        And the version ordering should be chronologically correct
        And the Keep a Changelog format should be maintained

    Scenario: Pre-release with custom date range
        Given I want to analyze commits from "2025-01-15" to "2025-01-22"
        And I want to prepare for version "1.1.5" release
        When I run git-ai-reporter with --start-date "2025-01-15" --end-date "2025-01-22" --pre-release "1.1.5"
        Then only commits in the specified range should be analyzed
        And the release documentation should reflect that time period
        And NEWS.md should show the correct week range in the header
        And CHANGELOG.txt should contain only relevant changes

    Scenario: Pre-release documentation format validation
        When I run git-ai-reporter with --pre-release "3.0.0"
        Then NEWS.md should be valid Markdown with proper frontmatter
        And the YAML frontmatter should be correctly formatted
        And CHANGELOG.txt should follow Keep a Changelog standards
        And version headers should use correct semantic version format
        And dates should be in ISO format (YYYY-MM-DD)
        And emoji indicators should be present for release headers

    Scenario: Pre-release with metrics and summary data
        Given the repository has significant activity:
            | metric           | value |
            | commits_analyzed | 25    |
            | files_changed    | 15    |
            | lines_added      | 450   |
            | lines_removed    | 120   |
        When I run git-ai-reporter with --pre-release "2.1.0"
        Then NEWS.md should include summary metrics for the release
        And the metrics should reflect the pre-release activity
        And the narrative should mention the scope of changes
        And DAILY_UPDATES.md should contain detailed daily breakdowns

    Scenario: Pre-release error handling with invalid version
        When I run git-ai-reporter with --pre-release "invalid.version"
        Then the tool should complete without errors
        And the version string should be used as provided
        And appropriate warnings should be logged
        And the release documentation should still be generated

    Scenario: Pre-release with existing release section conflict
        Given CHANGELOG.txt already contains a section for "[v1.3.0]"
        When I run git-ai-reporter with --pre-release "1.3.0"
        Then the tool should handle the conflict gracefully
        And the existing section should be preserved or merged
        And no data loss should occur
        And appropriate warnings should be displayed

    Scenario Outline: Pre-release version format handling
        Given I want to prepare for version "<version>" release
        When I run git-ai-reporter with --pre-release "<version>"
        Then the version should be formatted as "<expected_format>"
        And the release header should show "Released v<expected_format> 🚀"
        And CHANGELOG.txt should use format "## [v<expected_format>]"

        Examples:
            | version | expected_format |
            | 1.2.3   | 1.2.3          |
            | v2.0.0  | 2.0.0          |
            | 3.0.0-beta | 3.0.0-beta  |
            | 1.0.0-rc.1 | 1.0.0-rc.1  |

    Scenario: Pre-release documentation content quality
        Given I have meaningful commits with descriptive messages
        When I run git-ai-reporter with --pre-release "1.4.0"
        Then NEWS.md should contain coherent narrative about the release
        And the narrative should be written in past tense (as if released)
        And technical changes should be explained for stakeholders
        And the summary should highlight key improvements and fixes
        And the tone should be professional and informative

    Scenario: Pre-release with cache optimization
        Given previous analysis results exist in cache
        When I run git-ai-reporter with --pre-release "1.5.0"
        Then cached commit analyses should be reused when possible
        And only release-specific processing should be performed
        And the performance should be optimized for repeated runs
        And cache integrity should be maintained

    Scenario: Pre-release integration with git workflow
        Given I am preparing for a release in my git workflow
        And I want to ensure documentation is ready before tagging
        When I run git-ai-reporter with --pre-release "2.2.0"
        Then all release artifacts should be ready for commit
        And the documentation should be suitable for release notes
        And the changes should be staged for the release commit
        And the version should be clearly indicated throughout