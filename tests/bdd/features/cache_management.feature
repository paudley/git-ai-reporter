# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

Feature: Cache Management and Performance
    As a git-ai-reporter user
    I want efficient caching of analysis results
    So that subsequent runs are fast and cost-effective

    Background:
        Given I have a configured cache directory
        And I have a repository with analyzed commits

    Scenario: Create cache on first analysis
        Given no cache exists for the repository
        When I analyze commits for the first time
        Then a cache directory should be created
        And commit analyses should be stored
        And cache metadata should be generated
        And cache keys should be deterministic

    Scenario: Reuse cache for identical commits
        Given commits have been analyzed and cached:
            | commit_hash | message                |
            | abc123     | feat: Add feature      |
            | def456     | fix: Fix bug           |
        When I analyze the same commits again
        Then cached results should be loaded
        And no API calls should be made
        And results should be identical
        And performance should improve by 90%

    Scenario: Invalidate cache for modified analysis
        Given cached analysis exists
        When the analysis prompts are updated
        Then cache should be invalidated
        And new analysis should be performed
        And new results should be cached
        And old cache should be cleaned up

    Scenario: Handle cache size limits
        Given the cache directory is approaching size limit
        When new analyses are cached
        Then oldest entries should be evicted
        And frequently accessed entries should be retained
        And cache size should stay within limits
        And eviction should be logged

    Scenario: Cache partial analysis results
        Given an analysis is interrupted mid-process
        When the analysis is resumed
        Then completed analyses should be in cache
        And only remaining commits should be processed
        And the full analysis should complete successfully

    Scenario: Concurrent cache access
        Given multiple git-ai-reporter processes running
        When they access the cache simultaneously
        Then cache operations should be thread-safe
        And no corruption should occur
        And results should be consistent
        And file locking should work correctly

    Scenario: Cache expiration handling
        Given cached entries older than 30 days
        When cache cleanup runs
        Then expired entries should be removed
        And fresh entries should be retained
        And cache statistics should be updated
        And disk space should be recovered

    Scenario: Cache key generation
        Given a commit with specific content:
            | field       | value                          |
            | hash        | abc123def456                   |
            | message     | feat: Add new feature          |
            | diff        | +line1\n-line2\n+line3         |
        When a cache key is generated
        Then it should be deterministic
        And include commit hash
        And include prompt version
        And be filesystem-safe

    Scenario: Cache statistics tracking
        When I run git-ai-reporter with --stats flag
        Then cache statistics should be displayed:
            | metric           | displayed |
            | Total size       | yes       |
            | Number of entries| yes       |
            | Hit rate         | yes       |
            | Age distribution | yes       |
            | Eviction count   | yes       |

    Scenario: Incremental cache updates
        Given a repository with cached analysis
        When new commits are added
        Then only new commits should be analyzed
        And existing cache should be preserved
        And cache should be updated incrementally
        And performance should be optimal

    Scenario: Cache backup and restore
        Given a populated cache directory
        When I backup the cache
        Then all cache data should be preserved
        And cache can be restored on another machine
        And restored cache should function correctly

    Scenario: Handle corrupted cache gracefully
        Given a cache file is corrupted
        When the cache is accessed
        Then the corrupted entry should be detected
        And it should be automatically rebuilt
        And analysis should continue
        And corruption should be logged

    Scenario: Memory-efficient cache loading
        Given a large cache with thousands of entries
        When cache is accessed
        Then entries should be loaded on-demand
        And memory usage should remain bounded
        And LRU eviction should manage memory
        And performance should remain acceptable

    Scenario: Cache warming for common patterns
        Given historical usage patterns
        When git-ai-reporter starts
        Then frequently used entries should be pre-loaded
        And common prompts should be cached
        And startup time should be optimized

    Scenario: Clear cache on demand
        Given a populated cache
        When I run git-ai-reporter with --clear-cache
        Then all cache entries should be removed
        And cache directory should be cleaned
        And confirmation should be requested
        And next run should rebuild cache

    Scenario: Cache compatibility across versions
        Given cache created by older git-ai-reporter version
        When newer version accesses the cache
        Then version compatibility should be checked
        And incompatible entries should be rebuilt
        And compatible entries should be reused
        And migration should be automatic