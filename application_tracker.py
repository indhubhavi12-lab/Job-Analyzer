"""
Append-only JSONL log of Easy Apply attempts (for daily progress reports).
File lives next to this module: applications_log.jsonl
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

LOG_PATH = Path(__file__).resolve().parent / "applications_log.jsonl"


def log_apply_batch(attempts: Any) -> None:
    """Persist each ApplyAttempt after a Playwright run (duck-typed; no import cycle)."""
    if not attempts:
        return

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        for a in attempts:
            if not (hasattr(a, "status") and hasattr(a, "link")):
                continue
            rec = {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "index": int(getattr(a, "index", 0)),
                "title": str(getattr(a, "title", "") or ""),
                "company": str(getattr(a, "company", "") or ""),
                "link": str(getattr(a, "link", "") or ""),
                "status": str(getattr(a, "status", "") or ""),
                "detail": str(getattr(a, "detail", "") or "")[:800],
                "source": "easy_apply_assist",
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _parse_event_date(rec: Dict[str, Any]) -> Optional[date]:
    ts = rec.get("ts") or ""
    try:
        if "T" in ts:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")[:19]).date()
        return date.fromisoformat(ts[:10])
    except ValueError:
        return None


def events_for_date(target: date) -> List[Dict[str, Any]]:
    if not LOG_PATH.is_file():
        return []
    out: List[Dict[str, Any]] = []
    try:
        lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        d = _parse_event_date(rec)
        if d == target:
            out.append(rec)
    return out


def build_daily_digest_text(report_date: Optional[date] = None) -> str:
    """Human-readable summary for email/Telegram."""
    report_date = report_date or date.today()
    lines: List[str] = []

    lines.append(f"Job applications - daily progress ({report_date.isoformat()})")
    lines.append("")

    today_events = events_for_date(report_date)
    lines.append(f"--- Today ({report_date}) - {len(today_events)} Easy Apply event(s) ---")
    if not today_events:
        lines.append("(Nothing logged today yet. Runs with --auto-apply append to applications_log.jsonl.)")
    else:
        for rec in today_events:
            co = (rec.get("company") or "")[:50]
            ti = (rec.get("title") or "")[:70]
            st = rec.get("status") or ""
            lines.append(f"  [{st}] {co} | {ti}")

    lines.append("")
    lines.append("--- Last 7 days (attempts / filled) ---")
    for i in range(6, -1, -1):
        d = report_date - timedelta(days=i)
        day_list = events_for_date(d)
        n = len(day_list)
        filled = sum(1 for x in day_list if x.get("status") == "filled")
        lines.append(f"  {d}: {n} attempts, {filled} form(s) filled")

    lines.append("")
    lines.append(f"Log file: {LOG_PATH.name} (same folder as the project).")
    return "\n".join(lines)


def send_daily_digest(email: bool = True, telegram: bool = True) -> None:
    """Send digest via configured email and/or Telegram."""
    body = build_daily_digest_text()
    subj = f"Job analyzer: daily progress ({date.today().isoformat()})"

    if email:
        try:
            from email_notify import send_smtp_email

            ok, msg = send_smtp_email(subj[:200], body)
            print(f"[*] Daily email: {'OK - ' if ok else ''}{msg}")
        except Exception as exc:
            print(f"[!] Daily email error: {exc}")

    if telegram:
        try:
            from telegram_notify import send_telegram_report

            ok, msg = send_telegram_report(subj, body)
            print(f"[*] Daily Telegram: {'OK - ' if ok else ''}{msg}")
        except Exception as exc:
            print(f"[!] Daily Telegram error: {exc}")
