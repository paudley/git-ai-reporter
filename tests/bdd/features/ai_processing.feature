# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

Feature: AI-Powered Analysis with Gemini
    As a developer using git-ai-reporter
    I want the AI to accurately analyze my commits
    So that I get meaningful and accurate summaries

    Background:
        Given I have configured the Gemini API client
        And I have test data with known commit patterns

    Scenario: Three-tier AI processing for commits
        Given a set of commits to analyze:
            | commit_hash | message                        | diff_size |
            | abc123     | feat: Add authentication       | large     |
            | def456     | fix: Resolve memory leak       | medium    |
            | ghi789     | docs: Update API documentation | small     |
        When the AI analyzes these commits
        Then Tier 1 should extract key information quickly
        And Tier 2 should synthesize daily patterns
        And Tier 3 should generate narrative summaries
        And the results should maintain context across tiers

    Scenario: Handle malformed AI responses
        Given the AI returns imperfect JSON:
            """
            {
                "summary": "Added new feature",
                "category": "New Feature",
                "impact": "high",  // trailing comma
            }
            """
        When the response is parsed
        Then the tolerant JSON parser should handle it
        And valid data should be extracted
        And no crash should occur

    Scenario: Token limit management
        Given a very large diff exceeding token limits
        When the AI processes the content
        Then the prompt fitting module should be invoked
        And content should be chunked appropriately
        And overlapping segments should preserve context
        And all data should be analyzed without loss

    Scenario: Intelligent commit categorization
        Given commits with different characteristics:
            | message                              | expected_category    | expected_impact |
            | feat: Add payment processing         | New Feature         | high           |
            | fix: Typo in comment                 | Bug Fix             | low            |
            | refactor: Extract helper functions   | Refactoring         | medium         |
            | security: Fix SQL injection          | Security            | critical       |
            | perf: Optimize database queries      | Performance         | high           |
        When the AI categorizes these commits
        Then each should be assigned the correct category
        And impact levels should be appropriate
        And security issues should be prioritized

    Scenario: Generate contextual daily summaries
        Given commits from a single day:
            | time   | message                          |
            | 09:00  | feat: Start authentication work  |
            | 11:30  | wip: Add login form              |
            | 14:00  | feat: Complete OAuth integration |
            | 16:30  | test: Add auth tests             |
            | 17:00  | fix: Resolve OAuth callback bug  |
        When the AI generates a daily summary
        Then it should recognize the authentication theme
        And create a coherent narrative
        And identify the progression of work
        And mention both features and fixes

    Scenario: Create engaging weekly narratives
        Given daily summaries for a week:
            | day    | theme                         |
            | Mon    | Authentication implementation |
            | Tue    | OAuth provider integration    |
            | Wed    | Security hardening            |
            | Thu    | Performance optimization      |
            | Fri    | Bug fixes and testing         |
        When the AI generates a weekly narrative
        Then it should identify the security focus
        And create a story arc
        And highlight major achievements
        And provide stakeholder-friendly language

    Scenario: Handle multiple programming languages
        Given commits with changes in different languages:
            | file               | language   | change              |
            | src/app.py         | Python     | Add REST endpoint   |
            | frontend/app.js    | JavaScript | Update UI component |
            | database/schema.sql| SQL        | Add user table      |
            | config/nginx.conf  | Config     | Update routing      |
        When the AI analyzes these changes
        Then it should understand each language context
        And provide appropriate technical descriptions
        And maintain accuracy across technologies

    Scenario: Detect and highlight breaking changes
        Given commits with breaking changes:
            | message                                    | breaking |
            | feat!: Change API response format          | true     |
            | refactor: Rename internal function         | false    |
            | fix: Update deprecated method              | false    |
            | feat: Add backward-incompatible feature    | true     |
        When the AI analyzes these commits for breaking changes
        Then breaking changes should be clearly marked
        And the changelog should include warnings
        And migration notes should be suggested

    Scenario: Smart caching of AI responses
        Given identical commits analyzed previously
        When the same commits are analyzed again
        Then cached responses should be used
        And no API calls should be made
        And results should be identical
        And performance should be significantly faster

    Scenario: Batch processing optimization
        Given 100 small commits to analyze
        When the AI processes them
        Then commits should be batched for efficiency
        And API calls should be minimized
        And token limits should be respected
        And all commits should be processed

    Scenario: Generate changelog with emoji categories
        Given categorized commits:
            | category        | emoji | commits |
            | New Feature     | ✨    | 5       |
            | Bug Fix         | 🐛    | 3       |
            | Performance     | ⚡    | 2       |
            | Security        | 🔒    | 1       |
        When the changelog is generated
        Then each category should have its emoji
        And entries should be properly grouped
        And format should follow Keep a Changelog
        And emojis should enhance readability

    Scenario: Handle API rate limiting
        Given the API rate limit is reached
        When additional requests are made
        Then the system should wait appropriately
        And use exponential backoff
        And inform the user of the delay
        And resume when limits reset

    Scenario: Preserve commit context in summaries
        Given related commits across multiple days:
            | day | message                              |
            | 1   | feat: Start implementing search      |
            | 2   | wip: Add search index                |
            | 3   | feat: Complete search with filters   |
            | 4   | fix: Resolve search performance issue|
        When summaries are generated
        Then the AI should recognize the search feature thread
        And maintain context across daily boundaries
        And tell a coherent story in the weekly narrative