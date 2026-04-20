"""
Send run summaries via Telegram Bot API (HTTPS, no extra deps beyond requests).

Env (recommended): TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
Or set TELEGRAM_TOKEN and CHAT_ID in Config.py
"""

from __future__ import annotations

import os
from typing import Optional, Tuple

import requests


def _cfg(name: str, default: str = "") -> str:
    v = os.environ.get(name)
    if v is not None and str(v).strip():
        return str(v).strip()
    return default


def _is_placeholder_token(token: str) -> bool:
    t = (token or "").strip().lower()
    return not t or t in ("your_bot_token", "xxx", "token_here")


def send_telegram_text(text: str, *, parse_mode: Optional[str] = None) -> Tuple[bool, str]:
    """
    Send one message; splits into chunks if longer than Telegram limits (~4096).
    Returns (success, message).
    """
    try:
        from Config import CHAT_ID, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN
    except ImportError:
        return False, "Config module not found."

    token = _cfg("TELEGRAM_TOKEN", TELEGRAM_TOKEN)
    chat_id = (
        _cfg("TELEGRAM_CHAT_ID", str(TELEGRAM_CHAT_ID or "").strip())
        or _cfg("CHAT_ID", str(CHAT_ID or "").strip())
    )

    if _is_placeholder_token(token):
        return False, "Telegram not configured: set TELEGRAM_TOKEN (BotFather) and TELEGRAM_CHAT_ID."
    if not str(chat_id).strip():
        return False, "Telegram CHAT_ID missing: use @userinfobot or getUpdates."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    max_len = 4000

    parts = []
    s = text or ""
    while s:
        parts.append(s[:max_len])
        s = s[max_len:]

    last_err = ""
    for chunk in parts:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "disable_web_page_preview": True,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        try:
            r = requests.post(url, json=payload, timeout=45)
            data = r.json() if r.content else {}
            if r.status_code != 200 or not data.get("ok"):
                err = data.get("description", r.text[:500])
                last_err = f"HTTP {r.status_code}: {err}"
                return False, last_err
        except requests.RequestException as exc:
            return False, str(exc)[:300]

    suffix = f" ({len(parts)} parts)" if len(parts) > 1 else ""
    return True, f"Telegram OK{suffix}"


def send_telegram_report(header: str, body: str) -> Tuple[bool, str]:
    """Header line + body as single Telegram message (chunked if needed)."""
    full = f"{header.strip()}\n\n{body.strip()}".strip()
    return send_telegram_text(full)
