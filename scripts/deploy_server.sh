#!/usr/bin/env bash
set -euo pipefail

REMOTE_NAME="${REMOTE_NAME:-origin}"
SERVICE_NAME="${SERVICE_NAME:-pfor}"
BRANCH="${BRANCH:-main}"

find_repo_dir() {
  local candidates=()

  if [ -n "${REPO_DIR:-}" ]; then
    candidates+=("$REPO_DIR")
  fi

  local script_dir
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  candidates+=("$script_dir/..")
  candidates+=("$HOME/pfor")
  candidates+=("$HOME/pfor-startup")
  candidates+=("/home/pfor")
  candidates+=("/home/pfor-startup")
  candidates+=("/opt/pfor")
  candidates+=("/srv/pfor")

  for dir in "${candidates[@]}"; do
    if [ -d "$dir/.git" ] || [ -f "$dir/requirements.txt" ]; then
      if [ -f "$dir/requirements.txt" ] && [ -f "$dir/scripts/deploy_server.sh" ]; then
        printf '%s\n' "$dir"
        return 0
      fi
    fi
  done

  return 1
}

if ! REPO_DIR="$(find_repo_dir)"; then
  echo "[deploy] Could not find a valid project directory. Set REPO_DIR=/path/to/pfor-startup and retry." >&2
  exit 1
fi

cd "$REPO_DIR"

echo "[deploy] Using repository: $REPO_DIR"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
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
else
  echo "[deploy] Warning: $REPO_DIR is not a git repository; continuing with the files already present."
fi

if [ -f "$REPO_DIR/requirements.txt" ]; then
  if [ -d "$REPO_DIR/venv" ] && [ -x "$REPO_DIR/venv/bin/python" ]; then
    echo "[deploy] Installing Python dependencies into the repo venv"
    "$REPO_DIR/venv/bin/python" -m pip install --upgrade pip
    "$REPO_DIR/venv/bin/python" -m pip install -r "$REPO_DIR/requirements.txt"
  else
    echo "[deploy] No repo venv found at $REPO_DIR/venv; skipping dependency install."
  fi
fi

if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ] || systemctl list-unit-files 2>/dev/null | grep -q "^${SERVICE_NAME}\.service"; then
  echo "[deploy] Restarting systemd service: $SERVICE_NAME"
  systemctl daemon-reload
  systemctl restart "$SERVICE_NAME"
  systemctl status "$SERVICE_NAME" --no-pager -l || true
  echo "[deploy] Service restarted successfully"
else
  echo "[deploy] No systemd service named '$SERVICE_NAME' found; trying the repo startup script."
  if [ -f "$REPO_DIR/scripts/start_backend.sh" ]; then
    bash "$REPO_DIR/scripts/start_backend.sh" &
    echo "[deploy] Backend started via startup script"
  else
    echo "[deploy] No startup script found; nothing else to launch."
  fi
fi

echo "[deploy] Deployment finished successfully"
