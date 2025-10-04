#!/usr/bin/env python3
"""
Quick test script to verify Redis connection and embedding model setup.
Run this before starting the MCP server to ensure everything is configured correctly.
"""

import sys


def test_redis():
    """Test Redis connection."""
    try:
        import redis

        r = redis.Redis.from_url("redis://localhost:6379")
        if r.ping():
            print("✅ Redis connection: SUCCESS")
            return True
        else:
            print("❌ Redis connection: FAILED")
            return False
    except Exception as e:
        print(f"❌ Redis connection: FAILED - {e}")
        print("   Make sure Redis is running: docker run -d -p 6379:6379 redis:latest")
        return False


def test_embeddings():
    """Test embedding model loading."""
    try:
        from langchain_huggingface.embeddings import HuggingFaceEmbeddings

        print("⏳ Loading embedding model (this may take a moment)...")
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        # Test embedding a simple text
        test_embedding = embeddings.embed_query("test")
        if test_embedding and len(test_embedding) > 0:
            print(f"✅ Embedding model: SUCCESS (dimension: {len(test_embedding)})")
            return True
        else:
            print("❌ Embedding model: FAILED")
            return False
    except Exception as e:
        print(f"❌ Embedding model: FAILED - {e}")
        return False


def test_imports():
    """Test all required imports."""
    try:
        from langchain_redis import RedisVectorStore
        from langchain_community.document_loaders import TextLoader, PyPDFLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from mcp.server.fastmcp import FastMCP

        print("✅ All imports: SUCCESS")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        print("   Run: uv sync")
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("Vector Memory MCP Server - Connection Test")
    print("=" * 50)
    print()

    results = []
    results.append(("Imports", test_imports()))
    results.append(("Redis", test_redis()))
    results.append(("Embeddings", test_embeddings()))

    print()
    print("=" * 50)
    print("Test Summary")
    print("=" * 50)

    all_passed = all(result[1] for result in results)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:20} {status}")

    print()
    if all_passed:
        print("🎉 All tests passed! Your server is ready to run.")
        print("   Start it with: uv run vector_memory.py")
        sys.exit(0)
    else:
        print(
            "⚠️  Some tests failed. Please fix the issues above before running the server."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
