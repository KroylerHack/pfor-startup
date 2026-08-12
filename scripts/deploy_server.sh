#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
REMOTE_NAME="${REMOTE_NAME:-origin}"
SERVICE_NAME="${SERVICE_NAME:-pfor}"
BRANCH="${BRANCH:-main}"

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "[deploy] Error: repository not found at $REPO_DIR" >&2
  exit 1
fi

cd "$REPO_DIR"

if git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  echo "[deploy] Fetching latest changes from $REMOTE_NAME/$BRANCH"
  git fetch "$REMOTE_NAME" --prune

  if git rev-parse --verify "$REMOTE_NAME/$BRANCH" >/dev/null 2>&1; then
    git checkout "$BRANCH"
    git reset --hard "$REMOTE_NAME/$BRANCH"
  else
    git checkout -B "$BRANCH" "$REMOTE_NAME/HEAD"
    git reset --hard "$REMOTE_NAME/HEAD"
  fi
else
  echo "[deploy] Warning: remote '$REMOTE_NAME' not found; using local repo state only."
fi

if [ -f "$REPO_DIR/requirements.txt" ]; then
  if [ -d "$REPO_DIR/venv" ]; then
    echo "[deploy] Installing Python dependencies"
    "$REPO_DIR/venv/bin/python" -m pip install --upgrade pip
    "$REPO_DIR/venv/bin/python" -m pip install -r "$REPO_DIR/requirements.txt"
  else
    echo "[deploy] No venv found at $REPO_DIR/venv; skipping dependency install."
  fi
fi

if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ] || systemctl list-unit-files 2>/dev/null | grep -q "^${SERVICE_NAME}\.service"; then
  echo "[deploy] Restarting systemd service: $SERVICE_NAME"
  systemctl daemon-reload
  systemctl restart "$SERVICE_NAME"
  systemctl status "$SERVICE_NAME" --no-pager -l || true
else
  echo "[deploy] No systemd service named '$SERVICE_NAME' found; using direct uvicorn startup"
  if [ -f "$REPO_DIR/scripts/start_backend.sh" ]; then
    bash "$REPO_DIR/scripts/start_backend.sh" &
  fi
fi

echo "[deploy] Deployment finished successfully"
