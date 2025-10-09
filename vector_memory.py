import os
import sys
import warnings
import asyncio
from typing import Any
from mcp.server.fastmcp import FastMCP
from langchain_redis import RedisVectorStore
from langchain.schema import Document
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader

# Suppress warnings and redirect logging to stderr
warnings.filterwarnings("ignore")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# Initialize FastMCP server
mcp = FastMCP("vector-memory")

# Constants
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")  # DB 0 by default
INDEX_NAME = "mcp_vector_memory"  # Unique namespace
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Lazy initialization cache
_embeddings = None
_vector_store = None
_init_lock = asyncio.Lock()
_init_task = None


async def _initialize_vector_store() -> None:
    """
    Initialize the vector store in the background.

    This runs asynchronously after server startup to pre-load the model
    without blocking the initial connection.
    """
    global _embeddings, _vector_store

    async with _init_lock:
        if _vector_store is None:
            # Run the blocking initialization in a thread pool
            loop = asyncio.get_event_loop()
            _embeddings = await loop.run_in_executor(
                None, lambda: HuggingFaceEmbeddings(model_name=MODEL_NAME)
            )
            _vector_store = RedisVectorStore(
                embeddings=_embeddings,
                index_name=INDEX_NAME,
            )


async def _get_vector_store() -> RedisVectorStore:
    """
    Get or initialize the vector store (lazy initialization with background loading).

    This ensures the embedding model is loaded in the background after startup,
    so the first tool call doesn't experience delays.

    Returns:
        Initialized RedisVectorStore instance
    """
    global _vector_store, _init_task

    # If initialization is already complete, return immediately
    if _vector_store is not None:
        return _vector_store

    # Start background initialization if not already started
    if _init_task is None:
        _init_task = asyncio.create_task(_initialize_vector_store())

    # Wait for background initialization to complete
    await _init_task
    return _vector_store


def _get_optimal_chunk_size(file_extension: str) -> tuple[int, int]:
    """
    Determine optimal chunk size and overlap based on file type.

    Args:
        file_extension: File extension (e.g., '.pdf', '.txt', '.md')

    Returns:
        Tuple of (chunk_size, chunk_overlap)
    """
    # PDFs often have more structured content, use larger chunks
    if file_extension == ".pdf":
        return (1500, 200)
    # Markdown files benefit from preserving structure
    elif file_extension == ".md":
        return (1200, 150)
    # Text files - standard chunking
    else:
        return (1000, 100)


def _remove_existing_documents(file_paths: list[str]) -> None:
    """
    Remove existing documents from Redis for the given file paths.

    This prevents duplicate content when re-saving the same file.

    Args:
        file_paths: List of file paths to remove from memory
    """
    import redis
    import json

    redis_client = redis.Redis.from_url(REDIS_URL)

    for file_path in file_paths:
        abs_path = os.path.abspath(file_path)

        try:
            pattern = f"{INDEX_NAME}:*"
            keys = redis_client.keys(pattern)
            keys_to_delete = []

            for key in keys:
                doc_data = redis_client.hgetall(key)
                # Check both possible metadata storage formats
                if b"source_file" in doc_data:
                    stored_path = doc_data[b"source_file"].decode("utf-8")
                    if stored_path == abs_path:
                        keys_to_delete.append(key)
                elif b"_metadata_json" in doc_data:
                    metadata_str = doc_data[b"_metadata_json"].decode("utf-8")
                    metadata = json.loads(metadata_str)
                    if metadata.get("source_file") == abs_path:
                        keys_to_delete.append(key)

            if keys_to_delete:
                redis_client.delete(*keys_to_delete)
        except Exception:
            # Continue even if deletion fails
            pass


@mcp.tool()
async def save_to_memory(file_paths: list[str]) -> str:
    """
    Remember the contents of files for later recall.

    Use this to store documents in memory so you can recall their content later.
    Supports text files (.txt, .md) and PDF documents. The system automatically
    organizes content for optimal recall.

    Args:
        file_paths: Paths to files you want to remember

    Returns:
        Confirmation message
    """
    # Remove any existing documents from these file paths to avoid duplicates
    _remove_existing_documents(file_paths)

    docs = []

    for file_path in file_paths:
        # Convert to absolute path
        abs_path = os.path.abspath(file_path)

        # Check if file exists
        if not os.path.exists(abs_path):
            return f"Error: File not found: {abs_path}"

        ext = os.path.splitext(abs_path)[1].lower()

        # Get optimal chunk size for this file type
        chunk_size, chunk_overlap = _get_optimal_chunk_size(ext)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

        # Load document depending on type
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(abs_path)
            else:  # fallback to text
                loader = TextLoader(abs_path, encoding="utf-8")

            file_docs = loader.load()

            # Chunking with optimal settings
            chunks = splitter.split_documents(file_docs)

            # Add metadata (store absolute path)
            for chunk in chunks:
                chunk.metadata["source_file"] = abs_path

            docs.extend(chunks)
        except Exception as e:
            return f"Error processing {abs_path}: {str(e)}"

    # Store in Redis
    try:
        vector_store = await _get_vector_store()
        ids = vector_store.add_documents(docs)
        return f"✅ Successfully saved {len(file_paths)} file(s) to memory. Content is now available for recall."
    except Exception as e:
        return f"Error saving to memory: {str(e)}"


@mcp.tool()
async def recall_from_memory(what_to_remember: str, how_many_results: int = 3) -> str:
    """
    Recall information from memory.

    Use this to retrieve relevant information that was previously saved.
    The memory will find and return the most relevant content, even if the
    exact words don't match.

    Args:
        what_to_remember: What you're trying to recall or remember
        how_many_results: How many relevant memories to return (default: 3)

    Returns:
        The most relevant information found in memory
    """
    try:
        vector_store = await _get_vector_store()
        results = vector_store.similarity_search(what_to_remember, k=how_many_results)

        if not results:
            return "Nothing found in memory matching what you're looking for."

        output = []
        for i, doc in enumerate(results, 1):
            source_file = doc.metadata.get("source_file", "unknown")
            content = doc.page_content
            output.append(
                f"**Result {i}**\nSource: {source_file}\n\nContent:\n{content}\n"
            )

        return "\n---\n".join(output)
    except Exception as e:
        return f"Error recalling from memory: {str(e)}"


async def main():
    """Run the MCP server with background initialization."""
    global _init_task

    # Start background initialization immediately
    if _init_task is None:
        _init_task = asyncio.create_task(_initialize_vector_store())

    # Run the server
    await mcp.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())
