#!/usr/bin/env python3
"""
Quick cleanup script for Vector Memory

Simple script for common cleanup operations.
For advanced management, use manage_memory.py
"""

import sys
import os
import redis

# Constants
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
INDEX_NAME = "mcp_vector_memory"


def cleanup_all():
    """Delete all documents from memory."""
    try:
        redis_client = redis.Redis.from_url(REDIS_URL)

        # Check connection
        redis_client.ping()

        pattern = f"{INDEX_NAME}:*"
        keys = redis_client.keys(pattern)

        if not keys:
            print("✅ Memory is already empty.")
            return

        print(f"Found {len(keys)} document chunks in memory.")
        print("\n⚠️  WARNING: This will delete ALL documents!")
        response = input("Type 'yes' to confirm: ").strip().lower()

        if response != "yes":
            print("❌ Cancelled.")
            return

        deleted = redis_client.delete(*keys)

        # Drop index
        try:
            redis_client.execute_command(f"FT.DROPINDEX {INDEX_NAME}")
        except:
            pass

        print(f"\n✅ Deleted {deleted} document chunks from memory.")
        print("✅ Memory cleared successfully!")

    except redis.ConnectionError:
        print("❌ Cannot connect to Redis. Is it running?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cleanup_by_file(file_path):
    """Delete all chunks from a specific file."""
    try:
        redis_client = redis.Redis.from_url(REDIS_URL)
        redis_client.ping()

        pattern = f"{INDEX_NAME}:*"
        keys = redis_client.keys(pattern)

        if not keys:
            print("📭 Memory is empty.")
            return

        keys_to_delete = []

        for key in keys:
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

            if source_file and file_path in source_file:
                keys_to_delete.append(key)

        if not keys_to_delete:
            print(f"❌ No documents found for: {file_path}")
            print(
                "\nTip: Use absolute path or run 'python manage_memory.py search <term>' to find files"
            )
            return

        print(f"Found {len(keys_to_delete)} chunks from: {file_path}")
        response = input("Delete these? (yes/no): ").strip().lower()

        if response not in ["yes", "y"]:
            print("❌ Cancelled.")
            return

        deleted = redis_client.delete(*keys_to_delete)
        print(f"✅ Deleted {deleted} chunks from memory.")

    except redis.ConnectionError:
        print("❌ Cannot connect to Redis. Is it running?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def show_stats():
    """Show memory statistics."""
    try:
        redis_client = redis.Redis.from_url(REDIS_URL)
        redis_client.ping()

        pattern = f"{INDEX_NAME}:*"
        keys = redis_client.keys(pattern)

        if not keys:
            print("📭 Memory is empty - no documents stored.")
            return

        # Count unique files
        files = set()
        for key in keys:
            doc_data = redis_client.hgetall(key)

            # Try to get source_file from direct key first
            if b"source_file" in doc_data:
                files.add(doc_data[b"source_file"].decode("utf-8"))
            # Fallback to parsing _metadata_json
            elif b"_metadata_json" in doc_data:
                try:
                    metadata_str = doc_data[b"_metadata_json"].decode("utf-8")
                    import json

                    metadata = json.loads(metadata_str)
                    files.add(metadata.get("source_file", "unknown"))
                except:
                    pass

        print("\n📊 Memory Statistics:")
        print(f"   Total chunks: {len(keys)}")
        print(f"   Unique files: {len(files)}")
        print("\nRun 'uv run manage_memory.py' for detailed management.")

    except redis.ConnectionError:
        print("❌ Cannot connect to Redis. Is it running?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("\n🧹 Vector Memory Cleanup Tool")
        print("\nUsage:")
        print("  uv run cleanup.py all              # Delete all documents")
        print(
            "  uv run cleanup.py file <path>      # Delete documents from specific file"
        )
        print("  uv run cleanup.py stats            # Show memory statistics")
        print("\nFor advanced management:")
        print("  uv run manage_memory.py            # Interactive mode with search")
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "all":
        cleanup_all()
    elif command == "file" and len(sys.argv) > 2:
        cleanup_by_file(sys.argv[2])
    elif command == "stats":
        show_stats()
    else:
        print("❌ Invalid command. Run without arguments to see usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
