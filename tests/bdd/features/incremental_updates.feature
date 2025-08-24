# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

Feature: Incremental Repository Updates
    As a git-ai-reporter user
    I want the tool to correctly handle incremental updates
    So that new commits are properly added to existing reports

    Background:
        Given I have a git repository with sample commits
        And I have configured my Gemini API key

    Scenario: Add new commit to previously analyzed repository
        Given I have a repository with existing commits from sample_git_data.jsonl
        And I have run git-ai-reporter to generate initial files
        And NEWS.md contains the initial week's narrative
        And CHANGELOG.txt contains the initial entries
        And DAILY_UPDATES.md contains the initial daily summaries
        When I add a new commit with message "feat: Add important new feature"
        And I run git-ai-reporter again for the same week
        Then NEWS.md should contain the new commit information
        And CHANGELOG.txt should include the new feature entry
        And DAILY_UPDATES.md should be updated with the new commit
        And the week header should remain the same
        And existing content should be preserved and merged

    Scenario: Multiple incremental updates in same week
        Given I have a repository with existing commits
        And I have run git-ai-reporter to generate initial files
        When I add a commit "fix: Critical bug fix" on Monday
        And I run git-ai-reporter
        And I add a commit "test: Add comprehensive tests" on Tuesday
        And I run git-ai-reporter
        And I add a commit "refactor: Improve code structure" on Wednesday
        And I run git-ai-reporter
        Then NEWS.md should contain all three new commits
        And the narrative should be coherent and comprehensive
        And no commits should be missing from the analysis

    Scenario: Verify non-trivial commits are not filtered
        Given I have a repository with existing commits
        When I add commits with these prefixes:
            | prefix    | message                                   | should_appear |
            | feat      | feat: Add user authentication            | true          |
            | fix       | fix: Resolve memory leak                 | true          |
            | test      | test: Add integration tests              | true          |
            | refactor  | refactor: Improve database queries       | true          |
            | ci        | ci: Add GitHub Actions workflow          | true          |
            | docs      | docs: Update API documentation           | true          |
            | perf      | perf: Optimize image loading             | true          |
            | build     | build: Update dependencies               | true          |
            | style     | style: Format code with prettier         | false         |
            | chore     | chore: Update .gitignore                 | false         |
        And I run git-ai-reporter
        Then the commits marked as should_appear=true should be in all output files
        And the commits marked as should_appear=false may be filtered

    Scenario: Week boundary handling with incremental updates
        Given I have commits from last week that have been analyzed
        When I add new commits in the current week
        And I run git-ai-reporter
        Then NEWS.md should have separate entries for each week
        And CHANGELOG.txt should contain all changes in [Unreleased]
        And each week should maintain its own narrative

    Scenario: Verify file update detection
        Given I have a repository with analyzed commits
        And I record the modification times of output files
        When I add a new significant commit
        And I run git-ai-reporter
        Then all three output files should have newer modification times
        And the files should contain the new commit data