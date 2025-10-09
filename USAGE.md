# Usage Guide

Complete guide for using the Vector Memory MCP server.

## Table of Contents

- [Installation Methods](#installation-methods)
- [Running the Server](#running-the-server)
- [Using the Tools](#using-the-tools)
- [Memory Management](#memory-management)
- [Configuration](#configuration)
- [Examples](#examples)

## Installation Methods

### Option 1: Via pip (Recommended for Users)

```bash
pip install mcp-server-vector-memory
```

### Option 2: Via uvx (Isolated Environment)

```bash
uvx mcp-server-vector-memory
```

### Option 3: From Source (Development)

```bash
git clone https://github.com/NeerajG03/vector-memory.git
cd vector-memory
uv sync
```

## Running the Server

### Standalone Testing

```bash
# After pip install
mcp-server-vector-memory

# From source
uv run vector_memory.py
```

### Integrating with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vector-memory": {
      "command": "uvx",
      "args": ["mcp-server-vector-memory"]
    }
  }
}
```

Or if installed via pip:

```json
{
  "mcpServers": {
    "vector-memory": {
      "command": "python3",
      "args": ["-m", "vector_memory"]
    }
  }
}
```

### Integrating with Windsurf

Same configuration as Claude Desktop.

### Integrating with Codex CLI

Add to `~/.config/codex/mcp_config.toml`:

```toml
[servers.vector-memory]
command = "uvx"
args = ["mcp-server-vector-memory"]
```

## Using the Tools

The server provides three main tools:

### 1. `save_to_memory` - Remember Files

Save files to memory for later recall.

**Examples:**

```
"Remember the contents of /path/to/notes.txt"
"Save these files to memory: /path/to/doc1.pdf and /path/to/doc2.md"
```

**What it does:**
- Automatically removes old versions of the same file
- Optimizes chunk size based on file type (PDF, Markdown, Text)
- Stores absolute paths for reliable recall

### 2. `recall_from_memory` - Recall Information

Retrieve relevant information using natural language.

**Examples:**

```
"What do you remember about project deadlines?"
"Recall information about machine learning algorithms"
"What's in memory about the API documentation?"
```

**Parameters:**
- `what_to_remember`: What you're trying to recall
- `how_many_results`: Number of results to return (default: 3)

## Memory Management

### Quick Cleanup Commands

After `pip install`:

```bash
# Show statistics
vector-memory-cleanup stats

# Delete all documents
vector-memory-cleanup all

# Delete specific file
vector-memory-cleanup file /path/to/file.pdf
```

From source:

```bash
uv run cleanup.py stats
uv run cleanup.py all
uv run cleanup.py file /path/to/file.pdf
```

### Advanced Management Tool

After `pip install`:

```bash
# Interactive mode
vector-memory-manage

# Command-line usage
vector-memory-manage list                    # List all files
vector-memory-manage search <term>           # Search by filename
vector-memory-manage delete-file <path>      # Delete specific file
vector-memory-manage delete-all              # Delete everything
```

From source:

```bash
uv run manage_memory.py                      # Interactive mode
uv run manage_memory.py list
uv run manage_memory.py search <term>
uv run manage_memory.py delete-file <path>
uv run manage_memory.py delete-all
```

**Interactive Mode Features:**
- 📋 List all documents grouped by source file
- 🔍 Search documents by filename or path
- 🗑️ Selectively delete documents with confirmation
- 📊 See chunk counts per file

## Configuration

### Environment Variables

**`REDIS_URL`** - Redis connection string (default: `redis://localhost:6379/0`)

```bash
# Use different Redis database
export REDIS_URL=redis://localhost:6379/1

# With management tools
REDIS_URL=redis://localhost:6379/1 vector-memory-manage list
REDIS_URL=redis://localhost:6379/1 vector-memory-cleanup stats
```

**In Claude Desktop config:**

```json
{
  "mcpServers": {
    "vector-memory": {
      "command": "uvx",
      "args": ["mcp-server-vector-memory"],
      "env": {
        "REDIS_URL": "redis://localhost:6379/1"
      }
    }
  }
}
```

### Data Isolation

The server uses multiple layers of isolation:

1. **Database number**: Uses Redis DB 0 by default (configurable via URL)
2. **Index namespace**: All keys prefixed with `mcp_vector_memory:*`
3. **Metadata tagging**: Each document tagged with source file path

This ensures your vector memory data won't conflict with other Redis applications.

### Chunk Size Optimization

The server automatically optimizes chunk sizes based on file type:

- **PDF files**: 1500 characters, 200 overlap (structured content)
- **Markdown files**: 1200 characters, 150 overlap (preserve structure)
- **Text files**: 1000 characters, 100 overlap (standard)

No manual configuration needed!

## Examples

### Example 1: Document Research

```
User: "Save /Users/me/research/paper1.pdf to memory"
Assistant: ✅ Successfully saved 1 file(s) to memory. Content is now available for recall.

User: "What do you remember about neural networks?"
Assistant: [Returns relevant sections from paper1.pdf]
```

### Example 2: Project Notes

```
User: "Remember these files:
- /Users/me/project/notes.md
- /Users/me/project/requirements.txt
- /Users/me/project/README.md"
Assistant: ✅ Successfully saved 3 file(s) to memory.

User: "What were the project requirements?"
Assistant: [Returns content from requirements.txt]
```

### Example 3: Updating Files

```
User: "Save /Users/me/notes.txt to memory"
Assistant: ✅ Successfully saved 1 file(s) to memory.

[User edits notes.txt]

User: "Save /Users/me/notes.txt to memory again"
Assistant: ✅ Successfully saved 1 file(s) to memory.
[Old version automatically removed, new version saved]
```

### Example 4: Managing Memory

```bash
# See what's in memory
vector-memory-manage list

# Output:
# 📚 Memory Contents (3 files, 45 chunks)
# 
# 📄 /Users/me/project/notes.md (15 chunks)
# 📄 /Users/me/project/README.md (12 chunks)
# 📄 /Users/me/research/paper1.pdf (18 chunks)

# Search for specific files
vector-memory-manage search "project"

# Delete a specific file
vector-memory-manage delete-file /Users/me/project/notes.md
```

## Troubleshooting

### Redis Connection Error

Ensure Redis is running:

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Start Redis (macOS with Homebrew)
brew services start redis

# Start Redis (Docker)
docker run -d -p 6379:6379 redis:latest
```

### Model Download

The first time you run the server, it will download the embedding model (~80MB). This is normal and only happens once.

### File Not Found Errors

The server accepts both absolute and relative file paths, but automatically converts them to absolute paths for storage. If a file is not found, check that the path is correct.

### Memory Not Persisting

Make sure you're using the same Redis database. Check your `REDIS_URL` environment variable matches across all tools.

## Best Practices

1. **Use absolute paths** when possible for clarity
2. **Update files** by re-saving them (old versions are automatically removed)
3. **Use different Redis databases** for different projects
4. **Regular cleanup** - use `vector-memory-cleanup stats` to monitor memory usage
5. **Descriptive queries** - use natural language when recalling information

## Advanced Usage

### Multiple Redis Instances

```bash
# Project A - use database 0
REDIS_URL=redis://localhost:6379/0 mcp-server-vector-memory

# Project B - use database 1  
REDIS_URL=redis://localhost:6379/1 mcp-server-vector-memory
```

### Remote Redis

```bash
export REDIS_URL=redis://username:password@remote-host:6379/0
mcp-server-vector-memory
```

### Custom Embedding Model

Edit `vector_memory.py` and change:

```python
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
```

to any compatible sentence-transformers model.

## Getting Help

- **Documentation**: [README.md](README.md)
- **Issues**: https://github.com/NeerajG03/vector-memory/issues
- **MCP Registry**: https://mcp.run/server/io.github.NeerajG03/vector-memory
