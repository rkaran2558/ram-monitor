#!/usr/bin/env bash
set -euo pipefail

APP_NAME="ram-monitor"
INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/${APP_NAME}"
DESKTOP_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/autostart/${APP_NAME}.desktop"

if [ "${EUID:-$(id -u)}" -eq 0 ]; then
    echo "Do not run this uninstaller with sudo. Run it as your normal desktop user."
    exit 1
fi

if pgrep -f "$INSTALL_DIR/ram_monitor.py" >/dev/null 2>&1; then
    pkill -f "$INSTALL_DIR/ram_monitor.py" || true
fi

rm -f "$DESKTOP_FILE"
rm -rf "$INSTALL_DIR"

echo "RAM Monitor uninstalled."
