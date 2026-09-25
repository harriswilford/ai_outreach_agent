#!/bin/bash
set -e

echo "=========================================================="
echo " 🚀 Starting AI Passive Outreach & Inbox Sentinel Agent"
echo "=========================================================="

# Graceful shutdown handler
cleanup() {
    echo ""
    echo "[!] Caught shutdown signal, gracefully stopping processes..."
    if [ -n "$DAEMON_PID" ]; then
        kill -TERM "$DAEMON_PID" 2>/dev/null || true
    fi
    exit 0
}
trap cleanup SIGTERM SIGINT

# Ensure state files exist so volume bind mounts don't mount as directories
touch daemon.log alerts.log daemon_state.json sentinel_state.json campaign_state.json

# Launch background outreach & inbox sentinel daemon
echo "[+] Starting 24/7 Background Daemon (Outreach + Inbox Sentinel)..."
python background_daemon.py &
DAEMON_PID=$!
echo "[+] Background Daemon active with PID: $DAEMON_PID"

# Launch FastAPI Web Dashboard & Analytics server
PORT="${PORT:-8000}"
echo "[+] Starting Web Dashboard on http://0.0.0.0:${PORT}..."
exec python -m uvicorn app:api_app --host 0.0.0.0 --port "$PORT"
