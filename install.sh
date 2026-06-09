#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIDGET_ROOT="${UBERSICHT_WIDGETS_DIR:-$HOME/Library/Application Support/Übersicht/widgets}"
WIDGET_DIR="$WIDGET_ROOT/ai-limits.widget"

mkdir -p "$WIDGET_DIR"

rsync -a --delete \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude "__pycache__" \
  --exclude ".DS_Store" \
  "$SOURCE_DIR/" "$WIDGET_DIR/"

chmod +x "$WIDGET_DIR/ai_limits.py"

if command -v python3 >/dev/null 2>&1; then
  python3 -m venv "$WIDGET_DIR/.venv"
  "$WIDGET_DIR/.venv/bin/python" -m pip install --upgrade pip
  "$WIDGET_DIR/.venv/bin/python" -m pip install -r "$WIDGET_DIR/requirements.txt"
else
  echo "python3 was not found. Install Python 3, then run ./install.sh again." >&2
fi

if ! command -v ccusage >/dev/null 2>&1 && [ ! -x "$HOME/.bun/bin/ccusage" ]; then
  echo "ccusage was not found. Install it with: bun install -g ccusage" >&2
fi

if [ -d "/Applications/Übersicht.app" ]; then
  open -ga "Übersicht" || true
  osascript -e 'tell application "Übersicht" to refresh widget id "ai-limits-widget-index-coffee"' >/dev/null 2>&1 || true
fi

echo "Installed AI Limits widget to: $WIDGET_DIR"
echo "To test it manually, run:"
echo "  cd \"$WIDGET_DIR\""
echo "  ./.venv/bin/python ./ai_limits.py"
