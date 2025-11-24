# Video Client for Raspberry Pi

A Raspberry Pi video streaming client with OLED display control via rotary encoder. Connects to a MediaMTX server and displays WebRTC streams in fullscreen Chromium kiosk mode.

## Features

- 🎮 **Rotary Encoder Control**: Navigate menus and select streams using a rotary encoder with button
- 📺 **OLED Display**: 128x64 I2C OLED display (SSD1306) for menu navigation
- 🌐 **WebRTC Streaming**: Full-screen kiosk mode streaming via Chromium
- ⚙️ **Easy Configuration**: Edit server IP directly from the OLED interface
- 🚀 **Auto-start on Boot**: Systemd service ensures the client starts automatically
- 📡 **MediaMTX Integration**: Fetches available streams from MediaMTX server API

## Hardware Requirements

- Raspberry Pi (tested on Pi 3/4)
- SSD1306 OLED Display (128x64, I2C)
- Rotary Encoder with push button
- Display (HDMI monitor/TV)

### Wiring

| Component | Pin | GPIO |
|-----------|-----|------|
| Rotary Encoder CLK | GPIO 17 | Pin 11 |
| Rotary Encoder DT | GPIO 27 | Pin 13 |
| Rotary Encoder SW | GPIO 22 | Pin 15 |
| OLED SDA | SDA.1 | Pin 3 |
| OLED SCL | SCL.1 | Pin 5 |
| OLED VCC | 3.3V | Pin 1 |
| OLED GND | GND | Pin 6 |

## Quick Installation

Run this single command on your Raspberry Pi:

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/video-client/main/install.sh | bash
```

**⚠️ Important**: Before running the installer, make sure to:
1. Edit `install.sh` and replace `YOUR_USERNAME` with your GitHub username
2. Push the code to GitHub
3. Make sure the repository is public (or use authentication for private repos)

### What the installer does:

1. Creates `/opt/video-client` directory
2. Downloads `setup.sh` and `client.py` from GitHub
3. Installs all dependencies (Python3, Chromium, X11, etc.)
4. Creates a systemd service for auto-start
5. Reboots the system

## Manual Installation

If you prefer to install manually:

```bash
# SSH to your Raspberry Pi
ssh pi@raspberrypi.local

# Create installation directory
sudo mkdir -p /opt/video-client
sudo chown pi:pi /opt/video-client

# Clone the repository (or download files manually)
cd /opt/video-client
# Download setup.sh and client.py here

# Make scripts executable
chmod +x setup.sh client.py

# Run the setup script
sudo ./setup.sh
```

The system will reboot after installation completes.

## Configuration

### Server IP Configuration

The client stores its configuration in `/opt/video-client/config.json`:

```json
{
    "server_ip": "010.000.000.074"
}
```

The IP address is stored in padded format (3 digits per octet) for easier editing via the rotary encoder interface.

You can change the server IP:
1. **Via OLED Menu**: Main Menu → Settings → Set Server IP
2. **Via File**: Edit `/opt/video-client/config.json` directly

### Default Configuration

- **API Port**: 9997 (MediaMTX API)
- **WebRTC Port**: 8889 (MediaMTX WebRTC)
- **OLED I2C Address**: 0x3C
- **Display**: :0 (default X display)

## Usage

### Navigation

- **Rotate Encoder**: Navigate through menus and options
- **Short Press**: Select/Confirm
- **Long Press (>1s)**: Back/Cancel (in stream selection)

### Main Menu

1. **Select Stream**: Browse and play available streams from MediaMTX server
2. **Settings**: Configure server IP and other options

### Stream Selection

- The client automatically refreshes the stream list every 5 seconds
- Rotate to select a stream
- Short press to play
- Long press (>1s) to return to main menu

### Settings Menu

- **Set Server IP**: Edit the MediaMTX server IP address digit by digit
- **Back**: Return to main menu

## Service Management

The client runs as a systemd service:

```bash
# Check status
sudo systemctl status video-client

# View logs
sudo journalctl -u video-client -f

# Restart service
sudo systemctl restart video-client

# Stop service
sudo systemctl stop video-client

# Disable auto-start
sudo systemctl disable video-client
```

## Troubleshooting

### OLED Display Not Working

```bash
# Check I2C devices
sudo i2cdetect -y 1
# Should show 0x3C (or 0x3D depending on your display)

# Enable I2C if not enabled
sudo raspi-config
# Interface Options → I2C → Enable
```

### Chromium Not Starting

```bash
# Check if X server is running
echo $DISPLAY
# Should output :0

# Test Chromium manually
DISPLAY=:0 chromium --version
```

### Stream Not Connecting

- Verify the MediaMTX server is running and accessible
- Check the server IP in config.json
- Ensure ports 9997 (API) and 8889 (WebRTC) are open
- Test the API endpoint: `curl http://SERVER_IP:9997/v3/paths/list`

### No Video/Audio

- Check Chromium flags in `client.py` (autoplay policy, audio, etc.)
- Verify HDMI output is active: `tvservice -s`
- Test audio: `speaker-test -t wav -c 2`

## Development

### File Structure

```
/opt/video-client/
├── client.py           # Main Python application
├── config.json         # Configuration file (created by setup)
└── setup.sh           # Installation script
```

### Modifying the Code

```bash
# Edit the client
sudo nano /opt/video-client/client.py

# Restart to apply changes
sudo systemctl restart video-client
```

## MediaMTX Server Setup

This client requires a MediaMTX server. Basic server configuration:

```yaml
# mediamtx.yml
api: yes
apiAddress: :9997

webrtcAddress: :8889
```

For more information, visit: https://github.com/bluenviron/mediamtx

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Credits

- Built with [luma.oled](https://github.com/rm-hull/luma.oled) for OLED display
- Uses [gpiozero](https://gpiozero.readthedocs.io/) for GPIO control
- Streams via [MediaMTX](https://github.com/bluenviron/mediamtx)

