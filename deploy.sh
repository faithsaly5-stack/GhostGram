#!/bin/bash
set -e

echo "=================================================="
echo "🚀 Starting TeleAgent Deployment on VPS..."
echo "=================================================="

APP_DIR="/opt/teleagent"

# Stop any running service during update
sudo systemctl stop teleagent.service 2>/dev/null || true

# Extract files from /tmp to /opt/teleagent
echo "📝 Extracting files to ${APP_DIR}..."
# Clear old profiles directory to sync deletions perfectly
sudo rm -rf "${APP_DIR}"/profiles/
# -o overwrites existing files without prompting
sudo unzip -o /tmp/teleagent_deploy.zip -d "${APP_DIR}"
sudo chown -R $USER:$USER "${APP_DIR}"

if [ ! -d "${APP_DIR}/venv" ]; then
    echo "📦 Creating new Python virtual environment..."
    sudo apt-get update -y 2>/dev/null || true
    sudo apt-get install -y python3-venv 2>/dev/null || true
    python3 -m venv "${APP_DIR}/venv"
fi

echo "🌐 Installing / Updating Python requirements..."
"${APP_DIR}/venv/bin/pip" install --upgrade pip
"${APP_DIR}/venv/bin/pip" install --upgrade -r "${APP_DIR}/requirements.txt"

# Clean up payload zip ONLY (do not delete deploy.sh while it's running)
rm -f /tmp/teleagent_deploy.zip

cd "${APP_DIR}"

if [ ! -f /etc/systemd/system/teleagent.service ]; then
    echo "⚙️ Creating systemd service for the first time..."
    sudo tee /etc/systemd/system/teleagent.service > /dev/null <<EOF
[Unit]
Description=GhostGram Background Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable teleagent.service
fi

# Start background service
echo "🚀 Starting TeleAgent background service..."
sudo systemctl restart teleagent.service

echo "=================================================="
echo "🎉 TeleAgent deployed successfully!"
echo "📜 Showing live logs (Press Ctrl+C to exit logs, bot stays running):"
echo "=================================================="
journalctl -u teleagent.service -f -n 30
