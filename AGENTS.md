# Agent Guide - Vector Memory MCP Server

This document provides AI agents with comprehensive information about the codebase architecture, design decisions, and development guidelines.

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [File Structure](#file-structure)
- [Core Components](#core-components)
- [Design Decisions](#design-decisions)
- [Development Guidelines](#development-guidelines)
- [Testing Strategy](#testing-strategy)
- [Publishing Workflow](#publishing-workflow)

## Project Overview

**Purpose**: MCP server that provides semantic memory capabilities for AI assistants using Redis vector store and HuggingFace embeddings.

**Key Features**:

- Save files (PDF, TXT, MD) to vector memory
- Recall information using natural language queries
- Automatic duplicate removal when re-saving files
- Smart chunking based on file type
- Memory management tools

**Tech Stack**:

- **Language**: Python 3.12+
- **Framework**: FastMCP (MCP server framework)
- **Vector Store**: Redis with RedisVectorStore
- **Embeddings**: HuggingFace sentence-transformers
- **Build Tool**: Hatchling
- **Package Manager**: uv

## Architecture

### High-Level Flow

```
User/AI Client
    ↓
MCP Protocol (stdio)
    ↓
FastMCP Server (vector_memory.py)
    ↓
├─→ HuggingFace Embeddings (sentence-transformers)
└─→ Redis Vector Store (mcp_vector_memory:*)
```

### Data Flow

1. **Save to Memory**:

   ```
   File Path → Check Existence → Determine File Type →
   Get Optimal Chunk Size → Load Document →
   Remove Old Versions → Chunk Content →
   Generate Embeddings → Store in Redis
   ```

2. **Recall from Memory**:
   ```
   Query → Generate Query Embedding →
   Similarity Search in Redis →
   Retrieve Top K Results → Format Output
   ```

## File Structure

```
vector-memory/
├── vector_memory.py          # Main MCP server (2 tools)
├── manage_memory.py          # Interactive management CLI
├── cleanup.py                # Quick cleanup CLI
├── main.py                   # Entry point (if needed)
├── test_connection.py        # Connection test script
├── validate_server_json.py   # Schema validation script
├── pyproject.toml            # Package configuration
├── server.json               # MCP registry metadata
├── README.md                 # Quick start guide
├── USAGE.md                  # Complete usage documentation
├── AGENTS.md                 # This file
├── LICENSE                   # MIT license
└── .github/workflows/
    └── publish-mcp.yml       # Automated publishing workflow
```

## Core Components

### 1. vector_memory.py

**Main Server File** - Exposes MCP tools and handles core functionality.

#### Constants

```python
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
INDEX_NAME = "mcp_vector_memory"  # Namespace for all keys
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
```

#### Helper Functions

**`_get_optimal_chunk_size(file_extension: str) -> tuple[int, int]`**

- Returns (chunk_size, chunk_overlap) based on file type
- PDF: (1500, 200) - larger chunks for structured content
- Markdown: (1200, 150) - preserve structure
- Text: (1000, 100) - standard chunking
- **Design Decision**: Automatic optimization removes user burden

**`_remove_existing_documents(file_paths: list[str]) -> None`**

- Removes old versions of files before saving new ones
- Searches Redis for keys matching source_file metadata
- Handles both metadata storage formats (direct field and JSON)
- **Design Decision**: Prevents duplicate content, ensures freshness

#### MCP Tools

**`save_to_memory(file_paths: list[str]) -> str`**

- **Purpose**: Save files to vector memory
- **Process**:
  1. Remove existing documents for these paths
  2. For each file:
     - Convert to absolute path
     - Determine optimal chunk size
     - Load content (PyPDFLoader or TextLoader)
     - Split into chunks
     - Add source_file metadata
  3. Store all chunks in Redis vector store
- **Returns**: Success message with file count

**`recall_from_memory(what_to_remember: str, how_many_results: int = 3) -> str`**

- **Purpose**: Retrieve relevant information from memory
- **Process**:
  1. Perform similarity search on query
  2. Get top K results
  3. Format with source file and content
- **Returns**: Formatted results with source attribution

### 2. manage_memory.py

**Interactive Management Tool** - CLI for advanced memory management.

#### Key Functions

**`list_all_files()`**

- Lists all documents grouped by source file
- Shows chunk count per file

**`search_files(search_term: str)`**

- Searches for files matching a term
- Case-insensitive partial matching

**`delete_by_file(file_path: str)`**

- Deletes all chunks from a specific file
- Requires confirmation

**`delete_all()`**

- Deletes all documents from memory
- Requires explicit "yes" confirmation

**`interactive_mode()`**

- Menu-driven interface
- Options: list, search, delete, exit

### 3. cleanup.py

**Quick Cleanup Tool** - Simple commands for common operations.

#### Commands

**`cleanup_all()`**

- Deletes all documents
- Drops the Redis index
- Requires confirmation

**`cleanup_by_file(file_path: str)`**

- Deletes documents from specific file
- Shows tip if not found

**`show_stats()`**

- Shows total chunks and unique files
- Lists all files with chunk counts

## Design Decisions

### 1. Data Isolation

**Decision**: Use multiple layers of isolation

- **Database number**: Configurable via REDIS_URL (default: DB 0)
- **Index namespace**: All keys prefixed with `mcp_vector_memory:*`
- **Metadata tagging**: Each chunk has source_file metadata

**Rationale**: Prevents conflicts with other Redis applications, allows multi-project setups.

### 2. Automatic Chunk Size Optimization

**Decision**: System determines chunk size based on file type, not user parameter.

**Rationale**:

- Reduces cognitive load on users
- Optimizes for different content types
- Can be adjusted centrally if needed

### 3. Memory-Friendly Parameter Names

**Decision**: Use natural language parameter names

- `what_to_remember` instead of `query`
- `how_many_results` instead of `k`
- `file_paths` instead of `paths`

**Rationale**: More intuitive for AI assistants and users, aligns with "memory" metaphor.

### 4. Auto-Remove Duplicates

**Decision**: Automatically remove old versions when re-saving files.

**Rationale**:

- Prevents memory bloat
- Ensures latest content is always used
- Transparent to user

### 5. Absolute Path Storage

**Decision**: Convert all paths to absolute before storage.

**Rationale**:

- Consistent identification across sessions
- Reliable duplicate detection
- Clear source attribution

### 6. Logging Suppression

**Decision**: Suppress warnings and library logs to stderr.

**Rationale**:

- MCP protocol requires clean stdout (JSON only)
- Prevents parsing errors in clients
- Improves user experience

### 7. Background Initialization

**Decision**: Use background initialization for embeddings model and vector store.

**Implementation**: Model loading begins automatically in the background after server startup using asyncio tasks.

**Rationale**:

- **Instant startup**: Server starts in <1 second
- **No first-call delay**: Model loads in background while server is idle
- **Better UX**: MCP client connects immediately, tools are ready to use without delays
- **Efficient resources**: Model (~80MB + PyTorch overhead) loads asynchronously using thread pool
- **Self-healing**: If background init hasn't started, first tool call triggers it automatically

**How it works**: 
1. Server starts using `run_stdio_async()` with async main function
2. Background async task starts loading the model in a thread pool immediately
3. Server responds to MCP client instantly (doesn't wait for model loading)
4. First tool call waits for background loading to complete (if still loading)
5. Subsequent calls use the cached instance with no delay

**Result**: By the time the client connects and the user makes their first request, the model is often already loaded or nearly finished loading.

## Development Guidelines

### Code Style

1. **Type Hints**: Use type hints for all function parameters and returns
2. **Docstrings**: Google-style docstrings for all public functions
3. **Formatting**: Follow Black/Ruff formatting (double quotes, 4-space indent)
4. **Naming**:
   - Private functions: `_function_name`
   - Public functions: `function_name`
   - Constants: `UPPER_CASE`

### Environment Variables

**Supported**:

- `REDIS_URL`: Redis connection string (default: `redis://localhost:6379/0`)
- `TF_CPP_MIN_LOG_LEVEL`: TensorFlow logging (set to '3')
- `TRANSFORMERS_VERBOSITY`: Transformers logging (set to 'error')

**To Add New**:

```python
NEW_VAR = os.environ.get("NEW_VAR", "default_value")
```

## Testing Strategy

### Local Testing Without Publishing

#### Quick Tests

```bash
# Syntax check
uv run python -c "import vector_memory; print('✅ OK')"

# Build test
uv build
```

#### MCP Inspector (Recommended)

```bash
npm install -g @modelcontextprotocol/inspector
npx @modelcontextprotocol/inspector uv run vector_memory.py
```

#### Claude Desktop Dev Config

```json
{
  "mcpServers": {
    "vector-memory-dev": {
      "command": "/absolute/path/to/uv",
      "args": ["--directory", "/path/to/vector-memory", "run", "vector_memory.py"],
      "env": {
        "UV_LINK_MODE": "copy",
        "UV_NO_PROGRESS": "1",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

Find uv path: `which uv`. Restart Claude Desktop after config changes.

#### Editable Install

```bash
pip install -e /path/to/vector-memory
```

### Manual Testing

1. **Connection Test**:

   ```bash
   uv run test_connection.py
   ```

2. **Schema Validation**:

   ```bash
   python3 validate_server_json.py
   ```

3. **Build Test**:

   ```bash
   uv build
   ```

4. **Import Test**:
   ```bash
   python3 -c "import vector_memory; print('OK')"
   ```

### Integration Testing

Test with actual MCP client:

```bash
# Start server
uv run vector_memory.py

# In another terminal, test with MCP inspector or client
```

### Common Local Testing Issues

#### Issue: `spawn uv ENOENT`
**Cause**: Claude Desktop can't find the `uv` command in its PATH.

**Solution**: Use absolute path to `uv`:
```bash
which uv
# Use the output (e.g., /Users/username/.pyenv/shims/uv) in config
```

#### Issue: `Unexpected non-whitespace character after JSON`
**Cause**: Something is writing non-JSON to stdout, breaking MCP protocol.

**Solutions**:
1. Add environment variables to suppress UV output:
   ```json
   "env": {
     "UV_LINK_MODE": "copy",
     "UV_NO_PROGRESS": "1",
     "PYTHONUNBUFFERED": "1"
   }
   ```

2. Ensure logging goes to stderr (already configured in code)

3. Check for any `print()` statements or warnings going to stdout

#### Issue: Server connects but first tool call is slow
**Cause**: Model loads on first call (background initialization).

**Expected**: First call takes 10-15 seconds, subsequent calls are instant.

**Verify**: Check that `_initialize_vector_store()` is using `run_in_executor()` for background loading.

### Test Scenarios

1. **Save and Recall**:

   - Save a file
   - Recall information from it
   - Verify correct content returned

2. **Duplicate Handling**:

   - Save a file
   - Modify the file
   - Save again
   - Verify only one version exists

3. **Multi-Format**:

   - Save PDF, TXT, and MD files
   - Verify all are searchable
   - Check chunk sizes are optimized

4. **Memory Management**:
   - Use `vector-memory-manage list`
   - Use `vector-memory-cleanup stats`
   - Verify accurate counts

## Publishing Workflow

### Automated Publishing (Recommended)

1. **Make changes** to code
2. **Update version** in `pyproject.toml` and `server.json`
3. **Commit changes**: `git commit -am "feat: description"`
4. **Push to main**: `git push`
5. **Create tag**: `git tag v0.x.x`
6. **Push tag**: `git push origin v0.x.x`
7. **GitHub Actions** automatically:
   - Builds package
   - Publishes to PyPI
   - Publishes to MCP Registry

### Version Numbering

Follow Semantic Versioning (SemVer):

- **Major** (1.0.0): Breaking changes
- **Minor** (0.1.0): New features, backward compatible
- **Patch** (0.0.1): Bug fixes

### Pre-Release Checklist

- [ ] All tests pass
- [ ] Documentation updated (README.md, USAGE.md)
- [ ] Version bumped in pyproject.toml and server.json
- [ ] CHANGELOG updated (if exists)
- [ ] No uncommitted changes

## Key Constraints

1. **MCP Protocol**: stdout must be clean JSON only (no print statements)
2. **Redis Required**: Server won't work without Redis running
3. **Python 3.12+**: Uses modern type hints and features
4. **Absolute Paths**: All file paths converted to absolute for consistency
5. **Async Functions**: MCP tools must be async
6. **FastMCP Framework**: Must use FastMCP decorators and patterns

## Troubleshooting Guide for Agents

### Issue: Import Errors

**Cause**: Missing dependencies
**Solution**: Run `uv sync` to install all dependencies

### Issue: Redis Connection Error

**Cause**: Redis not running
**Solution**: Start Redis with `brew services start redis` or `docker run -d -p 6379:6379 redis`

### Issue: Model Download Slow

**Cause**: First-time download of embedding model (~80MB)
**Solution**: This is normal, only happens once

### Issue: JSON Parse Errors in MCP Client

**Cause**: Library logging to stdout
**Solution**: Ensure logging suppression is active in vector_memory.py:

```python
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
```

### Issue: Workflow Not Triggering

**Cause**: No tag pushed
**Solution**: Workflow only runs on tag push (`v*`), not regular commits

## Resources

- **MCP Documentation**: https://modelcontextprotocol.io/
- **FastMCP**: https://github.com/jlowin/fastmcp
- **LangChain Redis**: https://python.langchain.com/docs/integrations/vectorstores/redis
- **Sentence Transformers**: https://www.sbert.net/
- **Redis**: https://redis.io/docs/

---
