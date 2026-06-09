#!/usr/bin/env python3
import html
import hashlib
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone


HOME = pathlib.Path.home()
CODEX_HOME = pathlib.Path(os.environ.get("CODEX_HOME", HOME / ".codex")).expanduser()
CLAUDE_HOME = pathlib.Path(os.environ.get("CLAUDE_CONFIG_DIR", HOME / ".claude")).expanduser()
CLAUDE_APP_HOME = HOME / "Library/Application Support/Claude"
CCUSAGE_BIN = os.environ.get("CCUSAGE_BIN") or shutil.which("ccusage")
CODEX_USAGE_CACHE = HOME / ".cache/ai-limits/codex_usage.json"
CLAUDE_PLAN_CACHE = HOME / ".cache/ai-limits/claude_plan_usage.json"
LOCAL_TZ = datetime.now().astimezone().tzinfo
CODEX_USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"


def parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def dt_to_epoch(dt):
    if not dt:
        return None
    return dt.astimezone(timezone.utc).timestamp()


def fmt_int(value):
    try:
        value = int(value or 0)
    except Exception:
        return "0"
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.0f}k"
    return str(value)


def fmt_money(value):
    try:
        return f"${float(value):.2f}"
    except Exception:
        return "$0.00"


def fmt_clock(epoch):
    if not epoch:
        return "--"
    return datetime.fromtimestamp(float(epoch), LOCAL_TZ).strftime("%H:%M")


def fmt_codex_reset(epoch):
    if not epoch:
        return ""
    try:
        dt = datetime.fromtimestamp(float(epoch), LOCAL_TZ)
    except Exception:
        return ""
    now = datetime.now(LOCAL_TZ)
    if dt.date() == now.date():
        return dt.strftime("%I:%M %p").lstrip("0")
    return dt.strftime("%b %d").replace(" 0", " ")


def fmt_delta_to_epoch(epoch):
    if not epoch:
        return "--"
    seconds = int(float(epoch) - time.time())
    if seconds <= 0:
        return "now"
    minutes = seconds // 60
    hours = minutes // 60
    minutes = minutes % 60
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def fmt_reset(iso_value):
    dt = parse_iso(iso_value)
    if not dt:
        return ""
    epoch = dt_to_epoch(dt)
    delta = fmt_delta_to_epoch(epoch)
    if delta == "now":
        return "resets now"
    return f"resets {delta}"


def pct_class(percent):
    if percent is None:
        return "idle"
    if percent >= 85:
        return "danger"
    if percent >= 65:
        return "warn"
    return "ok"


def remaining_class(percent):
    if percent is None:
        return "idle"
    if percent <= 15:
        return "danger"
    if percent <= 35:
        return "warn"
    return "ok"


def clamp_percent(value):
    try:
        return max(0, min(100, float(value)))
    except Exception:
        return 0


def short_model_name(model):
    model = model or "Claude"
    parts = model.split("-")
    family = next((p for p in parts if p in ("opus", "sonnet", "haiku")), parts[0])
    nums = [p for p in parts if p.replace(".", "").isdigit()]
    if nums:
        version = nums[-1]
        if len(version) == 1:
            version = f"4.{version}" if family in ("opus", "sonnet", "haiku") else version
        return f"{family.capitalize()} {version}"
    return family.capitalize()


