---
title: Internal Documentation
description: Implementation details and module documentation
---

# Internal Documentation

This section contains detailed implementation documentation for Git AI Reporter's internal modules.

## Module Documentation

### Core Modules

- [Summaries Module](summaries.md) - Prompt generation and summary creation
- [Utils Module](utils.md) - Utility functions and helpers
- [Prompt Fitting Module](prompt-fitting.md) - Token optimization and prompt management

### Module Structure

Each module in the `src/git_ai_reporter/` directory contains its own documentation:

```
src/git_ai_reporter/
├── summaries/
│   └── SUMMARIES.md          # Summary generation documentation
├── utils/
│   └── UTILS_MODULE.md        # Utilities documentation
└── prompt_fitting/
    ├── README.md              # Prompt fitting overview
    └── PROMPT_FITTING.md      # Detailed prompt fitting docs
```

## Implementation Details

### Design Principles

1. **Clean Architecture**: Separation of concerns between layers
2. **Type Safety**: Full type hints with Pydantic models
3. **Async First**: Async/await for all I/O operations
4. **Robust Error Handling**: Comprehensive error recovery
5. **Intelligent Caching**: Multi-layer cache system

### Code Organization

The codebase follows a modular structure:

- **analysis/**: Git repository analysis and filtering
- **cache/**: Caching layer for API responses
- **orchestration/**: Main workflow coordination
- **services/**: External service integrations (Gemini AI)
- **summaries/**: Prompt templates and summary generation
- **utils/**: Shared utilities and helpers
- **writing/**: Output file generation

## Development Guidelines

### Adding New Features

1. Create feature branch from `main`
2. Add comprehensive tests (BDD and unit)
3. Update relevant module documentation
4. Ensure all linting passes (`./scripts/lint.sh`)
5. Submit PR with clear description

### Module Documentation Standards

Each module should have:

- **Purpose**: Clear statement of what the module does
- **Architecture**: How it fits into the overall system
- **API**: Public functions and classes
- **Examples**: Usage examples
- **Testing**: How to test the module

## Key Implementation Concepts

### The Airlock Pattern

Used for robust JSON handling from LLM outputs. See [JSON Handling Architecture](../architecture/json-handling.md).

### Three-Tier AI Processing

Multi-tier approach for cost-effective AI analysis. See [Three-Tier AI Architecture](../architecture/three-tier-ai.md).

### Multi-Lens Analysis

Three complementary perspectives for comprehensive analysis. See [Multi-Lens Strategy](../architecture/multi-lens.md).

## Testing Infrastructure

### Test Organization

```
tests/
├── unit/           # Unit tests for individual components
├── bdd/            # Behavior-driven development tests
│   ├── features/   # Gherkin feature files
│   └── step_defs/  # Step definitions
├── fixtures/       # Test data and fixtures
└── cassettes/      # VCR recordings for API tests
```

### Test Coverage Requirements

- Minimum 55% overall coverage (enforced by CI)
- Critical paths must have 100% coverage
- All public APIs must be tested
- Edge cases and error conditions covered

## Performance Considerations

### Optimization Points

1. **Batch Processing**: Process commits in batches of 50
2. **Async Operations**: Parallel API calls where possible
3. **Caching Strategy**: Multi-layer cache to minimize API calls
4. **Token Management**: Optimize prompts to reduce token usage

### Benchmarks

| Operation | Target | Current |
|-----------|--------|---------|
| Commit Analysis | <100ms | 95ms |
| Daily Summary | <500ms | 450ms |
| Weekly Report | <2s | 1.8s |
| Cache Hit Rate | >70% | 75% |

## Security Considerations

### Secure Practices

1. **No Secrets in Code**: API keys only in environment variables
2. **Input Validation**: All inputs validated with Pydantic
3. **Safe JSON Parsing**: Airlock pattern for untrusted JSON
4. **Path Traversal Prevention**: Absolute paths only
5. **Dependency Scanning**: Regular security updates

## Contributing

See [Contributing Guide](../development/contributing.md) for detailed information on:

- Development setup
- Code standards
- Testing requirements
- PR process
- Release procedures