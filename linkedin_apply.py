"""
Best-effort LinkedIn Easy Apply helper (Playwright).

- Fills visible text areas with JD-tailored cover letter and quick answers.
- Does NOT click final Submit (you review and submit yourself).

LinkedIn changes their UI often; automation may break. Check LinkedIn's terms
before using bots on your account.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    import pandas as pd


def _playwright():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None
    return sync_playwright


@dataclass
class ApplyAttempt:
    index: int
    title: str
    company: str
    link: str
    status: str
    detail: str = ""

    def line(self) -> str:
        co = (self.company or "")[:40]
        head = f"{co} | {self.title[:60]}" if co else self.title[:80]
        return f"[{self.status}] {head} - {self.detail}".replace("\n", " ")


def run_easy_apply_assist(
    df: "pd.DataFrame",
    limit: int = 3,
    user_data_dir: str = "",
    headless: bool = False,
    pause_sec: float = 2.0,
) -> List[ApplyAttempt]:
    """
    Open each job URL, click Easy Apply if found, fill visible ``textarea`` fields.

    Returns a list of :class:`ApplyAttempt` rows for logging and email summaries.

    ``user_data_dir``: optional Chromium profile folder so you stay logged in to LinkedIn
    (set ``LINKEDIN_USER_DATA_DIR`` in Config or pass path).
    """
    results: List[ApplyAttempt] = []
    pw_factory = _playwright()
    if pw_factory is None:
        print("[!] Playwright not installed. Run: pip install playwright && playwright install chromium")
        results.append(
            ApplyAttempt(0, "", "", "", "error", "Playwright not installed"),
        )
        return results

    from apply_kit import generate_cover_letter, generate_quick_answers

    n = min(int(limit), len(df))
    if n <= 0:
        print("[!] No jobs to process.")
        results.append(ApplyAttempt(0, "", "", "", "error", "No jobs to process"))
        return results

    cover_blocks = []
    answers_blocks = []
    for i in range(n):
        row = df.iloc[i]
        cover_blocks.append(generate_cover_letter(row))
        answers_blocks.append(generate_quick_answers(row))

    browser = None
    persistent: Optional[object] = None

    with pw_factory() as p:
        if user_data_dir and str(user_data_dir).strip():
            persistent = p.chromium.launch_persistent_context(
                str(user_data_dir).strip(),
                headless=headless,
                viewport={"width": 1400, "height": 900},
            )
            page = persistent.pages[0] if persistent.pages else persistent.new_page()
        else:
            browser = p.chromium.launch(headless=headless)
            ctx = browser.new_context(viewport={"width": 1400, "height": 900})
            page = ctx.new_page()

        try:
            for i in range(n):
                row = df.iloc[i]
                link = str(row.get("link") or "").strip()
                title = str(row.get("title") or "")
                company = str(row.get("company") or "")
                if not link:
                    print(f"[!] Row {i + 1}: missing link, skip.")
                    results.append(
                        ApplyAttempt(i + 1, title, company, link, "skipped", "missing link"),
                    )
                    continue

                print(f"[*] ({i + 1}/{n}) Opening: {title[:60]}...")
                try:
                    page.goto(link, wait_until="domcontentloaded", timeout=60000)
                except Exception as exc:
                    print(f"[!] Navigation failed: {exc}")
                    results.append(
                        ApplyAttempt(i + 1, title, company, link, "error_nav", str(exc)[:200]),
                    )
                    continue

                time.sleep(max(pause_sec, 1.0))

                clicked = False
                for pattern in (r"Easy Apply", r"\bApply\b"):
                    try:
                        loc = page.get_by_role("button", name=re.compile(pattern, re.I)).first
                        loc.wait_for(state="visible", timeout=8000)
                        loc.click(timeout=8000)
                        clicked = True
                        break
                    except Exception:
                        continue

                if not clicked:
                    print("[!] Easy Apply / Apply button not found (login wall or different layout).")
                    results.append(
                        ApplyAttempt(i + 1, title, company, link, "no_apply_button", "Easy Apply not found"),
                    )
                    continue

                time.sleep(pause_sec)

                textareas = page.locator("textarea:visible")
                count = textareas.count()
                if count == 0:
                    print("[!] No visible text areas - form may be non-standard or multi-step.")
                    results.append(
                        ApplyAttempt(i + 1, title, company, link, "no_textarea", "No visible textareas"),
                    )
                    continue

                ctext = cover_blocks[i]
                atext = answers_blocks[i]
                try:
                    textareas.nth(0).fill(ctext[:8000])
                    if count > 1:
                        textareas.nth(1).fill(atext[:8000])
                except Exception as exc:
                    print(f"[!] Could not fill fields: {exc}")
                    results.append(
                        ApplyAttempt(i + 1, title, company, link, "error_fill", str(exc)[:200]),
                    )
                else:
                    print("[*] Filled first text area(s). Review the form; we do not auto-submit.")
                    results.append(
                        ApplyAttempt(
                            i + 1,
                            title,
                            company,
                            link,
                            "filled",
                            "textarea(s) filled; submit manually",
                        ),
                    )

        finally:
            if persistent is not None:
                try:
                    persistent.close()
                except Exception:
                    pass
            elif browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass

    try:
        from application_tracker import log_apply_batch

        log_apply_batch(results)
    except Exception:
        pass

    return results
