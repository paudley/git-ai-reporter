---
title: Templates
description: Custom output templates (Future Feature)
---

# Templates

!!! warning "Future Feature"
    Custom templates are not yet implemented in Git AI Reporter. This page documents the planned feature for future reference.

## Planned Template System

Git AI Reporter will support custom Jinja2 templates to customize the output format of generated documentation.

### Planned Template Types

1. **NEWS.md Template**: Customize the narrative summary format
2. **CHANGELOG.txt Template**: Customize the structured changelog format  
3. **DAILY_UPDATES.md Template**: Customize the daily activity format

### Current Output Formats

Currently, Git AI Reporter generates three fixed-format files:

- **NEWS.md**: Narrative, stakeholder-friendly summaries
- **CHANGELOG.txt**: "Keep a Changelog" compliant structured format
- **DAILY_UPDATES.md**: Day-by-day development activity

## Implementation Status

This feature is planned for a future release. See the [Roadmap](../roadmap.md) for implementation timeline and priority.

## Contributing

If you're interested in contributing to the template system implementation, please:

1. Review the [Roadmap](../roadmap.md) for technical details
2. Open an issue to discuss your approach
3. Follow the [Contributing Guidelines](../development/contributing.md)

## Current Alternatives

While waiting for the template system, you can:

1. **Post-process outputs**: Use scripts to transform the generated files
2. **Custom parsing**: Parse the generated content and reformat as needed
3. **Configuration**: Use environment variables to adjust AI model behavior

## Next Steps

- Review the current [Basic Usage](basic-usage.md) patterns
- Learn about [Configuration](configuration.md) options
- Check the [Roadmap](../roadmap.md) for template system timeline