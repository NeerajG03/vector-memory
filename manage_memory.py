#!/usr/bin/env python3
"""
Memory Management Script for Vector Memory MCP Server

This script helps you manage the documents stored in Redis vector memory.
You can list, search, and delete documents by file path.
"""

import sys
import redis
from langchain_redis import RedisVectorStore
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from collections import defaultdict

# Constants (must match vector_memory.py)
import os

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
INDEX_NAME = "mcp_vector_memory"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_vector_store():
    """Initialize and return the vector store."""
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    return RedisVectorStore(
        embeddings=embeddings,
        redis_url=REDIS_URL,
        index_name=INDEX_NAME,
    )


def get_redis_client():
    """Get direct Redis client for low-level operations."""
    return redis.Redis.from_url(REDIS_URL)


def list_all_documents():
    """List all documents grouped by source file."""
    try:
        vector_store = get_vector_store()
        redis_client = get_redis_client()

        # Get all keys matching our index pattern
        pattern = f"{INDEX_NAME}:*"
        keys = redis_client.keys(pattern)

        if not keys:
            print("📭 Memory is empty - no documents found.")

        # Group by source file
        files_map = defaultdict(list)

        for key in keys:
            key_str = key.decode("utf-8")
            # Get the document metadata
            doc_data = redis_client.hgetall(key)

            # Try to get source_file from direct key first (faster)
            if b"source_file" in doc_data:
                source_file = doc_data[b"source_file"].decode("utf-8")
                files_map[source_file].append(key_str)
            # Fallback to parsing _metadata_json
            elif b"_metadata_json" in doc_data:
                metadata_str = doc_data[b"_metadata_json"].decode("utf-8")
                import json

                metadata = json.loads(metadata_str)
                source_file = metadata.get("source_file", "unknown")
                files_map[source_file].append(key_str)

        print("\n" + "=" * 80)
        print("  MEMORY CONTENTS")
        print("=" * 80)
        print(f"\nTotal documents: {len(keys)}")
        print(f"Total source files: {len(files_map)}")
        print("\n" + "-" * 80)

        for source_file, doc_keys in sorted(files_map.items()):
            print(f"\n📄 {source_file}")
            print(f"   Chunks: {len(doc_keys)}")

        print("\n" + "=" * 80 + "\n")
        return files_map

    except Exception as e:
        print(f"❌ Error listing documents: {e}")
        return {}


def search_by_filename(search_term):
    """Search for documents by filename or path pattern."""
    try:
        vector_store = get_vector_store()
        redis_client = get_redis_client()

        pattern = f"{INDEX_NAME}:*"
        keys = redis_client.keys(pattern)

        if not keys:
            print("📭 Memory is empty - no documents found.")
            return []

        matching_files = defaultdict(list)

        for key in keys:
            key_str = key.decode("utf-8")
            doc_data = redis_client.hgetall(key)

            source_file = None
            # Try to get source_file from direct key first
            if b"source_file" in doc_data:
                source_file = doc_data[b"source_file"].decode("utf-8")
            # Fallback to parsing _metadata_json
            elif b"_metadata_json" in doc_data:
                metadata_str = doc_data[b"_metadata_json"].decode("utf-8")
                import json

                metadata = json.loads(metadata_str)
                source_file = metadata.get("source_file", "unknown")

            # Check if search term matches
            if source_file and search_term.lower() in source_file.lower():
                matching_files[source_file].append(key_str)

        if not matching_files:
            print(f"\n🔍 No files found matching: '{search_term}'")
            return []

        print("\n" + "=" * 80)
        print(f"🔍 SEARCH RESULTS for: '{search_term}'")
        print("=" * 80)

        for source_file, doc_keys in sorted(matching_files.items()):
            print(f"\n📄 {source_file}")
            print(f"   Chunks: {len(doc_keys)}")

        print("\n" + "=" * 80 + "\n")
        return matching_files

    except Exception as e:
        print(f"❌ Error searching: {e}")
        return []


