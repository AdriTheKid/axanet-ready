#!/usr/bin/env bash
set -euo pipefail
HOST="${1:?host}"; KEY="${2:?pem}"; USER="${3:-ec2-user}"
chmod 400 "$KEY" || true
ssh -o StrictHostKeyChecking=accept-new -i "$KEY" "$USER@$HOST" "echo Connected to $(hostname)"
