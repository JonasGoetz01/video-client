#!/usr/bin/env python3
import time
import json
import os
import subprocess
import requests

from gpiozero import RotaryEncoder, Button
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# CONFIGURATION
# ============================================================

CONFIG_PATH = "/opt/video-client/config.json"

# Store padded IP internally, easier for digit editing.
DEFAULT_CONFIG = {
    "server_ip": "010.000.000.074"   # padded 3-3-3-3 digits
}

API_PORT = 9997
WEBRTC_PORT = 8889

OLED_I2C_PORT = 1
OLED_I2C_ADDRESS = 0x3C

ENC_CLK_PIN = 17
ENC_DT_PIN = 27
ENC_SW_PIN = 22

GUI_USER = "pi"
DISPLAY_ENV = ":0"
XAUTHORITY_ENV = f"/home/{GUI_USER}/.Xauthority"

CHROMIUM_CMD = "chromium"
CHROMIUM_ARGS = [
    "--no-sandbox",
    "--kiosk",
    "--autoplay-policy=no-user-gesture-required",
    "--start-fullscreen",
    "--noerrdialogs",
    "--disable-session-crashed-bubble",
    "--disable-infobars",
    "--disable-pinch",
    "--use-gl=egl",

    # 🔥 Prevent keyring popup
    "--password-store=basic",
    "--use-mock-keychain",
]

REFRESH_INTERVAL = 5  # seconds between stream list refresh


# ============================================================
# HELPERS
# ============================================================

def ip_trim(padded_ip: str) -> str:
    """
    Convert padded IP '010.000.001.004' -> '10.0.1.4'.
    Always use this for display and network operations.
    """
    parts = padded_ip.split(".")
    return ".".join(str(int(p)) for p in parts)


# ============================================================
# OLED SETUP
# ============================================================

serial = i2c(port=OLED_I2C_PORT, address=OLED_I2C_ADDRESS)
device = ssd1306(serial)

WIDTH = device.width
HEIGHT = device.height
font = ImageFont.load_default()


def draw(lines):
    """
    Draw up to 4 lines of text on the OLED.
    """
    img = Image.new("1", (WIDTH, HEIGHT))
    draw_obj = ImageDraw.Draw(img)
    y = 0
    for line in lines[:4]:
        draw_obj.text((0, y), line[:16], font=font, fill=255)
        y += 10
    device.display(img)


# ============================================================
# CONFIG LOAD/SAVE
# ============================================================

def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f)


# ============================================================
# MEDIA MTX NETWORK
# ============================================================

def fetch_paths(server_ip_trimmed: str):
    """
    Get list of available paths from MediaMTX using trimmed IP.
    """
    try:
        url = f"http://{server_ip_trimmed}:{API_PORT}/v3/paths/list"
        r = requests.get(url, timeout=2)
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            return ["<no streams>"]
        return [it.get("name", "unknown") for it in items]
    except Exception:
        return ["ERR"]


def build_webrtc_url(server_ip_trimmed: str, path: str) -> str:
    return f"http://{server_ip_trimmed}:{WEBRTC_PORT}/{path}"


# ============================================================
# CHROMIUM LAUNCH
# ============================================================