def delete_by_file(file_path, confirm=True):
    """Delete all chunks from a specific file."""
    try:
        redis_client = get_redis_client()

        pattern = f"{INDEX_NAME}:*"
        keys = redis_client.keys(pattern)

        keys_to_delete = []

        for key in keys:
            key_str = key.decode("utf-8")
            doc_data = redis_client.hgetall(key)

            source_file = None
            # Try to get source_file from direct key first
            if b"source_file" in doc_data:
                source_file = doc_data[b"source_file"].decode("utf-8")
            # Fallback to parsing _metadata_json
            elif b"_metadata_json" in doc_data:
                metadata_str = doc_data[b"_metadata_json"].decode("utf-8")
                import json

                metadata = json.loads(metadata_str)
                source_file = metadata.get("source_file", "")

            if source_file == file_path:
                keys_to_delete.append(key)

        if not keys_to_delete:
            print(f"\n⚠️  No documents found for file: {file_path}")
            return False

        print(f"\n📄 File: {file_path}")
        print(f"📦 Chunks to delete: {len(keys_to_delete)}")

        if confirm:
            response = input("\n⚠️  Delete these documents? (yes/no): ").strip().lower()
            if response not in ["yes", "y"]:
                print("❌ Cancelled.")
                return False

        # Delete the keys
        deleted = redis_client.delete(*keys_to_delete)
        print(f"\n✅ Deleted {deleted} document chunks from memory.")
        return True

    except Exception as e:
        print(f"❌ Error deleting documents: {e}")
        return False


def delete_all(confirm=True):
    """Delete all documents from memory."""
    try:
        redis_client = get_redis_client()

        pattern = f"{INDEX_NAME}:*"
        keys = redis_client.keys(pattern)

        if not keys:
            print("\n📭 Memory is already empty.")
            return True

        print(f"\n⚠️  WARNING: This will delete ALL documents from memory!")
        print(f"📦 Total chunks to delete: {len(keys)}")

        if confirm:
            response = input(
                "\n⚠️  Are you absolutely sure? Type 'DELETE ALL' to confirm: "
            ).strip()
            if response != "DELETE ALL":
                print("❌ Cancelled.")
                return False

        # Delete all keys
        deleted = redis_client.delete(*keys)

        # Also drop the index if it exists
        try:
            redis_client.execute_command(f"FT.DROPINDEX {INDEX_NAME}")
            print(f"\n✅ Deleted {deleted} documents and dropped index.")
        except:
            print(f"\n✅ Deleted {deleted} documents from memory.")

        return True

    except Exception as e:
        print(f"❌ Error deleting all documents: {e}")
        return False


def interactive_mode():
    """Interactive menu for managing memory."""
    while True:
        print("\n" + "=" * 80)
        print("🧠 VECTOR MEMORY MANAGEMENT")
        print("=" * 80)
        print("\n1. List all documents in memory")
        print("2. Search documents by filename")
        print("3. Delete documents from specific file")
        print("4. Delete ALL documents (careful!)")
        print("5. Exit")
        print("\n" + "=" * 80)

        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == "1":
            list_all_documents()

        elif choice == "2":
            search_term = input("\n🔍 Enter filename or path to search: ").strip()
            if search_term:
                results = search_by_filename(search_term)
                if results:
                    delete_choice = (
                        input("\n❓ Delete any of these files? (yes/no): ")
                        .strip()
                        .lower()
                    )
                    if delete_choice in ["yes", "y"]:
                        for file_path in results.keys():
                            print(f"\n📄 {file_path}")
                            confirm = (
                                input("   Delete this file? (yes/no): ").strip().lower()
                            )
                            if confirm in ["yes", "y"]:
                                delete_by_file(file_path, confirm=False)

        elif choice == "3":
            file_path = input("\n📄 Enter full file path to delete: ").strip()
            if file_path:
                delete_by_file(file_path, confirm=True)

        elif choice == "4":
            delete_all(confirm=True)

        elif choice == "5":
            print("\n👋 Goodbye!")
            break

        else:
            print("\n❌ Invalid choice. Please try again.")


def main():
    """Main entry point."""
    print("\n🧠 Vector Memory Management Tool")
    print("=" * 80)

    # Check Redis connection
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Cannot connect to Redis: {e}")
        print("\nMake sure Redis is running:")
        print("  docker run -d -p 6379:6379 redis:latest")
        sys.exit(1)

    # Check if running with arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "list":
            list_all_documents()
        elif command == "search" and len(sys.argv) > 2:
            search_by_filename(sys.argv[2])
        elif command == "delete-file" and len(sys.argv) > 2:
            delete_by_file(sys.argv[2], confirm=True)
        elif command == "delete-all":
            delete_all(confirm=True)
        else:
            print("\nUsage:")
            print("  python manage_memory.py                    # Interactive mode")
            print("  python manage_memory.py list               # List all documents")
            print("  python manage_memory.py search <term>      # Search by filename")
            print("  python manage_memory.py delete-file <path> # Delete specific file")
            print("  python manage_memory.py delete-all         # Delete everything")
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
