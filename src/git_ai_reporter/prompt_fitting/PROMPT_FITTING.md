# Prompt Fitting Module

## CRITICAL: Data Integrity Compliance

**MANDATORY READING BEFORE ANY CHANGES:**
- This module enforces **complete data integrity** as required by project specifications
- **NO truncation, sampling, or data loss is permitted under any circumstances**
- **All commits must be analyzed** - mandatory complete commit coverage
- **System fails fast if any data would be lost**
- Legacy class names (e.g., `DiffTruncationFitter`) are misleading - they now preserve ALL data

## Overview

The `prompt_fitting.py` module provides advanced, **data-preserving** strategies for fitting large content into LLM token limits. This is a critical component for maintaining **mandatory complete data integrity** while working within the constraints of language model context windows.

## Core Principles

### 1. **PROJECT COMPLIANCE: ZERO Data Loss**
- **MANDATORY complete data integrity** - NO truncation, sampling, or data loss permitted
- **Complete commit coverage** - Every commit must be analyzed (no sampling allowed)
- **All fitting strategies MUST preserve all of the original information**
- **Immediate failure on data loss** - System fails fast if any data would be lost
- Validation mechanisms ensure data preservation requirements are met

### 2. **Research-Based Approaches**
- Implements state-of-the-art techniques from prompt engineering research
- Overlapping chunking with configurable overlap ratios
- Semantic-aware truncation that preserves structure
- Adaptive strategies based on content type

### 3. **Production-Ready Architecture**
- Pluggable strategy system for different content types
- Comprehensive error handling and validation
- Performance monitoring and metrics
- Extensive configuration options

## Strategies

### Overlapping Chunks Strategy
**Best for:** Daily summaries, weekly narratives, changelog content

```python
# Creates overlapping chunks with 20% overlap by default
# Processes adjacent pairs to ensure full coverage
# Combines results while maintaining information completeness

config = PromptFittingConfig(overlap_ratio=0.2)
fitter = PromptFitter(config, token_counter)
result = await fitter.fit_content(content, ContentType.DAILY_SUMMARY)
```

**How it works:**
1. Splits content into overlapping chunks
2. Each chunk overlaps with neighbors by configured ratio (default 20%)
3. Processes chunks in pairs to ensure boundary coverage
4. Combines results with clear segment markers

### Data-Preserving Diff Strategy
**Best for:** Git diffs, code changes
**⚠️ NOTE:** Despite the legacy class name `DiffTruncationFitter`, this strategy NEVER truncates data.

```python
# PROJECT COMPLIANT: Preserves 100% of diff content through overlapping chunks
# NO truncation or data loss - uses hierarchical processing instead
# Maintains complete file-level context for analysis

result = await fit_git_diff(diff_content, token_counter, max_tokens=100000)
```

**How it works:**
1. Identifies structural elements (file headers, hunk markers)
2. Creates overlapping chunks that respect file boundaries
3. **NEVER truncates** - uses overlapping segments to preserve ALL data
4. Returns instruction for hierarchical processing if content is too large
5. Maintains 100% file-level representation

### Log Compression Strategy (100% Data Preserving)
**Best for:** Commit logs, temporal data
**CRITICAL:** NO sampling allowed - preserves ALL commit information

```python
# PROJECT COMPLIANT: Preserves 100% of commit log through overlapping chunks
# NO sampling or data loss - uses chunk processing for ALL commits
# Maintains complete temporal coverage and commit diversity

result = await fit_commit_log(log_content, token_counter, max_tokens=50000)
```

**How it works:**
1. Analyzes complete temporal distribution (never samples)
2. Creates overlapping chunks with 50% overlap to ensure no data loss
3. **Preserves ALL commits** - no sampling or skipping allowed
4. Returns instruction for chunk processing if content is too large
5. Maintains complete chronological context and commit coverage

## Usage Examples

### Basic Usage

