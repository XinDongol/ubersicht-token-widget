# AI Limits Übersicht Widget

A macOS desktop widget for [Übersicht](https://tracesof.net/uebersicht/) that shows Codex and Claude Code limit usage in one compact panel.

It displays all limit rows as **used limit percentage**:

- Codex: 5-hour and weekly usage from ChatGPT/Codex's official `/wham/usage` endpoint.
- Claude Code: 5-hour, weekly all-models, and Sonnet-only usage from Claude's usage endpoint.
- Claude Code session tokens: recent local session input/output/cache token counts.

## English

### What It Reads

- Codex auth: `~/.codex/auth.json`
- Codex usage API: `https://chatgpt.com/backend-api/wham/usage`
- Claude Desktop cookies: `~/Library/Application Support/Claude/Cookies`
- Claude Keychain item: `Claude Safe Storage`
- Claude Code logs: `~/.claude/projects/**/*.jsonl`
- Local caches: `~/.cache/ai-limits/`

The widget does not store your tokens in the repository. It reads local auth/cookies at runtime and calls the official OpenAI/Anthropic endpoints needed for usage display.

### Requirements

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

### Install

```bash
git clone git@github.com:XinDongol/ubersicht-token-widget.git
cd ubersicht-token-widget
./install.sh
```

The installer copies the widget to:

```bash
~/Library/Application Support/Übersicht/widgets/ai-limits.widget
```

It also creates a local Python virtual environment inside the widget folder and installs Python dependencies from `requirements.txt`.

Open Übersicht if it is not already running:

```bash
open -a "Übersicht"
```

### Verify

Run the widget script manually:

```bash
cd "$HOME/Library/Application Support/Übersicht/widgets/ai-limits.widget"
./.venv/bin/python ./ai_limits.py
```

You should see HTML containing sections for `Codex` and `Claude Code`.

Refresh the widget:

```bash
osascript -e 'tell application "Übersicht" to refresh widget id "ai-limits-widget-index-coffee"'
```

### Update

```bash
cd ubersicht-token-widget
git pull
./install.sh
```

### Troubleshooting

If Codex shows `offline`, sign in again on that Mac:

```bash
codex login
ls ~/.codex/auth.json
```

If Claude usage is unavailable:

```bash
open -a Claude
python3 -m pip install --user -r requirements.txt
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

### Uninstall

```bash
rm -rf "$HOME/Library/Application Support/Übersicht/widgets/ai-limits.widget"
```

## 中文

### 它读取什么

- Codex 登录信息：`~/.codex/auth.json`
- Codex 用量接口：`https://chatgpt.com/backend-api/wham/usage`
- Claude Desktop Cookie：`~/Library/Application Support/Claude/Cookies`
- Claude 钥匙串条目：`Claude Safe Storage`
- Claude Code 日志：`~/.claude/projects/**/*.jsonl`
- 本地缓存：`~/.cache/ai-limits/`

这个仓库不会保存你的 token。组件只会在运行时读取本机登录状态，并调用 OpenAI/Anthropic 的官方用量接口来显示 limit。

### 前置条件

1. macOS，并已安装 Übersicht。
2. 目标 Mac 上 Codex 已用 ChatGPT 登录。
3. 目标 Mac 上 Claude Desktop 已登录。
4. Claude Code 至少使用过一次，这样 `~/.claude` 里才会有本地日志。
5. Python 3。
6. `ccusage`，用于汇总 Claude Code 本地 session token。

推荐安装：

```bash
brew install --cask ubersicht
brew install bun
bun install -g ccusage
```

### 安装

```bash
git clone git@github.com:XinDongol/ubersicht-token-widget.git
cd ubersicht-token-widget
./install.sh
```

安装脚本会把组件复制到：

```bash
~/Library/Application Support/Übersicht/widgets/ai-limits.widget
```

它还会在 widget 目录里创建本地 Python 虚拟环境，并安装 `requirements.txt` 里的依赖。

如果 Übersicht 没有运行，手动打开：

```bash
open -a "Übersicht"
```

### 验证

手动运行组件脚本：

```bash
cd "$HOME/Library/Application Support/Übersicht/widgets/ai-limits.widget"
./.venv/bin/python ./ai_limits.py
```

正常情况下会输出包含 `Codex` 和 `Claude Code` 两个区域的 HTML。

刷新组件：

```bash
osascript -e 'tell application "Übersicht" to refresh widget id "ai-limits-widget-index-coffee"'
```

### 更新

```bash
cd ubersicht-token-widget
git pull
./install.sh
```

### 排障

如果 Codex 显示 `offline`，在那台 Mac 上重新登录：

```bash
codex login
ls ~/.codex/auth.json
```

如果 Claude 用量不可用：

```bash
open -a Claude
python3 -m pip install --user -r requirements.txt
```

如果 Claude Code session token 不显示：

```bash
bun install -g ccusage
ccusage --version
```

如果 `ccusage` 安装在非标准路径，设置：

```bash
export CCUSAGE_BIN="/absolute/path/to/ccusage"
```

如果你使用非默认配置目录：

```bash
export CODEX_HOME="$HOME/.codex"
export CLAUDE_CONFIG_DIR="$HOME/.claude"
```

然后重启 Übersicht。

### 卸载

```bash
rm -rf "$HOME/Library/Application Support/Übersicht/widgets/ai-limits.widget"
```
