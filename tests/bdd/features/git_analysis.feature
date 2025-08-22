Feature: Git Repository Analysis
    As a developer
    I want to analyze my git repository
    So that I can generate summaries and changelogs

    Background:
        Given I have a git repository with commits

    Scenario: Analyze a single commit
        Given a commit with message "feat: Add new authentication feature"
        And the commit has changes to "src/auth.py"
        When I analyze the commit
        Then the analysis should identify it as "New Feature"
        And the analysis should mark it as non-trivial

    Scenario: Analyze a trivial commit
        Given a commit with message "docs: Update README"
        And the commit has changes to "README.md"
        When I analyze the commit
        Then the analysis should identify it as "Documentation"
        And the analysis should mark it as trivial

    Scenario: Filter out ignored commits
        Given a commit with message "chore: Update dependencies"
        And the commit has changes to "package.json"
        When I filter commits for analysis
        Then the commit should be excluded from analysis

    Scenario: Group commits by day
        Given commits from multiple days:
            | date       | message                    |
            | 2025-01-07 | feat: Add login feature    |
            | 2025-01-07 | fix: Resolve login bug     |
            | 2025-01-08 | docs: Update API docs      |
        When I group commits by day
        Then I should have 2 daily groups
        And the 2025-01-07 group should have 2 commits
        And the 2025-01-08 group should have 1 commit

    Scenario: Generate daily diff
        Given commits on 2025-01-07:
            | message                  | files         |
            | feat: Add user profile   | src/user.py   |
            | fix: Fix profile loading | src/loader.py |
        When I generate the daily diff
        Then the diff should show net changes for the day
        And the diff should include both files

    Scenario: Handle empty repository
        Given an empty git repository
        When I analyze the repository
        Then the analysis should return empty results
        And no errors should occur

    Scenario: Handle repository with only filtered commits
        Given commits that are all trivial:
            | message                     |
            | style: Format code          |
            | docs: Fix typos             |
            | chore: Update build script  |
        When I analyze the repository
        Then all commits should be marked as trivial
        And the final summary should indicate minimal changes

    Scenario Outline: Categorize different commit types
        Given a commit with message "<message>"
        When I analyze the commit
        Then the analysis should identify it as "<category>"
        And the analysis should mark it as <triviality>

        Examples:
            | message                              | category              | triviality  |
            | feat: Add new dashboard              | New Feature          | non-trivial |
            | fix: Resolve memory leak             | Bug Fix              | non-trivial |
            | perf: Optimize database queries      | Performance          | non-trivial |
            | refactor: Restructure auth module    | Refactoring          | non-trivial |
            | test: Add unit tests for API         | Tests                | trivial     |
            | docs: Update installation guide      | Documentation        | trivial     |
            | style: Apply black formatting        | Styling              | trivial     |
            | chore: Update CI configuration       | Chore                | trivial     |
            | security: Fix SQL injection          | Security             | non-trivial |
            | build: Update webpack config         | Build                | non-trivial |