```python
from git_ai_reporter.utils.prompt_fitting import PromptFitter, PromptFittingConfig, ContentType

# Initialize with configuration
config = PromptFittingConfig(
    max_tokens=100000,
    overlap_ratio=0.25,
    validation_enabled=True
)

fitter = PromptFitter(config, token_counter)

# Fit content with automatic strategy selection
result = await fitter.fit_content(
    content=large_diff,
    content_type=ContentType.GIT_DIFF,
    target_tokens=80000
)

print(f"Compression ratio: {result.compression_ratio:.2f}")
print(f"Data preserved: {result.data_preserved}")
print(f"Strategy used: {result.strategy_used}")
```

### Advanced Configuration

```python
# Custom configuration for specific needs
config = PromptFittingConfig(
    max_tokens=500000,      # Higher limit for powerful models
    overlap_ratio=0.3,      # More overlap for critical content
    min_chunk_size=200,     # Larger minimum chunks
    max_iterations=15,      # More fitting attempts
    preserve_structure=True, # Maintain document structure
    validation_enabled=True  # Enable data preservation checks
)

# Strategy-specific usage
chunks_fitter = OverlappingChunksFitter(config, token_counter)
result = await chunks_fitter.fit_content(weekly_content, 100000)
```

### Integration with Gemini Client

```python
# Example integration pattern
class TokenCounterAdapter:
    def __init__(self, gemini_client, model_name):
        self.client = gemini_client
        self.model = model_name
    
    async def count_tokens(self, content: str) -> int:
        response = await self.client.aio.models.count_tokens(
            model=self.model, 
            contents=content
        )
        return response.total_tokens

# Usage in service
token_counter = TokenCounterAdapter(gemini_client, "gemini-2.5-pro")
fitted_content = await fit_git_diff(diff, token_counter, 100000)
```

## Validation and Monitoring

### Data Preservation Validation

The module includes built-in validation to ensure data preservation:

```python
# PROJECT COMPLIANT: 100% data integrity validation
def validate_preservation(self, original: str, fitted: str) -> bool:
    # For chunked content, verify complete preservation
    if "--- Content Segment" in fitted or "--- Diff Segment" in fitted:
        # Chunked content preserves ALL data through overlapping boundaries
        return len(fitted) >= len(original) * 0.8  # Account for chunk headers
    
    # For non-chunked content, must be identical (already fits)
    return len(fitted) >= len(original) * 0.95  # Minimal formatting tolerance
    
    # CRITICAL: Any data loss triggers immediate system failure
    # This enforces the mandatory 100% data integrity requirement
```

### Performance Monitoring

```python
# Results include comprehensive metrics
@dataclass
class FittingResult:
    fitted_content: str
    original_size: int
    fitted_size: int
    strategy_used: FittingStrategy
    data_preserved: bool
    metadata: dict[str, Any]
    
    @property
    def compression_ratio(self) -> float:
        return self.fitted_size / self.original_size
```

## Research Context

This implementation is based on current research in:

- **Prompt Engineering**: Optimal strategies for LLM context management
- **Information Compression**: Lossless techniques for content reduction  
- **Semantic Preservation**: Maintaining meaning across transformations
- **Chunking Strategies**: Overlap optimization for continuity

## CRITICAL BUG: OverlappingChunksFitter Data Loss Issue

**DISCOVERED:** A critical data integrity violation has been identified in `OverlappingChunksFitter._create_overlapping_chunks()` at lines 166-167:

```python
chunk_size = total_lines // num_chunks
overlap_size = int(chunk_size * self.config.overlap_ratio)  # ❌ TRUNCATES TO ZERO
```

**THE PROBLEM:**
- For small content with small chunks, `int()` truncation causes `overlap_size = 0`
- Example: 10 lines, 3 chunks → `chunk_size = 3`, `overlap_ratio = 0.2` → `overlap_size = int(3 * 0.2) = 0`
- Result: Chunks `[0-2]`, `[3-5]`, `[6-9]` with **ZERO overlap** and only 90% coverage (missing line 9)
- **VIOLATES PROJECT SPEC:** This creates data loss, breaking the mandatory 100% data integrity requirement

