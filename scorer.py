from Config import MY_SKILLS, ROLE_PRIORITY
try:
    from duplicate_filter import is_new_job
except ImportError:
    # Fallback if the file hasn't been renamed yet
    def is_new_job(link): return True

def score_job(row):
    link = row.get("link", "")
    # Ensure we don't crash on missing links and handle duplicates
    if not link:
        return 0
    if is_new_job and not is_new_job(link):
        return -1  # Mark for exclusion or lowest priority

    title = str(row.get("title") or "").lower()
    desc = str(row.get("description") or "").lower()
    text = f"{title} {desc}"

    score = 0
    for skill in MY_SKILLS:
        if skill in text:
            score += 2

    # Priority (avoid overlap) — use full posting text when description exists
    if "senior data analyst" in text:
        score += ROLE_PRIORITY["senior data analyst"]
    elif "data analyst" in text:
        score += ROLE_PRIORITY["data analyst"]
    elif "data scientist" in text:
        score += ROLE_PRIORITY["data scientist"]

    return score


def rank_jobs(df):
    """Add score column and return dataframe sorted by score (highest first)."""
    out = df.copy()
    out["score"] = out.apply(score_job, axis=1)
    return out.sort_values("score", ascending=False).reset_index(drop=True)
