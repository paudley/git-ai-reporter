# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

Feature: Error Handling and Recovery
    As a git-ai-reporter user
    I want the tool to handle errors gracefully
    So that I can recover from failures and understand issues

    Background:
        Given I have git-ai-reporter installed
        And I am in a directory with git access

    Scenario: Handle missing API key
        Given no GEMINI_API_KEY is configured
        When I run git-ai-reporter
        Then an error message should explain the missing key
        And instructions for obtaining a key should be shown
        And the tool should exit gracefully
        And no partial files should be created

    Scenario: Handle invalid API key
        Given an invalid GEMINI_API_KEY is set
        When I run git-ai-reporter
        Then the API error should be caught
        And a user-friendly message should be shown
        And suggestions for fixing the key should be provided
        And the exit code should indicate failure

    Scenario: Handle non-git directory
        Given I am in a directory without git initialization
        When I run git-ai-reporter
        Then an error should indicate no git repository
        And suggestions to run 'git init' should be shown
        And no crash should occur

    Scenario: Handle empty git repository
        Given a git repository with no commits
        When I run git-ai-reporter
        Then the tool should handle the empty state
        And generate minimal summary files
        And indicate no commits were found
        And exit successfully

    Scenario: Handle corrupted git repository
        Given a git repository with corrupted objects
        When I run git-ai-reporter
        Then git errors should be caught
        And repository issues should be reported
        And suggestions for git fsck should be provided
        And the tool should exit cleanly

    Scenario: Handle network connectivity issues
        Given the network connection is unavailable
        When I run git-ai-reporter
        Then connection errors should be caught
        And offline mode should be suggested
        And cached results should be used if available
        And retry logic should be attempted

    Scenario: Handle API timeout
        Given the Gemini API is slow to respond
        When I run git-ai-reporter
        Then requests should timeout appropriately
        And retries should use exponential backoff
        And partial progress should be saved
        And timeout duration should be configurable

    Scenario: Handle rate limiting
        Given API rate limits are exceeded
        When I run git-ai-reporter
        Then rate limit errors should be detected
        And wait time should be calculated
        And progress should be displayed
        And analysis should resume after waiting

    Scenario: Handle file permission errors
        Given output files are read-only
        When I run git-ai-reporter
        Then permission errors should be caught
        And specific files should be identified
        And permission fix suggestions should be shown
        And no data loss should occur

    Scenario: Handle disk space issues
        Given insufficient disk space for cache
        When I run git-ai-reporter
        Then disk space errors should be detected
        And space requirements should be shown
        And cleanup suggestions should be provided
        And graceful degradation should occur

    Scenario: Handle malformed git commits
        Given commits with invalid UTF-8 encoding
        When I analyze these commits
        Then encoding errors should be handled
        And commits should still be processed
        And problematic text should be sanitized
        And analysis should continue

    Scenario: Handle circular dependencies
        Given a complex merge history with loops
        When analyzing the repository
        Then circular references should be detected
        And infinite loops should be prevented
        And analysis should complete
        And merge commits should be handled correctly

    Scenario: Handle interrupted analysis
        Given an analysis is terminated unexpectedly
        When I run git-ai-reporter again
        Then previous progress should be detected
        And option to resume should be offered
        And completed work should be preserved
        And analysis should continue from last point

    Scenario: Handle concurrent modifications
        Given files are modified during analysis
        When git-ai-reporter is running
        Then file changes should not corrupt output
        And atomic writes should be used
        And backup files should be created
        And final state should be consistent

    Scenario: Handle invalid date ranges
        Given invalid date parameters:
            | start_date  | end_date    | issue                |
            | 2025-13-01  | 2025-01-15  | Invalid month        |
            | 2025-01-32  | 2025-02-01  | Invalid day          |
            | 2025-02-01  | 2025-01-01  | End before start     |
            | tomorrow    | yesterday   | Future dates         |
        When I run git-ai-reporter with these dates
        Then date validation should catch errors
        And clear error messages should be shown
        And valid date format should be explained
        And examples should be provided

    Scenario: Handle memory constraints
        Given a repository with 10000+ commits
        When analyzing with limited memory
        Then memory usage should be bounded
        And streaming processing should be used
        And garbage collection should run
        And analysis should complete successfully

    Scenario: Handle missing dependencies
        Given required Python packages are missing
        When I run git-ai-reporter
        Then missing dependencies should be detected
        And installation commands should be suggested
        And virtual environment should be recommended
        And clear error messages should be shown

    Scenario: Validate and sanitize AI responses
        Given AI returns unexpected response format
        When processing the response
        Then validation should catch format issues
        And response should be sanitized
        And default values should be used
        And analysis should continue

    Scenario: Handle repository access permissions
        Given limited read access to repository
        When analyzing protected branches
        Then permission errors should be handled
        And accessible content should be analyzed
        And skipped content should be logged
        And partial results should be generated

    Scenario: Graceful degradation for API failures
        Given Gemini API is partially available
        When some requests fail
        Then successful requests should be preserved
        And failed requests should be retried
        And degraded mode should be indicated
        And best-effort results should be generated