def play_stream(server_ip_trimmed: str, path: str):
    """
    Kill existing Chromium instance and launch WebRTC stream
    in fullscreen kiosk mode.
    """
    url = build_webrtc_url(server_ip_trimmed, path)

    # Kill old Chromium silently
    subprocess.run(
        ["pkill", "-f", CHROMIUM_CMD],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY_ENV
    env["XAUTHORITY"] = XAUTHORITY_ENV

    subprocess.Popen(
        [CHROMIUM_CMD] + CHROMIUM_ARGS + [url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env
    )


# ============================================================
# INPUT DEVICES
# ============================================================

encoder = RotaryEncoder(ENC_CLK_PIN, ENC_DT_PIN, max_steps=300, wrap=True)
button = Button(ENC_SW_PIN, pull_up=True, bounce_time=0.2)


def wait_for_release():
    while button.is_pressed:
        time.sleep(0.05)


# ============================================================
# MENUS
# ============================================================

# ---------- MAIN MENU ----------

def show_main_menu(cfg):
    items = ["Select Stream", "Settings"]
    idx = 0
    last_steps = encoder.steps

    while True:
        ip_disp = ip_trim(cfg["server_ip"])
        draw([
            f"> {items[idx]}",
            "",
            f"IP: {ip_disp}"
        ])

        steps = encoder.steps
        d = steps - last_steps
        if d != 0:
            idx = (idx + (1 if d > 0 else -1)) % len(items)
            last_steps = steps
            time.sleep(0.15)

        if button.is_pressed:
            wait_for_release()
            return items[idx]


# ---------- SETTINGS MENU ----------

def show_settings_menu(cfg):
    items = ["Set Server IP", "Back"]
    idx = 0
    last_steps = encoder.steps

    while True:
        ip_disp = ip_trim(cfg["server_ip"])
        draw([
            f"> {items[idx]}",
            "",
            f"IP: {ip_disp}"
        ])

        steps = encoder.steps
        d = steps - last_steps
        if d != 0:
            idx = (idx + (1 if d > 0 else -1)) % len(items)
            last_steps = steps
            time.sleep(0.15)

        if button.is_pressed:
            wait_for_release()
            return items[idx]


# ---------- CONFIRM YES / NO ----------

def confirm_yes_no():
    items = ["Yes", "No"]
    idx = 0
    last_steps = encoder.steps

    while True:
        draw([
            f"> {items[idx]}",
            f"  {items[1 - idx]}"
        ])

        steps = encoder.steps
        d = steps - last_steps
        if d != 0:
            idx = 1 - idx  # toggle
            last_steps = steps
            time.sleep(0.15)

        if button.is_pressed:
            wait_for_release()
            return (idx == 0)


# ---------- IPV4 EDITOR (HIGHLIGHT DIGIT) ----------

def edit_ip(cfg):
    """
    Edit server_ip as padded IPv4 using rotary encoder.
    - Rotate: change current digit 0–9
    - Press: move to next digit
    - Dots '.' are skipped automatically
    - At end, prompt to save changes
    """
    ip_chars = list(cfg["server_ip"])
    pos = 0
    last_steps = encoder.steps

    while True:
        # Skip dot positions
        if ip_chars[pos] == ".":
            pos += 1
            if pos >= len(ip_chars):
                pos = 0
            continue

        # Draw IP with highlighted current digit
        img = Image.new("1", (WIDTH, HEIGHT))
        d = ImageDraw.Draw(img)

        ip_str = "".join(ip_chars)
        x = 0
        y = 0

        # Fixed char cell width (8 px) for consistent cursor
        char_w = 8

        for i, ch in enumerate(ip_str):
            if i == pos:
                # Draw white rectangle then black digit: inverted highlight
                d.rectangle([x, y, x + char_w - 1, y + 9], fill=255)
                d.text((x, y), ch, font=font, fill=0)
            else:
                d.text((x, y), ch, font=font, fill=255)
            x += char_w

        d.text((0, 12), "Edit IP", font=font, fill=255)
        d.text((0, 22), "Press=Next", font=font, fill=255)

        device.display(img)

        # Rotary: change digit
        steps = encoder.steps
        delta = steps - last_steps
        if delta != 0:
            digit = int(ip_chars[pos])
            digit = (digit + (1 if delta > 0 else -1)) % 10
            ip_chars[pos] = str(digit)
            last_steps = steps
            time.sleep(0.15)

        # Press: next digit or finish
        if button.is_pressed:
            wait_for_release()
            pos += 1

            if pos >= len(ip_chars):
                new_padded_ip = "".join(ip_chars)
                new_trimmed = ip_trim(new_padded_ip)

                draw([
                    "Save changes?",
                    new_trimmed,
                    "> Yes",
                    "  No"
                ])
                time.sleep(0.3)

                if confirm_yes_no():
                    cfg["server_ip"] = new_padded_ip
                    save_config(cfg)
                return


# ---------- STREAM SELECTOR ----------

def select_stream(cfg):
    """
    Show list of streams and allow selection.
    - Rotate: move selection
    - Short press: play
    - Long press (>1s): back to main menu
    """
    server_ip_trimmed = ip_trim(cfg["server_ip"])
    paths = fetch_paths(server_ip_trimmed)
    idx = 0
    last_steps = encoder.steps
    last_refresh = time.time()

    while True:
        ip_disp = server_ip_trimmed
        current = paths[idx] if paths else "<no streams>"

        draw([
            f"> {current[:16]}",
            "",
            "Press=Play",
            "Hold>1s=Back"
        ])

        # Button handling: short vs long press
        if button.is_pressed:
            t0 = time.time()
            while button.is_pressed:
                time.sleep(0.05)
            hold = time.time() - t0

            if hold > 1.0:
                # Long press: back
                return

            # Short press: play if valid
            sel = paths[idx]
            if not sel.startswith("<") and sel != "ERR":
                draw(["Connecting...", sel[:16], ip_disp])
                play_stream(server_ip_trimmed, sel)
            time.sleep(0.4)

        # Rotary movement
        steps = encoder.steps
        d_steps = steps - last_steps
        if d_steps != 0 and paths:
            idx = (idx + (1 if d_steps > 0 else -1)) % len(paths)
            last_steps = steps
            time.sleep(0.1)

        # Periodic refresh of stream list
        if time.time() - last_refresh > REFRESH_INTERVAL:
            paths = fetch_paths(server_ip_trimmed)
            if idx >= len(paths):
                idx = 0 if paths else 0
            last_refresh = time.time()


# ============================================================
# MAIN LOOP
# ============================================================

def main():
    # Small delay to let GUI come up when auto-started
    time.sleep(2)

    cfg = load_config()

    while True:
        choice = show_main_menu(cfg)

        if choice == "Select Stream":
            select_stream(cfg)

        elif choice == "Settings":
            opt = show_settings_menu(cfg)
            if opt == "Set Server IP":
                edit_ip(cfg)
            elif opt == "Back":
                continue


if __name__ == "__main__":
    main()