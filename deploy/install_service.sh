#!/usr/bin/env bash
# ==============================================================================
# JARVIS Core 24/7 Systemd Background Service Installer
# ==============================================================================

set -e

JARVIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="jarvis"
USER_NAME="$(whoami)"
PYTHON_EXEC="$JARVIS_DIR/venv/bin/python"

if [ ! -f "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="$(which python3)"
fi

echo "============================================================"
echo " 🤖 Installing JARVIS Core 24/7 System Service"
echo "============================================================"
echo " • Working Directory: $JARVIS_DIR"
echo " • Python Path:       $PYTHON_EXEC"
echo " • System User:       $USER_NAME"
echo "============================================================"

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

sudo bash -c "cat <<EOF > $SERVICE_FILE
[Unit]
Description=JARVIS Autonomous Spatial Intelligence Platform
After=network.target sound.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$JARVIS_DIR
ExecStart=$PYTHON_EXEC $JARVIS_DIR/main.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=PULSE_SERVER=unix:/run/user/1000/pulse/native

[Install]
WantedBy=multi-user.target
EOF"

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl restart ${SERVICE_NAME}

echo ""
echo "✅ JARVIS Core service successfully installed and started!"
echo " • Status:  sudo systemctl status ${SERVICE_NAME}"
echo " • Logs:    journalctl -u ${SERVICE_NAME} -f"
echo " • Restart: sudo systemctl restart ${SERVICE_NAME}"
echo " • Stop:    sudo systemctl stop ${SERVICE_NAME}"

