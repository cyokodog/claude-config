#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Deliberately bypass nodenv shims and per-project .node-version files.
NODE_DIR="$HOME/.nodenv/versions/22.19.0/bin"
NODE="$NODE_DIR/node"
CLI="$SCRIPT_DIR/node_modules/@playwright/mcp/cli.js"

if [[ ! -x "$NODE" ]]; then
  echo "Playwright MCP: fixed Node runtime is missing. See tools/playwright-mcp/README.md." >&2
  exit 1
fi
if [[ ! -f "$CLI" ]]; then
  echo "Playwright MCP: local dependencies are missing. Run the documented npm ci command." >&2
  exit 1
fi

# Browser helpers that spawn node also use the fixed runtime.
export PATH="$NODE_DIR:$PATH"
exec "$NODE" "$CLI" "$@"
