#!/usr/bin/env bash
# FloraFlow Online Tunnel Launcher
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$DIR/bin/cloudflared"
URL_FILE="$DIR/online_url.txt"
LOG_FILE="$DIR/tunnel.log"

# Check if cloudflared exists
if [ ! -f "$BIN" ]; then
    echo "cloudflared binary not found in $BIN"
    exit 1
fi

# Ensure server is running
if ! lsof -i :8089 >/dev/null 2>&1 && ! fuser 8089/tcp >/dev/null 2>&1; then
    echo "Starting FloraFlow local server..."
    nohup python3 "$DIR/server.py" > "$DIR/server.log" 2>&1 &
    sleep 1
fi

echo "Launching Cloudflare Tunnel..."
rm -f "$URL_FILE"
"$BIN" tunnel --no-autoupdate --url http://127.0.0.1:8089 > "$LOG_FILE" 2>&1 &
TUNNEL_PID=$!

echo "Waiting for public HTTPS URL..."
for i in {1..20}; do
    URL=$(grep -o 'https://[a-zA-Z0-9.-]*\.trycloudflare\.com' "$LOG_FILE" | head -n 1 || true)
    if [ -n "$URL" ]; then
        echo "$URL" > "$URL_FILE"
        echo ""
        echo "=========================================================="
        echo " 🌿 FloraFlow is LIVE Online!"
        echo " URL: $URL"
        echo "=========================================================="
        echo ""
        break
    fi
    sleep 1
done

wait "$TUNNEL_PID"
