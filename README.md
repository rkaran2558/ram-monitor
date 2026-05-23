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
- A config file at `~/.local/share/ram-monitor/config.env`
- An autostart entry at `~/.config/autostart/ram-monitor.desktop`
- A runtime log at `/tmp/ram-monitor.log`

Do not run the installer with `sudo`. Tray icons and notifications need the normal desktop user session.

## Uninstall

```bash
bash ~/.local/share/ram-monitor/uninstall.sh
```

If you are working from a cloned copy of this repository, you can also run:

```bash
bash uninstall.sh
```

## Configure

During installation, you can press Enter to use the default values or enter values according to your system and preference.

| Parameter | Default | Meaning |
| --- | ---: | --- |
| `WARNING_THRESHOLD` | `90` | Show a warning alert when RAM usage reaches this percent. |
| `CRITICAL_THRESHOLD` | `95` | Show a critical alert when RAM usage reaches this percent. This must be higher than `WARNING_THRESHOLD`. |
| `CHECK_INTERVAL` | `5` | How often the app checks RAM usage, in seconds. |
| `WARNING_REPEAT_MINUTES` | `5` | How often warning alerts repeat while RAM stays above the warning threshold, in minutes. |
| `CRITICAL_REPEAT_SECONDS` | `30` | How often critical alerts repeat while RAM stays above the critical threshold, in seconds. |

After install, edit:

```bash
nano ~/.local/share/ram-monitor/config.env
```

Then restart:

```bash
pkill -f "/home/$USER/.local/share/ram-monitor/ram_monitor.py"
nohup ~/.local/share/ram-monitor/venv/bin/python3 ~/.local/share/ram-monitor/ram_monitor.py >/tmp/ram-monitor.log 2>&1 &
```

## Development

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python3 ram_monitor.py
```

The default settings are configured in `ram_monitor.py` and can be overridden by `config.env`:

- Warning: 90%
- Critical: 95%
- Check interval: 5 seconds
- Warning repeat delay: 5 minutes
- Critical repeat delay: 30 seconds
