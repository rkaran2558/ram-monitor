#!/usr/bin/env python3
"""
RAM Monitor - System Tray App
Monitors RAM usage and alerts at 90% (warning) and 95% (critical)
"""

import psutil
import threading
import time
import os
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as item
from plyer import notification
import pygame

# ─────────────────────────────────────────
#  CONFIGURATION — Change these as needed
# ─────────────────────────────────────────
WARNING_THRESHOLD  = 90   # % — Yellow warning
CRITICAL_THRESHOLD = 95   # % — Red critical alert
CHECK_INTERVAL     = 5    # seconds between RAM checks
SOUND_FILE         = os.path.join(os.path.dirname(__file__), "alert.wav")
SNOOZE_MINUTES     = 5    # How long to wait before re-alerting

# ─────────────────────────────────────────
#  GLOBAL STATE
# ─────────────────────────────────────────
last_alert_time = 0       # Timestamp of last alert (to avoid spam)
snooze_until    = 0       # Timestamp until which alerts are snoozed
icon_ref        = None    # Reference to tray icon (set later)


# ══════════════════════════════════════════
#  STEP A: READ RAM STATS
#  psutil.virtual_memory() returns:
#    .total   = total RAM in bytes
#    .used    = used RAM in bytes
#    .percent = used percentage (0–100)
# ══════════════════════════════════════════
def get_ram_stats():
    mem = psutil.virtual_memory()
    return {
        "percent": mem.percent,
        "used_gb": mem.used / (1024 ** 3),
        "total_gb": mem.total / (1024 ** 3),
        "available_gb": mem.available / (1024 ** 3),
    }


# ══════════════════════════════════════════
#  STEP B: GET TOP MEMORY-EATING PROCESSES
#  We sort all processes by memory usage
#  and return the top 5 culprits
# ══════════════════════════════════════════
def get_top_processes(n=5):
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'memory_percent']):
        try:
            procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    # Sort descending by memory_percent
    procs.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
    return procs[:n]


# ══════════════════════════════════════════
#  STEP C: PLAY ALERT SOUND
#  pygame.mixer handles audio playback
#  WARNING  → plays once
#  CRITICAL → plays 3 times
# ══════════════════════════════════════════
def play_sound(times=1):
    try:
        if not os.path.exists(SOUND_FILE):
            print(f"[Sound] alert.wav not found at {SOUND_FILE}, skipping sound.")
            return
        pygame.mixer.init()
        pygame.mixer.music.load(SOUND_FILE)
        for _ in range(times):
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            time.sleep(0.2)
    except Exception as e:
        print(f"[Sound Error] {e}")


# ══════════════════════════════════════════
#  STEP D: SEND DESKTOP NOTIFICATION
#  plyer.notification.notify() sends a
#  native Linux desktop notification popup
# ══════════════════════════════════════════
def send_notification(title, message, urgency="normal"):
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="RAM Monitor",
            timeout=10,  # seconds before auto-dismiss
        )
    except Exception as e:
        print(f"[Notification Error] {e}")


# ══════════════════════════════════════════
#  STEP E: SHOW TERMINAL ALERT (FALLBACK UI)
#  Prints a bold colored warning in terminal
#  Acts as the "UI alert" if no GUI popup
# ══════════════════════════════════════════
def print_alert(level, stats, top_procs):
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    RESET  = "\033[0m"
    BOLD   = "\033[1m"

    color = RED if level == "CRITICAL" else YELLOW
    border = "═" * 55

    print(f"\n{color}{BOLD}{border}")
    print(f"  ⚠️  RAM {level} ALERT — {stats['percent']:.1f}% USED")
    print(f"  Used: {stats['used_gb']:.1f} GB / {stats['total_gb']:.1f} GB")
    print(f"  Free: {stats['available_gb']:.1f} GB")
    print(f"─────────────────────────────────────────────────────")
    print(f"  Top memory consumers:")
    for i, p in enumerate(top_procs, 1):
        name = (p['name'] or 'unknown')[:30]
        pct  = p['memory_percent'] or 0
        print(f"  {i}. {name:<30} {pct:.1f}%")
    print(f"{border}{RESET}\n")


