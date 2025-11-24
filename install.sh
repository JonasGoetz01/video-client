#!/bin/bash
set -e

# ============================================================
# Video Client - One-Line Installer
# ============================================================
# Usage:
#   curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/video-client/main/install.sh | bash
#
# This script will:
#   1. Create /opt/video-client directory
#   2. Download setup.sh and client.py from GitHub
#   3. Run setup.sh to install dependencies and configure autostart
# ============================================================

GITHUB_USER="jonasgoetz01"          # TODO: Replace with your GitHub username
GITHUB_REPO="video-client"           # TODO: Replace with your repo name
GITHUB_BRANCH="main"                 # or "master" depending on your default branch

INSTALL_DIR="/opt/video-client"
RAW_BASE="https://raw.githubusercontent.com/${GITHUB_USER}/${GITHUB_REPO}/${GITHUB_BRANCH}"

echo "=============================="
echo " Video Client Installer"
echo "=============================="
echo ""
echo "This will install the video client to ${INSTALL_DIR}"
echo ""

# ------------------------------------------------------------
# Check if running as root (not recommended)
# ------------------------------------------------------------
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Warning: Running as root. This script will use 'pi' as the user."
    TARGET_USER="pi"
else
    TARGET_USER="$USER"
fi

# ------------------------------------------------------------
# Create installation directory
# ------------------------------------------------------------
echo "[1/4] Creating installation directory..."

if [ -d "$INSTALL_DIR" ]; then
    echo "Directory $INSTALL_DIR already exists."
    read -p "Do you want to continue and overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
fi

sudo mkdir -p "$INSTALL_DIR"
sudo chown -R ${TARGET_USER}:${TARGET_USER} "$INSTALL_DIR"
echo "✓ Directory created and owned by ${TARGET_USER}"

# ------------------------------------------------------------
# Download files from GitHub
# ------------------------------------------------------------
echo "[2/4] Downloading files from GitHub..."

echo "  - Downloading setup.sh..."
if ! sudo curl -sSL -f "${RAW_BASE}/setup.sh" -o "${INSTALL_DIR}/setup.sh"; then
    echo "❌ Failed to download setup.sh"
    echo "   Please check:"
    echo "   - Your GitHub username: ${GITHUB_USER}"
    echo "   - Your repository name: ${GITHUB_REPO}"
    echo "   - Your branch name: ${GITHUB_BRANCH}"
    echo "   - That the repository is public"
    exit 1
fi

echo "  - Downloading client.py..."
if ! sudo curl -sSL -f "${RAW_BASE}/client.py" -o "${INSTALL_DIR}/client.py"; then
    echo "❌ Failed to download client.py"
    exit 1
fi

# Set ownership
sudo chown ${TARGET_USER}:${TARGET_USER} "${INSTALL_DIR}/setup.sh"
sudo chown ${TARGET_USER}:${TARGET_USER} "${INSTALL_DIR}/client.py"

# Make setup.sh executable
sudo chmod +x "${INSTALL_DIR}/setup.sh"
sudo chmod +x "${INSTALL_DIR}/client.py"

echo "✓ Files downloaded successfully"

# ------------------------------------------------------------
# Copy setup.sh to current directory for execution
# ------------------------------------------------------------
echo "[3/4] Preparing setup script..."
cd "$INSTALL_DIR"
echo "✓ Ready to run setup"

# ------------------------------------------------------------
# Run setup.sh
# ------------------------------------------------------------
echo "[4/4] Running setup script..."
echo ""
echo "The setup will now:"
echo "  - Update system packages"
echo "  - Install Python3 and dependencies"
echo "  - Install Chromium and X11"
echo "  - Create systemd service for autostart"
echo "  - Reboot the system"
echo ""

read -p "Continue with setup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled. Files are in ${INSTALL_DIR}"
    echo "You can run the setup manually later:"
    echo "  cd ${INSTALL_DIR} && sudo ./setup.sh"
    exit 0
fi

# Run the setup script
sudo bash "${INSTALL_DIR}/setup.sh"