def read_codex_session_limits():
    sessions = CODEX_HOME / "sessions"
    if not sessions.exists():
        return {"error": "No Codex sessions"}

    latest = None
    latest_dt = None
    files = sorted(sessions.glob("**/*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)

    for path in files:
        if latest_dt and path.stat().st_mtime < latest_dt.timestamp() - 300:
            break
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    try:
                        event = json.loads(line)
                    except Exception:
                        continue
                    payload = event.get("payload")
                    if not isinstance(payload, dict) or payload.get("type") != "token_count":
                        continue
                    rate_limits = payload.get("rate_limits")
                    if not isinstance(rate_limits, dict):
                        continue
                    dt = parse_iso(event.get("timestamp"))
                    if not dt or (latest_dt and dt <= latest_dt):
                        continue
                    latest_dt = dt
                    latest = {
                        "timestamp": dt,
                        "rate_limits": rate_limits,
                        "info": payload.get("info") if isinstance(payload.get("info"), dict) else {},
                    }
        except Exception:
            continue

    if not latest:
        return {"error": "No Codex limits yet"}
    return latest


def read_codex_auth():
    auth_path = CODEX_HOME / "auth.json"
    try:
        auth = json.loads(auth_path.read_text())
        tokens = auth.get("tokens") if isinstance(auth, dict) else None
        if not isinstance(tokens, dict):
            return None, None, "Codex auth tokens missing"
        token = tokens.get("access_token")
        if not token:
            return None, None, "Codex access token missing"
        return token, tokens.get("account_id"), None
    except Exception:
        return None, None, "Codex auth unreadable"


def fetch_codex_usage():
    token, account_id, error = read_codex_auth()
    if error:
        return {"error": error}

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "OAI-Language": "en",
        "X-OpenAI-Attach-Auth": "1",
        "X-OpenAI-Attach-Integrity-State": "1",
        "originator": "Codex Desktop",
    }
    if account_id:
        headers["ChatGPT-Account-Id"] = account_id

    request = urllib.request.Request(CODEX_USAGE_URL, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not isinstance(data, dict):
            return {"error": "Codex usage response invalid"}
        return {"data": data, "fetched_at": time.time()}
    except urllib.error.HTTPError as exc:
        return {"error": f"Codex usage HTTP {exc.code}"}
    except Exception as exc:
        return {"error": f"Codex usage fetch failed: {type(exc).__name__}"}


def read_codex_usage():
    try:
        if CODEX_USAGE_CACHE.exists() and time.time() - CODEX_USAGE_CACHE.stat().st_mtime < 50:
            cached = json.loads(CODEX_USAGE_CACHE.read_text())
            if isinstance(cached, dict) and "data" in cached:
                cached["cached"] = True
                return cached
    except Exception:
        pass

    fresh = fetch_codex_usage()
    if "data" in fresh:
        try:
            CODEX_USAGE_CACHE.parent.mkdir(parents=True, exist_ok=True)
            CODEX_USAGE_CACHE.write_text(json.dumps(fresh))
        except Exception:
            pass
        return fresh

    try:
        cached = json.loads(CODEX_USAGE_CACHE.read_text())
        if isinstance(cached, dict) and "data" in cached:
            cached["stale"] = True
            cached["error"] = fresh.get("error")
            return cached
    except Exception:
        pass
    return fresh


def decrypt_chrome_cookie(encrypted_value, host_key, password):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    data = bytes(encrypted_value)
    if not data:
        return ""
    if data.startswith((b"v10", b"v11")):
        data = data[3:]
    key = hashlib.pbkdf2_hmac("sha1", password.encode("utf-8"), b"saltysalt", 1003, 16)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(b" " * 16), backend=default_backend()).decryptor()
    plain = decryptor.update(data) + decryptor.finalize()
    pad = plain[-1]
    if 1 <= pad <= 16 and plain[-pad:] == bytes([pad]) * pad:
        plain = plain[:-pad]
    host_digest = hashlib.sha256(host_key.encode("utf-8")).digest()
    if plain.startswith(host_digest):
        plain = plain[32:]
    return plain.decode("utf-8")


def read_claude_cookies():
    cookie_db = CLAUDE_APP_HOME / "Cookies"
    if not cookie_db.exists():
        return None, [], "Claude cookies missing"
    try:
        password = subprocess.check_output(
            ["/usr/bin/security", "find-generic-password", "-w", "-s", "Claude Safe Storage"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).rstrip("\n")
    except Exception:
        return None, [], "Claude Safe Storage unavailable"

    cookies = []
    org = None
    try:
        con = sqlite3.connect(f"file:{cookie_db}?mode=ro", uri=True)
        rows = con.execute(
            "select host_key, name, value, encrypted_value, path "
            "from cookies where host_key like '%claude.ai%'"
        )
        for host, name, value, encrypted_value, path in rows:
            try:
                cookie_value = value or decrypt_chrome_cookie(encrypted_value, host, password)
            except Exception:
                continue
            if not cookie_value:
                continue
            cookies.append((host, name, cookie_value, path or "/"))
            if name == "lastActiveOrg":
                org = cookie_value
        con.close()
    except Exception:
        return None, [], "Claude cookie DB unreadable"
    if not org:
        return None, cookies, "lastActiveOrg cookie missing"
    return org, cookies, None


def fetch_claude_plan_usage():
    try:
        from curl_cffi import requests
    except Exception:
        return {"error": "curl_cffi missing"}

    org, cookies, error = read_claude_cookies()
    if error:
        return {"error": error}

    session = requests.Session(impersonate="chrome136")
    for host, name, value, path in cookies:
        session.cookies.set(name, value, domain=host, path=path)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://claude.ai",
        "Referer": "https://claude.ai/",
    }
    try:
        response = session.get(
            f"https://claude.ai/api/organizations/{org}/usage",
            headers=headers,
            timeout=20,
        )
        if response.status_code != 200:
            return {"error": f"Claude usage HTTP {response.status_code}"}
        data = response.json()
        if not isinstance(data, dict):
            return {"error": "Claude usage response invalid"}
        return {"data": data, "fetched_at": time.time()}
    except Exception as exc:
        return {"error": f"Claude usage fetch failed: {type(exc).__name__}"}


def read_claude_plan_usage():
    try:
        if CLAUDE_PLAN_CACHE.exists() and time.time() - CLAUDE_PLAN_CACHE.stat().st_mtime < 180:
            cached = json.loads(CLAUDE_PLAN_CACHE.read_text())
            if isinstance(cached, dict) and "data" in cached:
                cached["cached"] = True
                return cached
    except Exception:
        pass

    fresh = fetch_claude_plan_usage()
    if "data" in fresh:
        try:
            CLAUDE_PLAN_CACHE.parent.mkdir(parents=True, exist_ok=True)
            CLAUDE_PLAN_CACHE.write_text(json.dumps(fresh))
        except Exception:
            pass
        return fresh

    try:
        cached = json.loads(CLAUDE_PLAN_CACHE.read_text())
        if isinstance(cached, dict) and "data" in cached:
            cached["stale"] = True
            return cached
    except Exception:
        pass
    return fresh


def read_claude_session_usage():
    files = sorted(
        CLAUDE_HOME.glob("projects/**/*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not files:
        return {"error": "No Claude Code session logs"}

    totals = {}
    latest_time = None
    for path in files[:1]:
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    try:
                        event = json.loads(line)
                    except Exception:
                        continue
                    message = event.get("message")
                    if not isinstance(message, dict):
                        continue
                    usage = message.get("usage")
                    if not isinstance(usage, dict):
                        continue
                    model = message.get("model") or "claude"
                    bucket = totals.setdefault(
                        model,
                        {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0},
                    )
                    bucket["input"] += int(usage.get("input_tokens") or 0)
                    bucket["output"] += int(usage.get("output_tokens") or 0)
                    bucket["cache_read"] += int(usage.get("cache_read_input_tokens") or 0)
                    bucket["cache_write"] += int(usage.get("cache_creation_input_tokens") or 0)
                    latest_time = event.get("timestamp") or latest_time
        except Exception:
            continue

    if not totals:
        return {"error": "No Claude Code token usage"}
    rows = []
    for model, counts in totals.items():
        rows.append(
            {
                "model": model,
                **counts,
                "total": counts["input"] + counts["output"] + counts["cache_read"] + counts["cache_write"],
            }
        )
    rows.sort(key=lambda row: row["total"], reverse=True)
    return {"rows": rows, "timestamp": latest_time}


def run_ccusage(args, timeout=8):
    candidates = [
        pathlib.Path(CCUSAGE_BIN).expanduser() if CCUSAGE_BIN else None,
        HOME / ".bun/bin/ccusage",
        pathlib.Path("/opt/homebrew/bin/ccusage"),
        pathlib.Path("/usr/local/bin/ccusage"),
    ]
    ccusage = next((path for path in candidates if path and path.exists()), None)
    if not ccusage:
        return None
    try:
        output = subprocess.check_output(
            [str(ccusage), *args],
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            text=True,
        )
        return json.loads(output)
    except Exception:
        return None


def read_claude_blocks():
    data = run_ccusage(["claude", "blocks", "--active", "--json", "--offline"])
    blocks = data.get("blocks", []) if isinstance(data, dict) else []
    if not blocks:
        data = run_ccusage(["claude", "blocks", "--recent", "--order", "desc", "--json", "--offline"])
        blocks = data.get("blocks", []) if isinstance(data, dict) else []
    if not blocks:
        data = run_ccusage(["claude", "blocks", "--order", "desc", "--json", "--offline"])
        blocks = data.get("blocks", []) if isinstance(data, dict) else []

    clean = [b for b in blocks if isinstance(b, dict) and not b.get("isGap")]
    if not clean:
        return {"error": "No Claude Code usage"}
    active = next((b for b in clean if b.get("isActive")), None)
    return active or clean[0]


def bar(label, percent, caption, mode="used"):
    safe_percent = clamp_percent(percent)
    shown = "--" if percent is None else f"{safe_percent:.0f}%"
    css_class = remaining_class(percent) if mode == "remaining" else pct_class(percent)
    return f"""
      <div class="limit-row {css_class}">
        <div class="limit-copy">
          <span>{html.escape(label)}</span>
          <strong>{shown}</strong>
          <em>{html.escape(caption)}</em>
        </div>
        <div class="meter"><i style="width:{safe_percent:.1f}%"></i></div>
      </div>
    """


def codex_window_label(bucket):
    seconds = bucket.get("limit_window_seconds")
    try:
        minutes = int(seconds or 0) // 60
    except Exception:
        minutes = 0
    if 285 <= minutes <= 315:
        return "5h"
    if 9500 <= minutes <= 10600:
        return "Weekly"
    if minutes >= 1440:
        return f"{round(minutes / 1440)}d"
    if minutes >= 60:
        return f"{round(minutes / 60)}h"
    return "Limit"


def remaining_from_used(used):
    if used is None:
        return None
    return 100 - clamp_percent(used)


def render_codex_live(data):
    usage = data["data"]
    rate_limit = usage.get("rate_limit") if isinstance(usage.get("rate_limit"), dict) else {}
    primary = rate_limit.get("primary_window") if isinstance(rate_limit.get("primary_window"), dict) else {}
    secondary = rate_limit.get("secondary_window") if isinstance(rate_limit.get("secondary_window"), dict) else {}
    plan = usage.get("plan_type") or "plan"
    reached = usage.get("rate_limit_reached_type") or rate_limit.get("limit_reached")
    badge = "stale" if data.get("stale") else str(plan)
    status = "limited" if reached else badge
    fetched = datetime.fromtimestamp(data.get("fetched_at", time.time()), LOCAL_TZ).strftime("%H:%M")
    error = data.get("error")
    error_html = f"<span>{html.escape(error)}</span>" if error and data.get("stale") else ""

    return f"""
      <section>
        <div class="service-head"><span>Codex</span><b>{html.escape(status)}</b></div>
        <div class="subhead">Limit usage</div>
        {bar(codex_window_label(primary), primary.get("used_percent"), fmt_codex_reset(primary.get("reset_at")))}
        {bar(codex_window_label(secondary), secondary.get("used_percent"), fmt_codex_reset(secondary.get("reset_at")))}
        <div class="stats">
          <span>fetched {fetched}</span>
          {error_html}
        </div>
      </section>
    """


def render_codex_session_fallback(data, error=None):
    rate_limits = data["rate_limits"]
    primary = rate_limits.get("primary") or {}
    secondary = rate_limits.get("secondary") or {}
    timestamp = data["timestamp"].astimezone(LOCAL_TZ).strftime("%H:%M")
    error_html = f"<span>{html.escape(error)}</span>" if error else ""

    return f"""
      <section>
        <div class="service-head"><span>Codex</span><b>stale</b></div>
        <div class="subhead">Limit usage</div>
        {bar("5h", primary.get("used_percent"), fmt_codex_reset(primary.get("resets_at")))}
        {bar("Weekly", secondary.get("used_percent"), fmt_codex_reset(secondary.get("resets_at")))}
        <div class="stats">
          <span>session snapshot {timestamp}</span>
          {error_html}
        </div>
      </section>
    """


def render_codex():
    data = read_codex_usage()
    if data.get("data"):
        return render_codex_live(data)

    fallback = read_codex_session_limits()
    if not fallback.get("error"):
        return render_codex_session_fallback(fallback, data.get("error"))

    error = data.get("error") or fallback.get("error") or "No Codex limits yet"
    if error:
        return f"""
          <section>
            <div class="service-head"><span>Codex</span><b>offline</b></div>
            <div class="empty">{html.escape(error)}</div>
          </section>
        """


def render_claude():
    plan = read_claude_plan_usage()
    session = read_claude_session_usage()
    badge = "plan"
    if plan.get("stale"):
        badge = "stale"

    if plan.get("error"):
        plan_html = f'<div class="empty">{html.escape(plan["error"])}</div>'
        badge = "offline"
    else:
        data = plan["data"]
        five_hour = data.get("five_hour") or {}
        seven_day = data.get("seven_day") or {}
        sonnet = data.get("seven_day_sonnet") or {}
        plan_html = "\n".join(
            [
                bar("5-hour limit", five_hour.get("utilization"), fmt_reset(five_hour.get("resets_at"))),
                bar("Weekly · all models", seven_day.get("utilization"), fmt_reset(seven_day.get("resets_at"))),
                bar("Sonnet only", sonnet.get("utilization"), fmt_reset(sonnet.get("resets_at"))),
            ]
        )

    if session.get("error"):
        session_html = f'<div class="empty">{html.escape(session["error"])}</div>'
    else:
        rows = []
        for row in session["rows"][:3]:
            rows.append(
                f"""
                <div class="usage-row">
                  <span>{html.escape(short_model_name(row["model"]))}</span>
                  <b>{fmt_int(row["input"])}</b>
                  <b>{fmt_int(row["output"])}</b>
                  <b>{fmt_int(row["cache_read"])}</b>
                  <b>{fmt_int(row["cache_write"])}</b>
                </div>
                """
            )
        total = sum(row["total"] for row in session["rows"])
        session_html = f"""
          <div class="usage-table">
            <div class="usage-head"><span></span><span>in</span><span>out</span><span>cache r</span><span>cache w</span></div>
            {''.join(rows)}
            <div class="usage-total"><span>Total</span><strong>{fmt_int(total)}</strong></div>
          </div>
        """

    return f"""
      <section>
        <div class="service-head"><span>Claude Code</span><b>{badge}</b></div>
        <div class="subhead">Limit usage</div>
        {plan_html}
        <div class="subhead session-label">Session usage</div>
        {session_html}
      </section>
    """


def main():
    updated = datetime.now().strftime("%H:%M")
    print(f"""
      <div class="panel">
        <div class="topline">
          <div>
            <p>AI Limits</p>
            <h1>Codex + Claude</h1>
          </div>
          <time>{updated}</time>
        </div>
        {render_codex()}
        {render_claude()}
      </div>
    """)


if __name__ == "__main__":
    main()
