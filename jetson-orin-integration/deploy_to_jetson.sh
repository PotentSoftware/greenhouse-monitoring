#!/usr/bin/env bash
set -euo pipefail

# Deploy Jetson Orin Nano Greenhouse Monitoring (Streamlit multipage app)
# Usage:
#   ./deploy_to_jetson.sh <JETSON_HOST_OR_IP> [--stop] [--start] [--service SERVICE_NAME] [--remote-dir DIR]
# Examples:
#   ./deploy_to_jetson.sh 192.168.1.75            # sync + install only
#   ./deploy_to_jetson.sh 192.168.1.75 --stop     # stop running app/services before deploy
#   ./deploy_to_jetson.sh 192.168.1.75 --stop --start  # stop, deploy, then restart
#   ./deploy_to_jetson.sh 192.168.1.75 --service greenhouse-monitoring
#   ./deploy_to_jetson.sh 192.168.1.75 --remote-dir /home/lionel/jetson-greenhouse
#
# Notes:
# - Username is assumed to be 'lionel'
# - This script uses rsync over SSH. It will prompt for the password unless you have SSH keys set up.
# - Do NOT hardcode passwords in scripts. If you insist on non-interactive, install sshpass and adapt the RSYNC/SSH lines accordingly.

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <JETSON_HOST_OR_IP> [--stop] [--start] [--service SERVICE_NAME]"
  exit 1
fi

JETSON_HOST="$1"; shift || true
DO_STOP=false
DO_START=false
SERVICE_NAME="greenhouse-monitoring"
REMOTE_DIR_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stop)
      DO_STOP=true; shift ;;
    --start)
      DO_START=true; shift ;;
    --service)
      SERVICE_NAME="$2"; shift 2 ;;
    --remote-dir)
      REMOTE_DIR_OVERRIDE="$2"; shift 2 ;;
    *)
      echo "Unknown option: $1"; exit 1 ;;
  esac
done
JETSON_USER="lionel"
if [[ -n "${REMOTE_DIR_OVERRIDE}" ]]; then
  REMOTE_APP_DIR="${REMOTE_DIR_OVERRIDE}"
  REMOTE_BASE_DIR="$(dirname "${REMOTE_APP_DIR}")"
else
  REMOTE_BASE_DIR="/home/${JETSON_USER}/greenhouse-monitoring"
  REMOTE_APP_DIR="${REMOTE_BASE_DIR}/jetson-orin-integration"
fi

LOCAL_APP_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Creating remote directories on ${JETSON_USER}@${JETSON_HOST}"
ssh "${JETSON_USER}@${JETSON_HOST}" "mkdir -p '${REMOTE_APP_DIR}'"
echo "    Remote app path: ${REMOTE_APP_DIR}"

# Optionally stop running services/processes to avoid conflicts
if [[ "${DO_STOP}" == "true" ]]; then
  echo "==> Stopping running greenhouse processes/services on Jetson"
  read -r -d '' REMOTE_STOP <<EOS
set -euo pipefail
# Try stopping a systemd service if it exists
if systemctl list-unit-files | grep -q "^${SERVICE_NAME}\.service"; then
  echo "Stopping system service: ${SERVICE_NAME}.service"
  sudo systemctl stop ${SERVICE_NAME}.service || true
fi
# Stop user service if present
if systemctl --user list-unit-files | grep -q "^${SERVICE_NAME}\.service"; then
  echo "Stopping user service: ${SERVICE_NAME}.service"
  systemctl --user stop ${SERVICE_NAME}.service || true
fi
# Kill stray Streamlit/Python processes related to this app directory
pkill -f "streamlit .*streamlit_dashboard\.py" 2>/dev/null || true
pkill -f "${REMOTE_APP_DIR}" 2>/dev/null || true
sleep 1
EOS
  ssh "${JETSON_USER}@${JETSON_HOST}" "bash -lc '${REMOTE_STOP//'\n'/$'\n'}'"
fi

# Rsync the jetson-orin-integration app directory
# Exclude virtualenv, git, caches, large artifacts
echo "==> Syncing application files to Jetson (${JETSON_HOST})"
rsync -avz --delete \
  --exclude 'venv/' \
  --exclude '.git/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '*.log' \
  --exclude '.DS_Store' \
  "${LOCAL_APP_DIR}/" "${JETSON_USER}@${JETSON_HOST}:${REMOTE_APP_DIR}/"

# Prepare Python environment and install requirements
read -r -d '' REMOTE_SETUP <<EOS
set -euo pipefail
cd '${REMOTE_APP_DIR}'
echo "==> Ensuring uv is installed"
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv (user-local)"
  curl -fsSL https://astral.sh/uv/install.sh | sh
  # Ensure common install locations are on PATH for this session
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi
# Create venv if missing
if [[ ! -d venv ]]; then
  echo "==> Creating Python venv with uv"
  uv venv venv
fi
# Upgrade pip and install requirements
source venv/bin/activate
echo "==> Installing requirements with uv pip"
uv pip install --upgrade pip wheel setuptools
uv pip install -r requirements.txt
# Optional: print versions
python -c 'import sys,streamlit,numpy,pandas,sklearn;print("Python:",sys.version);print("Streamlit:",streamlit.__version__);print("NumPy:",__import__("numpy").__version__);print("Pandas:",__import__("pandas").__version__);print("sklearn:",__import__("sklearn").__version__)'
EOS

echo "==> Setting up environment and installing dependencies on Jetson"
ssh "${JETSON_USER}@${JETSON_HOST}" "bash -lc '${REMOTE_SETUP//'\n'/$'\n'}'"

# Optionally start services/processes after deployment
if [[ "${DO_START}" == "true" ]]; then
  echo "==> Starting greenhouse app/service on Jetson"
  read -r -d '' REMOTE_START <<EOS
set -euo pipefail
cd '${REMOTE_APP_DIR}'
source venv/bin/activate
# Prefer systemd service if available; else launch a screen session
if systemctl list-unit-files | grep -q "^${SERVICE_NAME}\.service"; then
  echo "Starting system service: ${SERVICE_NAME}.service"
  sudo systemctl start ${SERVICE_NAME}.service || true
elif systemctl --user list-unit-files | grep -q "^${SERVICE_NAME}\.service"; then
  echo "Starting user service: ${SERVICE_NAME}.service"
  systemctl --user start ${SERVICE_NAME}.service || true
else
  echo "Launching Streamlit in screen session 'greenhouse'"
  screen -S greenhouse -dm bash -lc "STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run streamlit_dashboard.py --server.port 8083 --server.address 0.0.0.0 --server.headless true"
fi
EOS
  ssh "${JETSON_USER}@${JETSON_HOST}" "bash -lc '${REMOTE_START//'\n'/$'\n'}'"
fi

cat <<EOM

Deployment complete.

To run the Streamlit server on the Jetson in the foreground:
  ssh ${JETSON_USER}@${JETSON_HOST}
  cd ${REMOTE_APP_DIR}
  source venv/bin/activate
  STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
  streamlit run streamlit_dashboard.py --server.port 8083 --server.address 0.0.0.0 --server.headless true

Or start it in a detached screen session:
  ssh ${JETSON_USER}@${JETSON_HOST}
  cd ${REMOTE_APP_DIR}
  source venv/bin/activate
  screen -S greenhouse -dm bash -lc "STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run streamlit_dashboard.py --server.port 8083 --server.address 0.0.0.0 --server.headless true"
  # To reattach later: screen -r greenhouse

To automatically stop and start services during deployment, use:
  ./deploy_to_jetson.sh <JETSON_IP> --stop --start [--service greenhouse-monitoring]

EOM
