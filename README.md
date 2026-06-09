# AI Limits Übersicht Widget

A compact macOS desktop widget for [Übersicht](https://tracesof.net/uebersicht/) that shows Codex and Claude Code limit usage side by side.

Chinese version: [README.zh-CN.md](README.zh-CN.md)

![AI Limits widget screenshot](assets/screenshot.png)

The screenshot uses sample values. The widget displays all limit rows as **used limit percentage**.

## What It Shows

- Codex: 5-hour and weekly limit usage from ChatGPT/Codex's official `/wham/usage` endpoint.
- Claude Code: 5-hour, weekly all-models, and Sonnet-only limit usage from Claude's usage endpoint.
- Claude Code session tokens: recent local session input/output/cache token counts.

## What It Reads

- Codex auth: `~/.codex/auth.json`
- Codex usage API: `https://chatgpt.com/backend-api/wham/usage`
- Claude Desktop cookies: `~/Library/Application Support/Claude/Cookies`
- Claude Keychain item: `Claude Safe Storage`
- Claude Code logs: `~/.claude/projects/**/*.jsonl`
- Local caches: `~/.cache/ai-limits/`

The repository does not include or store your tokens. The widget reads local auth/cookies at runtime and calls the official usage endpoints required for display.

## Requirements

1. macOS with Übersicht installed.
2. Codex signed in with ChatGPT auth on the target Mac.
3. Claude Desktop signed in on the target Mac.
4. Claude Code used at least once, so local `~/.claude` logs exist.
5. Python 3.
6. `ccusage` for Claude Code local session summaries.

Recommended setup:

```bash
brew install --cask ubersicht
brew install bun
bun install -g ccusage
```

## Install

```bash
git clone git@github.com:XinDongol/ubersicht-token-widget.git
cd ubersicht-token-widget
./install.sh
```

The installer copies the widget to:

```bash
~/Library/Application Support/Übersicht/widgets/ai-limits.widget
```

It also creates a local Python virtual environment inside the widget folder and installs dependencies from `requirements.txt`.

Open Übersicht if it is not already running:

```bash
open -a "Übersicht"
```

## Verify

Run the widget script manually:

```bash
cd "$HOME/Library/Application Support/Übersicht/widgets/ai-limits.widget"
./.venv/bin/python ./ai_limits.py
```

You should see HTML containing sections for `Codex` and `Claude Code`.

Refresh the widget:

```bash
osascript -e 'tell application "Übersicht" to reload widget id "ai-limits-widget-index-coffee"'
```

## Update

```bash
cd ubersicht-token-widget
git pull
./install.sh
```

## Troubleshooting

If Codex shows `offline`, sign in again on that Mac:

```bash
codex login
ls ~/.codex/auth.json
```

If Claude usage is unavailable, make sure Claude Desktop is signed in and the widget dependencies are installed:

```bash
open -a Claude
cd "$HOME/Library/Application Support/Übersicht/widgets/ai-limits.widget"
./.venv/bin/python -m pip install -r requirements.txt
```

If Claude Code session totals are missing:

```bash
bun install -g ccusage
ccusage --version
```

If `ccusage` is installed somewhere custom, set:

```bash
export CCUSAGE_BIN="/absolute/path/to/ccusage"
```

If you use non-default config folders:

```bash
export CODEX_HOME="$HOME/.codex"
export CLAUDE_CONFIG_DIR="$HOME/.claude"
```

Then restart Übersicht.

## Uninstall

```bash
rm -rf "$HOME/Library/Application Support/Übersicht/widgets/ai-limits.widget"
```
