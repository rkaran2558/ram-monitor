# RAM Monitor

A small Linux desktop tray app that watches RAM usage and alerts when memory gets high.

## Install

From this folder:

```bash
bash install.sh
```

For a hosted one-command install after this project is pushed to GitHub:

```bash
curl -fsSL https://raw.githubusercontent.com/rkaran2558/ram-monitor/main/install.sh | bash
```

The installer creates:

- App files in `~/.local/share/ram-monitor`
- A Python virtual environment in `~/.local/share/ram-monitor/venv`
- An autostart entry at `~/.config/autostart/ram-monitor.desktop`
- A runtime log at `/tmp/ram-monitor.log`

Do not run the installer with `sudo`. Tray icons and notifications need the normal desktop user session.

## Uninstall

```bash
bash uninstall.sh
```

## Development

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python3 ram_monitor.py
```

The default thresholds are configured in `ram_monitor.py`:

- Warning: 90%
- Critical: 95%
- Check interval: 5 seconds
- Alert repeat delay: 5 minutes
