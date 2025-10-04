# Vector Memory MCP Server

<!-- mcp-name: io.github.NeerajG03/vector-memory -->

An MCP server that gives AI assistants the ability to save and recall information from files. Works like a long-term memory system where you can store documents and retrieve relevant information later using natural language.

**📖 [Complete Usage Guide](USAGE.md)** | **🔗 [PyPI Package](https://pypi.org/project/mcp-server-vector-memory/)** | **🌐 [MCP Registry](https://mcp.run/server/io.github.NeerajG03/vector-memory)**

## Features

- 🧠 **Semantic Memory**: Save and recall file contents using natural language
- 📄 **Multi-Format Support**: PDF, TXT, and Markdown files
- 🔄 **Auto-Update**: Re-saving a file automatically removes old versions
- 🎯 **Smart Chunking**: Optimizes chunk size based on file type
- 🔍 **Semantic Search**: Find information even without exact word matches
- 🗂️ **Memory Management**: Built-in tools to list, search, and clean up memory
- 🔒 **Data Isolation**: Separate Redis databases and namespaces

## Prerequisites

- Python 3.12 or higher
- Redis server running locally on port 6379
- UV package manager

### Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or using Homebrew on macOS
brew install redis
brew services start redis
```

## Quick Start

### Installation

```bash
# Via pip
pip install mcp-server-vector-memory

# Via uvx (isolated environment)
uvx mcp-server-vector-memory

# From source
git clone https://github.com/NeerajG03/vector-memory.git
cd vector-memory
uv sync
```

### Basic Usage

**After pip install:**
```bash
# Run the server
mcp-server-vector-memory

# Manage memory
vector-memory-manage list
vector-memory-cleanup stats
```

**From source:**
```bash
uv run vector_memory.py
uv run manage_memory.py list
uv run cleanup.py stats
```

### Integration with AI Clients

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):
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

**Codex CLI** (`~/.config/codex/mcp_config.toml`):
```toml
[servers.vector-memory]
command = "uvx"
args = ["mcp-server-vector-memory"]
```

See **[USAGE.md](USAGE.md)** for complete integration examples and advanced configuration.

## Configuration

You can customize the server using environment variables or by editing `vector_memory.py`:

### Environment Variables

- `REDIS_URL`: Redis connection string (default: `redis://localhost:6379/0`)
  - Format: `redis://host:port/db_number`
  - Example: `redis://localhost:6379/1` (use database 1)

### Constants in Code

- `INDEX_NAME`: Vector store index name (default: `mcp_vector_memory`)
  - All keys are prefixed with this namespace to avoid conflicts
- `MODEL_NAME`: Embedding model (default: `sentence-transformers/all-MiniLM-L6-v2`)

### Data Isolation

The server uses multiple layers of isolation:

1. **Database number**: Uses Redis DB 0 by default (configurable via URL)
2. **Index namespace**: All keys prefixed with `mcp_vector_memory:*`
3. **Metadata tagging**: Each document tagged with source file path

This ensures your vector memory data won't conflict with other Redis applications.

## Architecture

```
┌─────────────────┐
│  Claude/Client  │
└────────┬────────┘
         │ MCP Protocol
         │
┌────────▼────────┐
│  Vector Memory  │
│   MCP Server    │
└────────┬────────┘
         │
         ├─────► HuggingFace Embeddings
         │
         └─────► Redis Vector Store
```

## Memory Management

Two management tools are included:

- **`vector-memory-manage`** - Interactive tool with search and selective deletion
- **`vector-memory-cleanup`** - Quick cleanup commands

See **[USAGE.md](USAGE.md#memory-management)** for complete documentation and examples.

## Development

To run in development mode with auto-reload:

```bash
uv run --reload vector_memory.py
```

## Troubleshooting

### Redis Connection Error

Ensure Redis is running:

```bash
redis-cli ping
# Should return: PONG
```

### Model Download

The first time you run the server, it will download the embedding model (~80MB). This is normal and only happens once.

### File Not Found Errors

The server accepts both absolute and relative file paths, but automatically converts them to absolute paths for storage. If a file is not found, check that the path is correct relative to where the server is running.

## Path Handling

- **Input**: Accepts both absolute (`/full/path/to/file.txt`) and relative (`./docs/file.txt`) paths
- **Storage**: All paths are converted to absolute paths before being saved to memory
- **Output**: `recall_from_memory` always returns absolute paths to source files

This ensures consistent path references regardless of how files were originally added to memory.
