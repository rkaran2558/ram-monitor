#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "setup.sh is kept for compatibility."
echo "Running the user-session installer instead..."
echo ""

exec "$SCRIPT_DIR/install.sh"
