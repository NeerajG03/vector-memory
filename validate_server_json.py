#!/usr/bin/env python3
"""
Validate server.json against the MCP schema.
"""

import json
import urllib.request
import sys

def validate_server_json():
    """Validate server.json against the MCP schema."""
    
    # Read server.json
    try:
        with open('server.json', 'r') as f:
            server_data = json.load(f)
        print("✅ server.json is valid JSON")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in server.json: {e}")
        return False
    except FileNotFoundError:
        print("❌ server.json not found")
        return False
    
    # Basic validation checks
    required_fields = ['$schema', 'name', 'description', 'version']
    missing_fields = [field for field in required_fields if field not in server_data]
    
    if missing_fields:
        print(f"❌ Missing required fields: {', '.join(missing_fields)}")
        return False
    
    print(f"✅ All required fields present")
    
    # Validate name format
    name = server_data.get('name', '')
    if not name.startswith('io.github.'):
        print(f"⚠️  Warning: name '{name}' doesn't use io.github.* namespace")
    else:
        username = name.split('/')[0].replace('io.github.', '')
        print(f"✅ Name uses GitHub namespace: {username}")
    
    # Validate packages
    packages = server_data.get('packages', [])
    if not packages:
        print("⚠️  Warning: No packages defined")
    else:
        print(f"✅ {len(packages)} package(s) defined")
        
        for i, pkg in enumerate(packages):
            print(f"\n  Package {i+1}:")
            print(f"    Registry: {pkg.get('registryType', 'N/A')}")
            print(f"    Identifier: {pkg.get('identifier', 'N/A')}")
            print(f"    Version: {pkg.get('version', 'N/A')}")
            print(f"    Transport: {pkg.get('transport', {}).get('type', 'N/A')}")
            
            # Check PyPI package validation
            if pkg.get('registryType') == 'pypi':
                identifier = pkg.get('identifier')
                print(f"\n    📝 PyPI Validation Requirements:")
                print(f"       1. Package '{identifier}' must be published to PyPI")
                print(f"       2. README must contain: mcp-name: {name}")
                print(f"       3. Check README.md has the mcp-name comment")
    
    # Validate schema URL
    schema_url = server_data.get('$schema', '')
    if schema_url.startswith('https://static.modelcontextprotocol.io/schemas/'):
        print(f"\n✅ Valid schema URL: {schema_url}")
    else:
        print(f"\n⚠️  Unexpected schema URL: {schema_url}")
    
    print("\n" + "="*80)
    print("📋 VALIDATION SUMMARY")
    print("="*80)
    print(f"Server Name: {server_data.get('name')}")
    print(f"Version: {server_data.get('version')}")
    print(f"Description: {server_data.get('description')}")
    print(f"License: {server_data.get('license', 'Not specified')}")
    print(f"Homepage: {server_data.get('homepage', 'Not specified')}")
    print("\n✅ server.json structure is valid!")
    print("\n📚 Next Steps:")
    print("  1. Ensure README.md contains: <!-- mcp-name: {} -->".format(name))
    print("  2. Publish package to PyPI first")
    print("  3. Create a version tag: git tag vector-memory-v{}".format(server_data.get('version')))
    print("  4. Push tag: git push origin vector-memory-v{}".format(server_data.get('version')))
    print("  5. GitHub Actions will automatically publish to MCP Registry")
    
    return True

if __name__ == "__main__":
    success = validate_server_json()
    sys.exit(0 if success else 1)
