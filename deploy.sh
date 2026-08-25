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
# -o overwrites existing files without prompting
sudo unzip -o /tmp/teleagent_deploy.zip -d "${APP_DIR}"
sudo chown -R $USER:$USER "${APP_DIR}"

echo "🌐 Installing / Updating Python requirements..."
"${APP_DIR}/venv/bin/pip" install --upgrade pip
"${APP_DIR}/venv/bin/pip" install --upgrade -r "${APP_DIR}/requirements.txt"

# Clean up payload zip ONLY (do not delete deploy.sh while it's running)
rm -f /tmp/teleagent_deploy.zip

# Check login status non-interactively
cd "${APP_DIR}"
echo "🔐 Checking Telegram authentication status..."
./venv/bin/python login.py || true

# Start background service
echo "🚀 Starting TeleAgent background service..."
sudo systemctl restart teleagent.service

echo "=================================================="
echo "🎉 TeleAgent deployed successfully!"
echo "📜 Showing live logs (Press Ctrl+C to exit logs, bot stays running):"
echo "=================================================="
journalctl -u teleagent.service -f -n 30
