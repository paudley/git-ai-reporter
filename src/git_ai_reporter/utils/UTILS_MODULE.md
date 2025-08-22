# Data Oracle `utils` Module: Developer Documentation

## 1. Purpose and Core Goal

The `utils` module is a utility toolkit for the `git-ai-reporter` library. Its primary goal is to provide a central, standardized, and highly robust repository for common, cross-cutting concerns such as JSON handling, file processing, and functional programming patterns.

This module enforces the **DRY (Don't Repeat Yourself)** principle at a fundamental level. By centralizing this logic, we ensure that the entire application handles common tasks in a consistent, predictable, and resilient manner. Adherence to the functions provided by this module is not optional; it is a core requirement for maintaining the stability and quality of the system.

## 2. Module Structure

The `utils` module is broken down into several files, each with a distinct and narrow responsibility, adhering to the project's coding guidelines for high cohesion and low coupling.

-   `__init__.py`: Defines the **public API** of the module. It exports a curated set of high-level functions for use by the rest of the application. All imports from the `utils` module should be made from this top-level package.
-   `json_helpers.py`: Contains all logic for JSON serialization and deserialization. This is a critical component for ensuring data integrity at the system's boundaries.
-   `file_helpers.py`: Provides utilities for file I/O and, specifically, for extracting clean, usable text from various file formats (e.g., Markdown, HTML, JSON).

## 3. Mandatory JSON Handling: The "Airlock" Pattern

A primary function of this module is to create a secure and robust "airlock" for all JSON data entering or leaving the system. The standard Python `json` library is notoriously brittle and fails on common, real-world data formats. Therefore, direct use of `json.loads` and `json.dumps` is **strictly forbidden** throughout the application. They **MUST** be replaced by the robust alternatives provided in this module.

### 3.1 Decoding with `utils.tolerate` (The Ingress Airlock)

**Requirement:** All external JSON data, particularly data originating from files or LLM outputs, **MUST** be decoded using `utils.tolerate()`.

**Rationale:**
Real-world JSON is often imperfect. Large Language Models, in particular, are prone to generating JSON with minor syntax errors such as trailing commas, single quotes instead of double quotes, or wrapping the JSON in Markdown code fences (` ```json ... ``` `). The standard `json.loads()` is unforgiving and will raise a `JSONDecodeError` on any of these minor deviations, causing the application to crash.

The `utils.tolerate()` function is built on top of the `tolerantjson` library and is specifically designed to handle these real-world imperfections. It automatically cleans and parses slightly malformed JSON, making the data ingestion pipeline significantly more resilient. Using this function is a foundational aspect of the "Robustness" principle outlined in the coding guidelines. It creates a protective airlock that ensures that only syntactically valid data structures proceed to the next stage of processing (e.g., Pydantic validation).

### 3.2 Encoding with `utils.safe_json_dumps` (The Egress Airlock)

**Requirement:** All Python objects being serialized into JSON strings **MUST** be encoded using `utils.safe_json_dumps()`.

**Rationale:**
The standard `json.dumps()` is fragile and lacks built-in support for many common data types used in data science and database applications. It will raise a `TypeError` if it encounters types like `datetime`, `date`, `Decimal`, or `UUID`. This leads to frequent runtime crashes when handling real-world data from databases or APIs.

The `utils.safe_json_dumps()` function provides a robust, centralized encoder that gracefully handles these types by converting them to their standard string representations (e.g., ISO 8601 for datetimes), preventing `TypeError` exceptions. By mandating its use, we eliminate an entire class of common serialization errors and ensure that the application can reliably produce well-formed JSON from complex, real-world data objects.

## 4. Usage Guide

All utilities should be imported directly from the top-level `git-ai-reporter.utils` package.

**Example: Robust JSON Handling**
```python
from data_oracle import utils
from decimal import Decimal
from datetime import datetime
import json

# Decoding a slightly malformed JSON string from an LLM
llm_output = '{"key": "value",}' # Note the trailing comma
try:
    parsed_data = utils.tolerate(llm_output)
    print("Successfully parsed:", parsed_data)
except json.JSONDecodeError as e:
    print("This will not be triggered.")

# Encoding a complex object with non-standard JSON types
data_to_serialize = {
    "amount": Decimal("199.99"),
    "timestamp": datetime.now()
}
# This would fail with the standard json.dumps()
json_string = utils.safe_json_dumps(data_to_serialize, indent=2)
print("Successfully serialized:", json_string)
```
