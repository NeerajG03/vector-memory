# Vector Memory MCP Server

<!-- mcp-name: io.github.NeerajG03/vector-memory -->

An MCP server that gives AI assistants the ability to save and recall information from files. Works like a long-term memory system where you can store documents and retrieve relevant information later using natural language.

## Features

This server exposes two main tools:

1. **`save_to_memory`** - Save files to memory for later retrieval

   - Supports PDF, TXT, and MD files
   - Accepts both absolute and relative file paths (converts all to absolute)
   - Automatically processes and organizes content for efficient recall
   - Preserves source file information

2. **`recall_from_memory`** - Recall information from memory
   - Find relevant content using natural language queries
   - Returns the most relevant information even without exact word matches
   - Shows absolute paths to source files for each result

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

## Installation

The dependencies are already configured in `pyproject.toml`. Install them using:

```bash
uv sync
```

### Verify Your Setup

Before running the server, test your configuration:

```bash
uv run test_connection.py
```

This will verify:

- ✅ All required packages are installed
- ✅ Redis is running and accessible
- ✅ Embedding model loads correctly

## Usage

### Running the Server Standalone

You can test the server directly:

```bash
uv run vector_memory.py
```

### Integrating with Claude or Windsurf

Add this configuration to your MCP config file at:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "vector-memory": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/TO/mcp-servers/servers/vector-memory",
        "run",
        "vector_memory.py"
      ]
    }
  }
}
```

**Important**: Replace `/ABSOLUTE/PATH/TO` with the full path to your project directory.

After updating the config, restart Claude for Desktop or Windsurf.

### Integrating with Codex CLI

For Codex CLI, add this to your MCP configuration file (typically `~/.config/codex/mcp_config.toml` or similar):

```toml
[servers.vector-memory]
command = "uv"
args = [
  "--directory",
  "/ABSOLUTE/PATH/TO/mcp-servers/servers/vector-memory",
  "run",
  "vector_memory.py"
]
```

**Important**: Replace `/ABSOLUTE/PATH/TO` with the full path to your project directory.

After updating the config, restart or reload Codex CLI.

## Tool Examples

### Saving to Memory

In Claude/Windsurf/Codex, you can ask:

```
Save these files to memory:
- /path/to/document1.pdf
- /path/to/notes.md
```

or simply:

```
Remember the contents of /path/to/my-notes.txt
```

### Recalling from Memory

```
What do you remember about machine learning algorithms?
```

or:

```
Recall information about project deadlines
```

## Configuration

You can customize the following constants in `vector_memory.py`:

- `REDIS_URL`: Redis connection string (default: `redis://localhost:6379`)
- `INDEX_NAME`: Vector store index name (default: `doc_chunks`)
- `MODEL_NAME`: Embedding model (default: `sentence-transformers/all-MiniLM-L6-v2`)

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

Two scripts are provided to manage stored documents:

### Quick Cleanup (`cleanup.py`)

Simple commands for common operations:

```bash
# Show memory statistics
uv run cleanup.py stats

# Delete all documents from memory
uv run cleanup.py all

# Delete documents from a specific file
uv run cleanup.py file /path/to/file.pdf
```

### Advanced Management (`manage_memory.py`)

Interactive tool with search and selective deletion:

```bash
# Interactive mode
uv run manage_memory.py

# Command-line usage
uv run manage_memory.py list                    # List all files
uv run manage_memory.py search <term>           # Search by filename
uv run manage_memory.py delete-file <path>      # Delete specific file
uv run manage_memory.py delete-all              # Delete everything
```

**Interactive Mode Features:**

- 📋 List all documents grouped by source file
- 🔍 Search documents by filename or path
- 🗑️ Selectively delete documents with confirmation
- 📊 See chunk counts per file

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
