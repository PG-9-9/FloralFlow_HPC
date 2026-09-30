#!/usr/bin/env bash
# ==========================================================
#  🌸 FloralFlow HPC - Streamlined Online Launcher
# ==========================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$DIR/bin"
BIN="$BIN_DIR/cloudflared"
URL_FILE="$DIR/online_url.txt"
LOG_DIR="$DIR"
SERVER_LOG="$LOG_DIR/server.log"
TUNNEL_LOG="$LOG_DIR/tunnel.log"

PORT=8089
USER_NAME="${USER:-$(whoami)}"
PASSWORD=""
RESET_PASS=false

show_help() {
    echo "Usage: ./start_online.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --password <PASS>   Set/update cluster password for your account"
    echo "  -u, --user <USER>       Specify Slurm user to monitor (default: $USER_NAME)"
    echo "  --port <PORT>           Local server port (default: 8089)"
    echo "  --reset-password        Interactively reset your cluster password"
    echo "  --stop                  Stop all running FloralFlow servers and tunnels"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./start_online.sh                           # Start FloralFlow"
    echo "  ./start_online.sh -p mySecretPass123        # Start and set password"
    echo "  ./start_online.sh --reset-password          # Change password interactively"
    echo "  ./start_online.sh --stop                    # Stop running instances"
}

# Parse Arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--password|--set-password)
            PASSWORD="$2"
            shift 2
            ;;
        -u|--user)
            USER_NAME="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --reset-password)
            RESET_PASS=true
            shift
            ;;
        --stop)
            echo "🛑 Stopping running FloralFlow instances..."
            pkill -f "$DIR/server.py" 2>/dev/null || true
            pkill -f "$BIN tunnel" 2>/dev/null || true
            if command -v fuser >/dev/null 2>&1; then
                fuser -k "${PORT}/tcp" 2>/dev/null || true
            fi
            echo "✅ All FloralFlow services stopped."
            exit 0
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "❌ Unknown argument: $1"
            show_help
            exit 1
            ;;
    esac
done

# Step 1: Ensure cloudflared binary is available
if [ ! -f "$BIN" ]; then
    echo "📥 Downloading standalone cloudflared binary (no root required)..."
    mkdir -p "$BIN_DIR"
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o "$BIN"
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o "$BIN"
    else
        echo "❌ Unsupported architecture: $ARCH. Please place cloudflared binary in $BIN"
        exit 1
    fi
    chmod +x "$BIN"
    echo "✅ cloudflared installed to $BIN"
fi

# Step 2: Handle password configuration
if [ "$RESET_PASS" = true ]; then
    python3 "$DIR/server.py" -u "$USER_NAME" --reset-password --only-set-password
elif [ -n "$PASSWORD" ]; then
    python3 "$DIR/server.py" -u "$USER_NAME" --password "$PASSWORD" --only-set-password
fi

# Step 3: Stop any existing instance on the same port
if command -v fuser >/dev/null 2>&1; then
    fuser -k "${PORT}/tcp" >/dev/null 2>&1 || true
else
    pkill -f "$DIR/server.py" >/dev/null 2>&1 || true
fi
sleep 0.5

# Step 4: Start local Python backend
echo "🚀 Starting FloralFlow Backend on port $PORT (User: $USER_NAME)..."
nohup python3 "$DIR/server.py" -p "$PORT" -u "$USER_NAME" > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!
sleep 1

# Check if server started successfully
if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "❌ Failed to start FloralFlow backend. Check $SERVER_LOG for details:"
    cat "$SERVER_LOG"
    exit 1
fi

# Step 5: Start Cloudflare Tunnel
echo "🌐 Establishing secure HTTPS Cloudflare Tunnel..."
rm -f "$URL_FILE" "$TUNNEL_LOG"
"$BIN" tunnel --no-autoupdate --url "http://127.0.0.1:$PORT" > "$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!

cleanup() {
    echo ""
    echo "🛑 Shutting down FloralFlow..."
    kill "$TUNNEL_PID" 2>/dev/null || true
    kill "$SERVER_PID" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Step 6: Wait for public URL
URL=""
for i in {1..25}; do
    URL=$(grep -o 'https://[a-zA-Z0-9.-]*\.trycloudflare\.com' "$TUNNEL_LOG" | head -n 1 || true)
    if [ -n "$URL" ]; then
        echo "$URL" > "$URL_FILE"
        break
    fi
    sleep 1
done

if [ -n "$URL" ]; then
    echo ""
    echo "=========================================================="
    echo " 🌸 FloralFlow HPC is LIVE Online!"
    echo "=========================================================="
    echo " 👤 Slurm User : $USER_NAME"
    echo " 🌐 Public URL : $URL"
    echo " 💡 Change pass: ./start_online.sh -p <new_password>"
    echo " 🛑 To Stop    : ./start_online.sh --stop"
    echo "=========================================================="
    echo ""
else
    echo "⚠️ Tunnel URL not detected immediately. Checking $TUNNEL_LOG:"
    tail -n 10 "$TUNNEL_LOG"
fi

wait "$TUNNEL_PID"
