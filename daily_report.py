"""
Daily digest of Easy Apply attempts (reads applications_log.jsonl).

Schedule once per day (Windows Task Scheduler) e.g.:
  python daily_report.py

Use the same SMTP / Telegram settings as main.py (Config + environment).

  python daily_report.py --dry-run   # print only, no email/Telegram
"""

from __future__ import annotations

import argparse

from application_tracker import build_daily_digest_text, send_daily_digest


def main() -> None:
    p = argparse.ArgumentParser(description="Send daily application progress to email and Telegram.")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print digest to the console only; do not send messages.",
    )
    p.add_argument("--no-email", action="store_true", help="Skip email.")
    p.add_argument("--no-telegram", action="store_true", help="Skip Telegram.")
    args = p.parse_args()

    text = build_daily_digest_text()
    print(text)

    if args.dry_run:
        return

    send_daily_digest(email=not args.no_email, telegram=not args.no_telegram)


if __name__ == "__main__":
    main()
