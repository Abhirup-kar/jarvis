#!/usr/bin/env bash
# ==============================================================================
# JARVIS Edge Node Daemon 24/7 Service Installer (For Connected Remote PCs)
# ==============================================================================

set -e

HUB_URL="${1:-ws://127.0.0.1:8000/ws/node}"
NODE_ID="${2:-$(hostname)}"
TOKEN="${3:-jarvis_secret_token}"

NODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="jarvis-node"
USER_NAME="$(whoami)"
PYTHON_EXEC="$NODE_DIR/venv/bin/python"

if [ ! -f "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="$(which python3)"
fi

echo "============================================================"
echo " 🛰️ Installing JARVIS Edge Node 24/7 Background Service"
echo "============================================================"
echo " • Central Hub URL:   $HUB_URL"
echo " • Node ID:           $NODE_ID"
echo " • Python Executable: $PYTHON_EXEC"
echo "============================================================"

SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

sudo bash -c "cat <<EOF > $SERVICE_FILE
[Unit]
Description=JARVIS Remote Edge Node Daemon
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$NODE_DIR
ExecStart=$PYTHON_EXEC $NODE_DIR/nodes/agent_daemon.py --hub $HUB_URL --node-id $NODE_ID --token $TOKEN
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF"

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl restart ${SERVICE_NAME}

echo ""
echo "✅ JARVIS Edge Node Daemon installed and connected!"
echo " • Status:  sudo systemctl status ${SERVICE_NAME}"
echo " • Logs:    journalctl -u ${SERVICE_NAME} -f"

