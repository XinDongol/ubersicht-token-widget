#!/usr/bin/env bash
set -euo pipefail

SERVICE="${CLAUDE_SAFE_STORAGE_SERVICE:-Claude Safe Storage}"
KEYCHAIN="${CLAUDE_KEYCHAIN:-$HOME/Library/Keychains/login.keychain-db}"

if [ ! -f "$KEYCHAIN" ]; then
  echo "Keychain not found: $KEYCHAIN" >&2
  exit 1
fi

ACCOUNT="${CLAUDE_SAFE_STORAGE_ACCOUNT:-}"
if [ -z "$ACCOUNT" ]; then
  ACCOUNT="$(
    security find-generic-password -s "$SERVICE" "$KEYCHAIN" 2>/dev/null \
      | sed -n 's/.*"acct"<blob>="\(.*\)".*/\1/p' \
      | head -n 1
  )"
fi

if [ -z "$ACCOUNT" ]; then
  echo "Could not find the '$SERVICE' keychain item." >&2
  echo "Open Claude Desktop and sign in, then run this script again." >&2
  exit 1
fi

echo "Granting persistent access for '$SERVICE' (account: '$ACCOUNT')."
echo "macOS may ask for your login/keychain password. Input is hidden."

security set-generic-password-partition-list \
  -a "$ACCOUNT" \
  -s "$SERVICE" \
  -S "apple-tool:,apple:" \
  "$KEYCHAIN"

echo "Verifying access..."
security find-generic-password -w -s "$SERVICE" "$KEYCHAIN" >/dev/null

rm -f "$HOME/.cache/ai-limits/claude_plan_usage.json"

echo "Claude keychain access is ready."
echo "Restart or refresh Übersicht to reload the widget."