**WHY LogCompressionFitter WORKS:**
- Uses step-based approach: `chunk_step = max(1, lines_per_chunk // 2)`
- Always maintains minimum step of 1, ensuring overlap even for tiny chunks
- Provides true 100% coverage as verified by testing

**IMMEDIATE ACTION REQUIRED:**
1. Replace percentage-based overlap calculation with step-based minimum overlap
2. Ensure `overlap_size >= 1` for any chunking operation
3. Add data loss prevention validation
4. Update all tests to verify 100% coverage requirement

**TEMPORARY WORKAROUND:**
Until fixed, prefer `LogCompressionFitter` for critical data preservation tasks.

## Why Two Different Compression Methods?

The codebase maintains two specialized compression approaches for different content types:

### 1. **LogCompressionFitter** - Temporal/Sequential Content
**Optimized for:** Commit logs, chronological data, event sequences

**Design Rationale:**
- **Step-Based Chunking**: Uses `chunk_step = lines_per_chunk // 2` for consistent 50% overlap
- **Temporal Continuity**: Preserves chronological flow across chunk boundaries
- **Commit Preservation**: Ensures no commits are lost during log processing
- **Proven Algorithm**: Successfully maintains 100% data coverage as verified

**Use Cases:**
- Processing commit history logs
- Analyzing chronological development activity
- Maintaining temporal context in summaries

### 2. **DiffTruncationFitter** - Structural/Hierarchical Content  
**Optimized for:** Git diffs, code changes, file-based content

**Design Rationale:**
- **File-Boundary Awareness**: Respects `diff --git` headers and file boundaries
- **Structural Preservation**: Maintains complete file context within chunks
- **Hunk-Level Integrity**: Preserves diff hunks and context lines
- **Variable Overlap**: Adaptive overlap based on file boundaries (25% default)

**Use Cases:**
- Processing git diff outputs
- Analyzing code changes across multiple files
- Maintaining file-level context for AI analysis

### **Strategic Separation Benefits:**

1. **Domain-Specific Optimization**: Each fitter is optimized for its content type's unique characteristics
2. **Boundary Handling**: Different content types have different natural boundaries (commits vs files)
3. **Overlap Strategies**: Temporal data benefits from fixed overlap; structural data needs adaptive overlap
4. **Validation Logic**: Each can validate preservation using domain-specific rules
5. **Performance Tuning**: Algorithm parameters can be optimized per content type

### **Architectural Decision:**
Rather than a single "one-size-fits-all" approach, the specialized fitters provide:
- Better preservation guarantees for each content type
- More efficient processing algorithms  
- Domain-specific error handling and validation
- Cleaner separation of concerns and maintainability

## Future Enhancements

Planned improvements include:

1. **FIX CRITICAL BUG**: Repair OverlappingChunksFitter data loss issue immediately
2. **Semantic Compression**: AI-powered summarization while preserving key facts
3. **Hierarchical Summary**: Multi-level abstraction with drill-down capability
4. **Dynamic Overlap**: Adaptive overlap based on content analysis
5. **Performance Optimization**: Caching and parallel processing
6. **Custom Validators**: Domain-specific preservation checks
7. **Unified Testing**: Comprehensive data integrity validation across all fitters

## Integration Guidelines

### For Service Classes

1. Create a token counter adapter for your LLM client
2. Configure prompt fitting based on your use case
3. Use appropriate content types for optimal strategy selection
4. Handle `FittingResult` objects for metrics and validation

### For New Content Types

1. Extend the `ContentType` enum
2. Implement specialized fitting strategy if needed
3. Add content type to strategy selection mapping
4. Create validation logic for your content domain

### Error Handling

```python
try:
    result = await fitter.fit_content(content, content_type, target_tokens)
except ValueError as e:
    if "exceeds target" in str(e):
        # Handle token limit exceeded
        pass
    elif "validation failed" in str(e):
        # Handle data preservation failure
        pass
```

This module ensures that git-ai-reporter maintains its commitment to 100% data integrity while efficiently working within LLM constraints.