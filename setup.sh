#!/bin/bash
set -e

echo "=============================="
echo " Installing Video Client"
echo "=============================="

# ------------------------------------------------------------
# Update system
# ------------------------------------------------------------
echo "[1/7] Updating system..."
sudo apt-get update -y
sudo apt-get upgrade -y


# ------------------------------------------------------------
# Install required packages
# ------------------------------------------------------------
echo "[2/7] Installing packages..."

sudo apt-get install -y \
    python3 python3-pip python3-venv python3-setuptools python3-wheel \
    python3-gpiozero \
    python3-requests \
    python3-pil \
    i2c-tools \
    chromium \
    xserver-xorg \
    xinit \
    unclutter \
    luma.oled

# Fix: ensure luma dependency exists
sudo pip3 install --break-system-packages luma.core luma.oled


# ------------------------------------------------------------
# Create install directory
# ------------------------------------------------------------
echo "[3/7] Setting up /opt/video-client/..."

sudo mkdir -p /opt/video-client
sudo chown -R pi:pi /opt/video-client


# ------------------------------------------------------------
# Write default config.json (padded IP)
# ------------------------------------------------------------
echo "[4/7] Creating default config..."

cat <<EOF | sudo tee /opt/video-client/config.json >/dev/null
{
    "server_ip": "010.000.000.074"
}
EOF

sudo chown pi:pi /opt/video-client/config.json


# ------------------------------------------------------------
# Create systemd autostart service
# ------------------------------------------------------------
echo "[5/7] Creating systemd service..."

sudo bash -c 'cat > /etc/systemd/system/video-client.service << "EOF"
[Unit]
Description=Video Client Autostart
After=graphical.target

[Service]
Type=simple
User=pi
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
WorkingDirectory=/opt/video-client
ExecStart=/usr/bin/python3 /opt/video-client/client.py
Restart=always
RestartSec=5

[Install]
WantedBy=graphical.target
EOF'

sudo systemctl daemon-reload
sudo systemctl enable video-client.service

# ------------------------------------------------------------
# Enable I2C
# ------------------------------------------------------------
echo "[6/7] Enabling I2C..."

# Enable I2C in config.txt (check both old and new locations)
if [ -f /boot/firmware/config.txt ]; then
    CONFIG_FILE=/boot/firmware/config.txt
elif [ -f /boot/config.txt ]; then
    CONFIG_FILE=/boot/config.txt
else
    echo "⚠️  Warning: Could not find config.txt"
    CONFIG_FILE=/boot/config.txt
fi

# Check if I2C is already enabled, if not add it
if ! grep -q "^dtparam=i2c_arm=on" "$CONFIG_FILE"; then
    echo "dtparam=i2c_arm=on" | sudo tee -a "$CONFIG_FILE" >/dev/null
    echo "✓ I2C enabled in $CONFIG_FILE"
else
    echo "✓ I2C already enabled in $CONFIG_FILE"
fi

# Add pi user to i2c group
sudo usermod -a -G i2c pi 2>/dev/null || echo "✓ User already in i2c group"

# Load i2c-dev module
if ! lsmod | grep -q i2c_dev; then
    sudo modprobe i2c-dev 2>/dev/null || true
fi

# Ensure i2c-dev loads on boot
if ! grep -q "^i2c-dev" /etc/modules; then
    echo "i2c-dev" | sudo tee -a /etc/modules >/dev/null
    echo "✓ i2c-dev module configured for boot"
else
    echo "✓ i2c-dev module already configured"
fi

echo "✓ I2C setup complete"

# ------------------------------------------------------------
# Fix: prevent Chromium from asking for keyring
# ------------------------------------------------------------
echo "[7/7] Disabling Chromium keyring popup..."

sudo rm -rf /home/pi/.local/share/keyrings
sudo mkdir -p /home/pi/.local/share/keyrings
sudo touch /home/pi/.local/share/keyrings/default
sudo chown -R pi:pi /home/pi/.local/share/keyrings

sudo reboot