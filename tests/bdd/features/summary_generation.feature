Feature: Summary Generation
    As a project manager
    I want to generate summaries of development work
    So that I can communicate progress to stakeholders

    Background:
        Given I have analyzed commits from the repository

    Scenario: Generate daily summary
        Given the following commits for 2025-01-07:
            | message                      | category     |
            | feat: Add user authentication | New Feature  |
            | fix: Resolve login timeout    | Bug Fix      |
            | docs: Update API docs         | Documentation|
        When I generate a daily summary
        Then the summary should have a title
        And the summary should have a descriptive paragraph
        And the summary should list key achievements
        And the summary should mention authentication and login fixes

    Scenario: Generate weekly narrative
        Given daily summaries for the week:
            | date       | summary                                    |
            | 2025-01-01 | Implemented core authentication system    |
            | 2025-01-02 | Added user profile management             |
            | 2025-01-03 | Integrated OAuth providers                |
            | 2025-01-04 | Fixed critical security vulnerabilities   |
            | 2025-01-05 | Optimized database queries                |
        When I generate a weekly narrative
        Then the narrative should be approximately 500 words
        And the narrative should identify major themes
        And the narrative should include a "Notable Changes" section
        And the narrative should mention authentication and security

    Scenario: Handle empty daily summary
        Given no commits for 2025-01-07
        When I generate a daily summary
        Then the summary should indicate no activity
        And the summary should be brief

    Scenario: Generate summary with only trivial commits
        Given only trivial commits for 2025-01-07:
            | message                | category       |
            | docs: Fix typos        | Documentation  |
            | style: Format code     | Styling        |
        When I generate a daily summary
        Then the summary should mention minor maintenance
        And the summary should not emphasize major changes

    Scenario: Include dependency changes in weekly narrative
        Given a week with dependency changes:
            | file              | change                    |
            | pyproject.toml    | Added requests library    |
            | requirements.txt  | Updated numpy version     |
        When I generate a weekly narrative
        Then the narrative should mention new dependencies
        And the narrative should not include test dependencies

    Scenario: Preserve historical context
        Given previous weekly narratives exist
        When I generate a new weekly narrative
        Then the new narrative should not repeat previous content
        And the new narrative should build on historical context

    Scenario: Format daily summary correctly
        Given commits with various changes
        When I generate a daily summary
        Then the summary should not include metadata headers
        And the summary should not include salutations
        And the summary should start directly with content

    Scenario: Include code statistics in summary
        Given commits with file changes:
            | files_changed | insertions | deletions |
            | 10           | 500        | 200       |
            | 5            | 150        | 50        |
        When I generate a daily summary
        Then the summary should reflect the scale of changes
        And the summary should mention significant code changes