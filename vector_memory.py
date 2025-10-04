import os
import sys
import warnings
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
REDIS_URL = "redis://localhost:6379"
INDEX_NAME = "doc_chunks"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Initialize embeddings and vector store
embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
vector_store = RedisVectorStore(
    embeddings=embeddings,
    index_name=INDEX_NAME,
)


@mcp.tool()
async def save_to_memory(
    file_paths: list[str], chunk_size: int = 1000, chunk_overlap: int = 100
) -> str:
    """
    Save files and their contents to memory for later retrieval.

    Use this tool to load documents into memory so their content can be recalled later.
    Supports text files (.txt, .md) and PDF documents. The content is automatically
    organized to make future searches more effective.

    Args:
        file_paths: List of file paths to save to memory

    Returns:
        Confirmation message
    """
    import redis
    import json
    
    docs = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    
    # First, remove any existing documents from these file paths to avoid duplicates
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
                if b'source_file' in doc_data:
                    stored_path = doc_data[b'source_file'].decode('utf-8')
                    if stored_path == abs_path:
                        keys_to_delete.append(key)
                elif b'_metadata_json' in doc_data:
                    metadata_str = doc_data[b'_metadata_json'].decode('utf-8')
                    metadata = json.loads(metadata_str)
                    if metadata.get('source_file') == abs_path:
                        keys_to_delete.append(key)
            
            if keys_to_delete:
                redis_client.delete(*keys_to_delete)
        except Exception:
            # Continue even if deletion fails
            pass

    # Now process and add the new documents
    for file_path in file_paths:
        # Convert to absolute path
        abs_path = os.path.abspath(file_path)

        # Check if file exists
        if not os.path.exists(abs_path):
            return f"Error: File not found: {abs_path}"

        ext = os.path.splitext(abs_path)[1].lower()

        # Load document depending on type
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(abs_path)
            else:  # fallback to text
                loader = TextLoader(abs_path, encoding="utf-8")

            file_docs = loader.load()

            # Chunking
            chunks = splitter.split_documents(file_docs)

            # Add metadata (store absolute path)
            for chunk in chunks:
                chunk.metadata["source_file"] = abs_path

            docs.extend(chunks)
        except Exception as e:
            return f"Error processing {abs_path}: {str(e)}"

    # Store in Redis
    try:
        ids = vector_store.add_documents(docs)
        return f"✅ Successfully saved {len(file_paths)} file(s) to memory. Content is now available for recall."
    except Exception as e:
        return f"Error saving to memory: {str(e)}"


@mcp.tool()
async def recall_from_memory(query: str, k: int = 3) -> str:
    """
    Recall information from memory based on what you're looking for.

    Use this tool to retrieve relevant information that was previously saved.
    The memory will find and return the most relevant content related to your query,
    even if the exact words don't match.

    Args:
        query: What you want to recall or search for
        k: How many relevant pieces of information to return (default: 3)

    Returns:
        The most relevant information found in memory
    """
    try:
        results = vector_store.similarity_search(query, k=k)

        if not results:
            return "Nothing found in memory matching your query."

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


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
