#!/bin/bash
# Wrapper script to run vector-memory with clean stdout for MCP

# Suppress all UV warnings
export UV_LINK_MODE=copy
export UV_NO_PROGRESS=1

# Run with uv, redirecting any non-JSON output to stderr
cd "/Volumes/CaseSensitive Volume/Github/vector-memory"
exec uv run vector_memory.py 2>&1 | grep -v "^warning:" | grep -v "Building" | grep -v "Built" | grep -v "Uninstalled" | grep -v "Installed"
