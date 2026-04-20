from __future__ import annotations

import argparse
import webbrowser
from typing import Optional

from apply_kit import (
    generate_cover_letter,
    generate_cover_letter_da,
    generate_cover_letter_ds,
    generate_pro_tips,
    generate_quick_answers,
    generate_quick_answers_da,
    generate_quick_answers_ds,
    generate_real_workflow,
    infer_application_role,
)
from Config import (
    DESCRIPTION_FETCH_LIMIT,
    LINKEDIN_USER_DATA_DIR,
    LOCATION,
    REQUEST_DELAY_SEC,
    SEARCH_KEYWORD,
)
from email_notify import format_run_report, send_smtp_email
from telegram_notify import send_telegram_report
from scraper import enrich_jobs_with_descriptions, fetch_jobs
from scorer import rank_jobs


def run(
    keyword: Optional[str] = None,
    with_descriptions: bool = True,
    desc_limit: Optional[int] = None,
    open_browser: bool = True,
    auto_apply: bool = False,
    apply_limit: int = 2,
    send_email: bool = False,
    send_telegram: bool = False,
) -> None:
    kw = keyword if keyword is not None else SEARCH_KEYWORD
    limit = desc_limit if desc_limit is not None else DESCRIPTION_FETCH_LIMIT

    def _notify(subject_note: str, top_jobs_lines: str, auto_apply_lines: str = "", notes: str = "") -> None:
        if not send_email and not send_telegram:
            return
        body = format_run_report(
            keyword=kw,
            location=LOCATION,
            top_jobs_lines=top_jobs_lines,
            auto_apply_lines=auto_apply_lines,
            notes=notes,
        )
        subj = f"Job analyzer: {subject_note}"
        if send_email:
            ok, msg = send_smtp_email(subj[:200], body)
            print(f"[*] Email: {'OK - ' if ok else ''}{msg}")
        if send_telegram:
            ok_t, msg_t = send_telegram_report(subj, body)
            print(f"[*] Telegram: {'OK - ' if ok_t else ''}{msg_t}")

    print(f"[*] Fetching jobs (keyword={kw!r}, location={LOCATION})...")
    df = fetch_jobs(keyword=kw, location=LOCATION)

    if df is None or df.empty:
        print("[!] No jobs found. Try a different keyword or location.")
        _notify(
            "no jobs",
            "(LinkedIn returned no rows - blocked, wrong keyword, or no listings.)",
            notes="Fix: log in via browser once, or change keyword/location.",
        )
        return

    required_cols = {"title", "company", "link"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"[!] Missing expected columns from scraper output: {missing}")
        _notify("schema error", f"Missing columns: {missing}")
        return

    print("[*] Ranking jobs (title)...")
    df = rank_jobs(df)

    if with_descriptions:
        print(
            f"[*] Loading job descriptions for top {min(limit, len(df))} postings "
            f"(~{REQUEST_DELAY_SEC}s between requests)..."
        )
        df = enrich_jobs_with_descriptions(df, limit=limit, delay_sec=REQUEST_DELAY_SEC)
        print("[*] Re-ranking using full job text...")
        df = rank_jobs(df)

    if df is None or df.empty:
        print("[!] Ranking produced no results.")
        _notify("empty after rank", "(No rows after ranking.)")
        return

    print("\n--- TOP JOBS ---\n")
    cols = ["title", "company", "score"]
    if "description" in df.columns:
        cols.append("description")
    show = df.head(5)[[c for c in cols if c in df.columns]]
    # Avoid dumping huge description text in the terminal
    if "description" in show.columns:
        show = show.copy()
        show["description"] = show["description"].apply(
            lambda x: (str(x)[:120] + "…") if len(str(x)) > 120 else str(x)
        )
    print(show.to_string(index=False))

    print("\n[*] Saving jobs to Excel...")
    df.to_excel("jobs.xlsx", index=False)

    if open_browser and not auto_apply:
        print("\n[*] Opening top jobs in browser...")
        for link in df["link"].head(3).tolist():
            if link and isinstance(link, str) and link.strip():
                webbrowser.open_new_tab(link)

    job = df.iloc[0]

    print("\n=== DATA ANALYST ROLE — QUICK APPLY (paste for DA / BI postings) ===")
    print(generate_quick_answers_da(job))

    print("\n=== DATA ANALYST ROLE — COVER LETTER ===")
    print(generate_cover_letter_da(job))

    print("\n=== DATA SCIENCE ROLE — QUICK APPLY (paste for DS / ML postings) ===")
    print(generate_quick_answers_ds(job))

    print("\n=== DATA SCIENCE ROLE — COVER LETTER ===")
    print(generate_cover_letter_ds(job))

    inferred = infer_application_role(job)
    print(f"\n=== AUTO VARIANT FOR TOP JOB (inferred: {inferred}; used by --auto-apply) ===")
    print(generate_quick_answers(job))
    print()
    print(generate_cover_letter(job))

    print("\n" + generate_real_workflow())
    print("\n" + generate_pro_tips())

    apply_log = ""
    if auto_apply:
        from linkedin_apply import run_easy_apply_assist

        print("\n[*] Starting Easy Apply assist (Playwright)...")
        attempts = run_easy_apply_assist(
            df,
            limit=apply_limit,
            user_data_dir=LINKEDIN_USER_DATA_DIR or "",
            headless=False,
        )
        apply_log = "\n".join(a.line() for a in attempts) if attempts else ""

    if send_email or send_telegram:
        cols_out = ["title", "company", "score", "link"]
        have = [c for c in cols_out if c in df.columns]
        top_txt = df.head(8)[have].to_string(index=False) if have else df.head(8).to_string(index=False)
        _notify(f"{kw} @ {LOCATION}", top_txt, auto_apply_lines=apply_log)


