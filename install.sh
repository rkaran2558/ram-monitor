#!/usr/bin/env bash
set -euo pipefail

APP_NAME="ram-monitor"
APP_TITLE="RAM Monitor"
INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/${APP_NAME}"
BIN_DIR="$INSTALL_DIR/venv/bin"
AUTOSTART_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/${APP_NAME}.desktop"
RAW_BASE_URL="${RAM_MONITOR_RAW_BASE_URL:-https://raw.githubusercontent.com/rkaran2558/ram-monitor/main}"

if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    SOURCE_DIR=""
fi

if [ "${EUID:-$(id -u)}" -eq 0 ]; then
    echo "Do not run this installer with sudo. Install it as your normal desktop user."
    exit 1
fi

command -v python3 >/dev/null 2>&1 || {
    echo "python3 is required. Install it with your distro package manager, then run this again."
    exit 1
}

if [ -z "$SOURCE_DIR" ] || [ ! -f "$SOURCE_DIR/ram_monitor.py" ] || [ ! -f "$SOURCE_DIR/requirements.txt" ]; then
    command -v curl >/dev/null 2>&1 || {
        echo "curl is required for hosted install. Install curl, then run this again."
        exit 1
    }

    SOURCE_DIR="$(mktemp -d)"
    trap 'rm -rf "$SOURCE_DIR"' EXIT
    curl -fsSL "$RAW_BASE_URL/ram_monitor.py" -o "$SOURCE_DIR/ram_monitor.py"
    curl -fsSL "$RAW_BASE_URL/requirements.txt" -o "$SOURCE_DIR/requirements.txt"
    curl -fsSL "$RAW_BASE_URL/uninstall.sh" -o "$SOURCE_DIR/uninstall.sh"
fi

echo ""
echo "Installing $APP_TITLE"
echo "Source : $SOURCE_DIR"
echo "Target : $INSTALL_DIR"
echo ""

mkdir -p "$INSTALL_DIR" "$AUTOSTART_DIR"
cp "$SOURCE_DIR/ram_monitor.py" "$INSTALL_DIR/ram_monitor.py"
cp "$SOURCE_DIR/requirements.txt" "$INSTALL_DIR/requirements.txt"
cp "$SOURCE_DIR/uninstall.sh" "$INSTALL_DIR/uninstall.sh"
chmod +x "$INSTALL_DIR/uninstall.sh"

python3 -m venv "$INSTALL_DIR/venv"
"$BIN_DIR/python3" -m pip install --upgrade pip
"$BIN_DIR/pip" install -r "$INSTALL_DIR/requirements.txt"

"$BIN_DIR/python3" - "$INSTALL_DIR/alert.wav" <<'PY'
import math
import struct
import sys
import wave

output = sys.argv[1]
with wave.open(output, "w") as f:
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(44100)
    for i in range(44100):
        value = int(32767 * math.sin(2 * math.pi * 880 * i / 44100))
        f.writeframes(struct.pack("<h", value))
PY

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_TITLE
Comment=Monitor RAM usage and show high-memory alerts
Exec=$BIN_DIR/python3 $INSTALL_DIR/ram_monitor.py
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

chmod +x "$DESKTOP_FILE"

if pgrep -f "$INSTALL_DIR/ram_monitor.py" >/dev/null 2>&1; then
    pkill -f "$INSTALL_DIR/ram_monitor.py" || true
fi

nohup "$BIN_DIR/python3" "$INSTALL_DIR/ram_monitor.py" >/tmp/${APP_NAME}.log 2>&1 &

echo ""
echo "$APP_TITLE installed and started."
echo "Autostart file: $DESKTOP_FILE"
echo "App files     : $INSTALL_DIR"
echo "Log file      : /tmp/${APP_NAME}.log"
echo "Uninstall     : bash $INSTALL_DIR/uninstall.sh"
