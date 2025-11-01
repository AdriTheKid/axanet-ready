#!/usr/bin/env bash
set -euo pipefail
APP_DIR="${APP_DIR:-/home/ec2-user/axanet}"
sudo yum update -y
sudo yum install -y python3 git
sudo mkdir -p "$APP_DIR"
sudo chown -R ec2-user:ec2-user "$APP_DIR"
cat <<'UNIT' | sudo tee /etc/systemd/system/axanet.service >/dev/null
[Unit]
Description=Axanet Client Manager (Flask/Gunicorn)
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/axanet
Environment=CLIENTS_DB=/home/ec2-user/axanet/data/clients.json
ExecStart=/bin/bash /home/ec2-user/axanet/scripts/start.sh
Restart=always

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable axanet.service
echo "Systemd unit installed."