def _cli():
    p = argparse.ArgumentParser(description="Job analyzer: rank jobs and build tailored applications.")
    p.add_argument("--keyword", default=SEARCH_KEYWORD, help="LinkedIn search keywords")
    p.add_argument(
        "--no-descriptions",
        action="store_true",
        help="Skip fetching job description pages (faster; weaker matching)",
    )
    p.add_argument(
        "--desc-limit",
        type=int,
        default=DESCRIPTION_FETCH_LIMIT,
        metavar="N",
        help="How many top rows to fetch full posting text for",
    )
    p.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open job URLs in the default browser",
    )
    p.add_argument(
        "--auto-apply",
        action="store_true",
        help="After printing, open Playwright and fill Easy Apply forms (does not submit)",
    )
    p.add_argument(
        "--apply-limit",
        type=int,
        default=2,
        metavar="N",
        help="How many jobs to process with --auto-apply",
    )
    p.add_argument(
        "--email",
        action="store_true",
        help="Email a run summary (set SMTP_USER + SMTP_PASSWORD; see Config.py). Uses EMAIL as inbox if EMAIL_TO is empty.",
    )
    p.add_argument(
        "--telegram",
        action="store_true",
        help="Send the same summary to Telegram (TELEGRAM_TOKEN + TELEGRAM_CHAT_ID or CHAT_ID in Config).",
    )
    p.add_argument(
        "--notify-all",
        action="store_true",
        help="Shortcut: enable both --email and --telegram",
    )
    args = p.parse_args()
    send_email = args.email or args.notify_all
    send_telegram = args.telegram or args.notify_all
    run(
        keyword=args.keyword,
        with_descriptions=not args.no_descriptions,
        desc_limit=args.desc_limit,
        open_browser=not args.no_browser,
        auto_apply=args.auto_apply,
        apply_limit=args.apply_limit,
        send_email=send_email,
        send_telegram=send_telegram,
    )


if __name__ == "__main__":
    _cli()
