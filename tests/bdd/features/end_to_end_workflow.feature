# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

Feature: End-to-End Git Reporter Workflow
    As a git-ai-reporter user
    I want to analyze my repository and generate summaries
    So that I can communicate development progress effectively

    Background:
        Given I have a git repository with recent commits
        And I have configured my Gemini API key

    Scenario: Generate summaries for the last week
        Given the repository has commits from the last 7 days
        When I run git-ai-reporter with default settings
        Then NEWS.md should be created with a weekly narrative
        And CHANGELOG.txt should be updated with new entries
        And DAILY_UPDATES.md should contain daily summaries
        And the cache should contain the analysis results

    Scenario: Generate summaries for a specific date range
        Given I want to analyze commits from "2025-01-01" to "2025-01-07"
        When I run git-ai-reporter with start and end dates
        Then the analysis should only include commits in that range
        And the generated files should reflect that time period

    Scenario: Skip cache and force re-analysis
        Given previous analysis results exist in cache
        When I run git-ai-reporter with --no-cache flag
        Then the cache should be bypassed
        And new API calls should be made
        And the results should be fresh

    Scenario: Debug mode with verbose output
        When I run git-ai-reporter with --debug flag
        Then detailed logging should be displayed
        And API requests should be logged
        And token counts should be shown
        And timing information should be displayed

    Scenario: Handle large repository efficiently
        Given a repository with over 1000 commits
        When I run git-ai-reporter for 4 weeks
        Then the analysis should complete successfully
        And commits should be batched appropriately
        And API rate limits should be respected
        And the cache should optimize repeated runs

    Scenario: Incremental update after initial analysis
        Given I have already analyzed the repository yesterday
        And new commits have been added today
        When I run git-ai-reporter again
        Then only new commits should be analyzed
        And existing cache should be reused
        And summaries should be updated incrementally

    Scenario: Handle repository with no changes
        Given a repository with no commits in the specified period
        When I run git-ai-reporter
        Then the tool should complete without errors
        And summaries should indicate no activity
        And cache should reflect the empty period

    Scenario: Respect commit filtering rules
        Given commits with various conventional prefixes:
            | message                           | should_analyze |
            | feat: Add new feature             | true          |
            | fix: Resolve bug                  | true          |
            | chore: Update dependencies        | false         |
            | docs: Update README               | false         |
            | style: Format code                | false         |
        When I run git-ai-reporter
        Then only non-trivial commits should be analyzed
        And filtered commits should be logged in debug mode

    Scenario: Generate summaries for multiple weeks
        Given I want to analyze 4 weeks of history
        When I run git-ai-reporter with --weeks 4
        Then 4 weekly narratives should be generated
        And daily summaries should cover the entire period
        And the changelog should include all relevant changes

    Scenario: Handle API failures gracefully
        Given the Gemini API is temporarily unavailable
        When I run git-ai-reporter with API failures
        Then the tool should retry with exponential backoff
        And error messages should be user-friendly
        And partial results should be cached
        And the tool should suggest recovery options

    Scenario: Merge new changelog entries correctly
        Given an existing CHANGELOG.txt with previous entries
        When I run git-ai-reporter with new commits
        Then new entries should be added to [Unreleased] section
        And existing entries should be preserved
        And the changelog format should remain valid
        And no duplicate entries should be created

    Scenario: Generate summaries for specific repository path
        Given I want to analyze a repository at "/path/to/repo"
        When I run git-ai-reporter with --repo-path option
        Then the tool should analyze that repository
        And use its git history
        And generate summaries in that directory

    Scenario: Validate output file formats
        When I run git-ai-reporter successfully
        Then NEWS.md should be valid Markdown
        And CHANGELOG.txt should follow Keep a Changelog format
        And DAILY_UPDATES.md should have consistent formatting
        And all files should have proper headers

    Scenario: Handle concurrent analysis requests
        Given multiple git-ai-reporter instances are started
        When they analyze the same repository
        Then cache locking should prevent conflicts
        And results should be consistent
        And no data corruption should occur