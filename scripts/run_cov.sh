#!/bin/bash
uv run pytest --cov=src --cov-report=term --tb=no -q 2>/dev/null | grep -E "^\s*src.*%" | awk '{print $4, $1}' | sort -n | head -20
