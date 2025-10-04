# Publishing to MCP Registry

This guide explains how to publish the Vector Memory MCP server to the official MCP registry.

## Overview

We use **automated publishing via GitHub Actions** which:
- ✅ Builds and publishes to PyPI automatically
- ✅ Publishes to MCP Registry using GitHub OIDC (no secrets needed!)
- ✅ Validates the package before publishing
- ✅ Keeps versions in sync across pyproject.toml and server.json

## Prerequisites

### 1. PyPI API Token

You need to create a PyPI API token and add it to your GitHub repository:

1. Go to [PyPI Account Settings](https://pypi.org/manage/account/)
2. Scroll to "API tokens" and click "Add API token"
3. Give it a name like "GitHub Actions - mcp-server-vector-memory"
4. Set scope to "Entire account" or specific to this project
5. Copy the token (starts with `pypi-...`)

### 2. Add Token to GitHub

1. Go to your repository: https://github.com/NeerajG03/vector-memory
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: `PYPI_API_TOKEN`
5. Value: Paste your PyPI token
6. Click "Add secret"

## Publishing a New Version

### Automated Publishing (Recommended)

Simply create and push a version tag:

```bash
# Create a version tag (e.g., v0.1.0, v0.2.0, etc.)
git tag v0.1.0

# Push the tag to GitHub
git push origin v0.1.0
```

This triggers the GitHub Actions workflow which:
1. Extracts the version from the tag (e.g., `v0.1.0` → `0.1.0`)
2. Updates `pyproject.toml` and `server.json` with the new version
3. Builds the Python package
4. Publishes to PyPI
5. Publishes to MCP Registry using GitHub OIDC

### Manual Publishing (Advanced)

If you need to publish manually:

```bash
# 1. Update version in pyproject.toml and server.json

# 2. Build the package
uv build

# 3. Publish to PyPI
uv publish

# 4. Install MCP Publisher
brew install mcp-publisher  # or download from releases

# 5. Login to MCP Registry
mcp-publisher login github-oidc

# 6. Publish to MCP Registry
mcp-publisher publish
```

## Validation

Before publishing, validate your `server.json`:

```bash
python3 validate_server_json.py
```

This checks:
- ✅ Valid JSON syntax
- ✅ Required fields present
- ✅ Correct namespace format
- ✅ Package configuration
- ✅ README contains mcp-name comment

## Version Management

The workflow automatically syncs versions across:
- `pyproject.toml` → Python package version
- `server.json` → MCP registry version
- `server.json` packages → Package version

You only need to set the version in the git tag!

## Troubleshooting

### "Package validation failed"
- Ensure package is published to PyPI first
- Check that README contains `<!-- mcp-name: io.github.neerajg03/vector-memory -->`

### "Authentication failed"
- For automated: Ensure `id-token: write` permission is set in workflow
- For manual: Use `mcp-publisher login github-oidc`

### "Version mismatch"
- The workflow automatically syncs versions
- If publishing manually, ensure all three version fields match

## What Gets Published

When you publish:

1. **PyPI Package**: `mcp-server-vector-memory`
   - Users can install with: `pip install mcp-server-vector-memory`
   - Or with uv: `uv add mcp-server-vector-memory`

2. **MCP Registry**: `io.github.neerajg03/vector-memory`
   - Discoverable in MCP-compatible clients
   - Auto-configuration support
   - Validated ownership via PyPI package

## First-Time Publishing Checklist

- [ ] Create PyPI account
- [ ] Generate PyPI API token
- [ ] Add `PYPI_API_TOKEN` secret to GitHub
- [ ] Verify README has mcp-name comment
- [ ] Run validation script
- [ ] Create and push first version tag
- [ ] Monitor GitHub Actions workflow
- [ ] Verify package on PyPI
- [ ] Verify server on MCP Registry

## Resources

- [MCP Publishing Guide](https://github.com/modelcontextprotocol/registry/blob/main/docs/guides/publishing/publish-server.md)
- [GitHub Actions Guide](https://github.com/modelcontextprotocol/registry/blob/main/docs/guides/publishing/github-actions.md)
- [PyPI Help](https://pypi.org/help/)