# ══════════════════════════════════════════
#  STEP F: DRAW TRAY ICON
#  We dynamically draw the tray icon with
#  the current RAM % as text + color coding:
#    Green  = below 70%
#    Yellow = 70–89%
#    Red    = 90%+
# ══════════════════════════════════════════
def create_tray_icon(percent):
    size = 64
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle color based on usage
    if percent >= CRITICAL_THRESHOLD:
        bg_color = (220, 50, 50, 230)    # Red
    elif percent >= WARNING_THRESHOLD:
        bg_color = (230, 160, 0, 230)    # Yellow/Orange
    elif percent >= 70:
        bg_color = (200, 200, 0, 230)    # Yellow
    else:
        bg_color = (50, 180, 80, 230)    # Green

    # Draw filled circle
    draw.ellipse([2, 2, size - 2, size - 2], fill=bg_color)

    # Draw RAM % text inside circle
    label = f"{int(percent)}%"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        ((size - text_w) / 2, (size - text_h) / 2),
        label,
        fill=(255, 255, 255),
        font=font
    )
    return img


# ══════════════════════════════════════════
#  STEP G: MAIN MONITORING LOOP
#  Runs in a background thread every N secs
#  Checks RAM → decides alert level → acts
# ══════════════════════════════════════════
def monitor_loop(icon):
    global last_alert_time, snooze_until

    while True:
        stats     = get_ram_stats()
        percent   = stats["percent"]
        now       = time.time()

        # Update tray icon with current %
        try:
            icon.icon = create_tray_icon(percent)
            icon.title = f"RAM: {percent:.1f}% used"
        except Exception:
            pass

        # Only alert if not snoozed and enough time has passed
        can_alert = (now > snooze_until) and (now - last_alert_time > SNOOZE_MINUTES * 60)

        if percent >= CRITICAL_THRESHOLD and can_alert:
            # ── CRITICAL ALERT ──
            top_procs = get_top_processes()
            top_names = ", ".join((p['name'] or 'unknown') for p in top_procs[:3])

            send_notification(
                title="🔴 CRITICAL: RAM Almost Full!",
                message=f"RAM at {percent:.1f}%! Free up memory now.\nTop: {top_names}"
            )
            print_alert("CRITICAL", stats, top_procs)
            threading.Thread(target=play_sound, args=(3,), daemon=True).start()
            last_alert_time = now

        elif percent >= WARNING_THRESHOLD and can_alert:
            # ── WARNING ALERT ──
            top_procs = get_top_processes()
            top_names = ", ".join((p['name'] or 'unknown') for p in top_procs[:3])

            send_notification(
                title="⚠️ WARNING: High RAM Usage",
                message=f"RAM at {percent:.1f}%. Consider closing apps.\nTop: {top_names}"
            )
            print_alert("WARNING", stats, top_procs)
            threading.Thread(target=play_sound, args=(1,), daemon=True).start()
            last_alert_time = now

        time.sleep(CHECK_INTERVAL)


# ══════════════════════════════════════════
#  STEP H: TRAY MENU ACTIONS
# ══════════════════════════════════════════
def show_status(icon, item):
    stats = get_ram_stats()
    top   = get_top_processes()
    print_alert("STATUS", stats, top)

def snooze_alerts(icon, item):
    global snooze_until
    snooze_until = time.time() + SNOOZE_MINUTES * 60
    print(f"[RAM Monitor] Alerts snoozed for {SNOOZE_MINUTES} minutes.")
    send_notification("RAM Monitor", f"Alerts snoozed for {SNOOZE_MINUTES} min.")

def quit_app(icon, item):
    print("[RAM Monitor] Exiting...")
    icon.stop()


# ══════════════════════════════════════════
#  STEP I: ENTRY POINT — BUILD TRAY APP
# ══════════════════════════════════════════
def main():
    global icon_ref
    print("=" * 50)
    print("  RAM Monitor Started")
    print(f"  Warning at:  {WARNING_THRESHOLD}%")
    print(f"  Critical at: {CRITICAL_THRESHOLD}%")
    print(f"  Checking every {CHECK_INTERVAL} seconds")
    print("=" * 50)

    # Create initial tray icon
    initial_stats = get_ram_stats()
    tray_image = create_tray_icon(initial_stats["percent"])

    # Build tray menu
    menu = pystray.Menu(
        item("📊 Show RAM Status",  show_status),
        item("😴 Snooze 5 min",     snooze_alerts),
        item("❌ Quit",             quit_app),
    )

    # Create tray icon object
    icon = pystray.Icon(
        name="ram_monitor",
        icon=tray_image,
        title=f"RAM: {initial_stats['percent']:.1f}%",
        menu=menu,
    )
    icon_ref = icon

    # Start monitoring in background thread
    monitor_thread = threading.Thread(
        target=monitor_loop,
        args=(icon,),
        daemon=True   # daemon=True means thread dies when main app exits
    )
    monitor_thread.start()

    # Run tray icon (this blocks the main thread — that's correct)
    icon.run()


if __name__ == "__main__":
    main()
