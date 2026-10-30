#!/usr/bin/env bash
# ==============================================================================
# JARVIS Background Service Uninstaller
# ==============================================================================

set -e

SERVICE_NAME="jarvis"

echo "============================================================"
echo " 🛑 Stopping and Removing JARVIS Background Service"
echo "============================================================"

if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
    echo "Stopping ${SERVICE_NAME} service..."
    sudo systemctl stop ${SERVICE_NAME}
fi

if sudo systemctl is-enabled --quiet ${SERVICE_NAME} 2>/dev/null; then
    echo "Disabling ${SERVICE_NAME} auto-start on boot..."
    sudo systemctl disable ${SERVICE_NAME}
fi

if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
    echo "Removing /etc/systemd/system/${SERVICE_NAME}.service..."
    sudo rm "/etc/systemd/system/${SERVICE_NAME}.service"
    sudo systemctl daemon-reload
    sudo systemctl reset-failed
fi

echo ""
echo "✅ JARVIS background service has been completely stopped and removed!"

