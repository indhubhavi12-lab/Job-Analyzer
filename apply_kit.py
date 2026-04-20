# apply_kit.py

import math

import pandas as pd

from Config import (
    DATA_SCIENCE_PROJECT_AREAS,
    DATA_SCIENCE_STATUS,
    LOCATION,
    MY_SKILLS,
    NAME,
    STATE,
    TOTAL_YEARS_EXPERIENCE,
    WORK_PREFERENCE,
    YEARS_DATA_ANALYST,
)

_SKILL_LABEL = {
    "sql": "SQL",
    "power bi": "Power BI",
    "python": "Python",
    "excel": "Excel",
    "machine learning": "Machine Learning",
    "nlp": "NLP",
    "deep learning": "Deep Learning",
    "generative ai": "Gen AI",
    "gen ai": "Gen AI",
    "large language model": "LLMs",
    "llm": "LLM",
}


def _pretty_skill(s: str) -> str:
    low = (s or "").strip().lower()
    return _SKILL_LABEL.get(low, s.strip().title() if s else "")


def _dedupe_hits_by_label(hits: list) -> list:
    seen = set()
    out = []
    for h in hits:
        lbl = _pretty_skill(h)
        if not lbl or lbl in seen:
            continue
        seen.add(lbl)
        out.append(h)
    return out


def _job_to_dict(job):
    if job is None:
        return {}
    if isinstance(job, pd.Series):
        return job.to_dict()
    return dict(job)


def _description_text(job_dict):
    d = job_dict.get("description")
    if d is None or (isinstance(d, float) and math.isnan(d)):
        return ""
    if isinstance(d, str) and not d.strip():
        return ""
    return str(d).strip()


def _field_text(val):
    if val is None:
        return ""
    try:
        if isinstance(val, float) and math.isnan(val):
            return ""
    except TypeError:
        pass
    s = str(val).strip()
    return "" if s.lower() == "nan" else s


def jd_skill_bullets(description: str, max_items: int = 4) -> str:
    """Short line listing which of MY_SKILLS appear in the posting."""
    if not description:
        return ""
    low = description.lower()
    hits = _dedupe_hits_by_label([s for s in MY_SKILLS if s in low])
    if not hits:
        return ""
    show = [_pretty_skill(h) for h in hits[:max_items]]
    return "Posting highlights vs my profile: " + ", ".join(show) + "."


def jd_fit_paragraph(description: str, for_data_science: bool = False) -> str:
    """One tailored paragraph referencing overlap between JD and your stack."""
    if not description:
        return ""
    low = description.lower()
    hits = _dedupe_hits_by_label([s for s in MY_SKILLS if s in low])
    if not hits:
        return (
            "I reviewed your posting and can adapt quickly to the tools and metrics "
            "you prioritize for this role."
        )
    tools = ", ".join(_pretty_skill(h) for h in hits[:5])
    if for_data_science:
        return (
            f"Your posting emphasizes {tools}. That aligns with my current Data Science internship work "
            f"and my {YEARS_DATA_ANALYST:g}-year foundation in hands-on analytics and delivery."
        )
    return (
        f"Your posting emphasizes {tools}, which matches how I have delivered analysis, "
        "dashboards, and stakeholder-ready insights in past roles."
    )


def infer_application_role(job) -> str:
    """Return 'data_analyst' or 'data_science' from title/description."""
    d = _job_to_dict(job)
    text = f"{d.get('title', '')} {d.get('description', '')}".lower()
    ds_hits = sum(
        1
        for kw in (
            "data scientist",
            "machine learning",
            "ml engineer",
            "deep learning",
            "nlp",
            "llm",
            "generative ai",
            "gen ai",
            "ai engineer",
            "research scientist",
        )
        if kw in text
    )
    da_hits = sum(
        1
        for kw in (
            "data analyst",
            "business analyst",
            "bi developer",
            "reporting analyst",
            "analytics engineer",
        )
        if kw in text
    )
    if ds_hits > da_hits:
        return "data_science"
    if da_hits > ds_hits:
        return "data_analyst"
    if "data scientist" in text:
        return "data_science"
    return "data_analyst"


def _shared_apply_footer(job_dict):
    extra = jd_skill_bullets(_description_text(job_dict))
    return ("\n" + extra) if extra else ""


def generate_quick_answers_da(job=None):
    """Use when applying to Data Analyst / BI / analytics roles."""
    job_dict = _job_to_dict(job)
    base = f"""
Name: {NAME}
Total experience: {TOTAL_YEARS_EXPERIENCE:g} years
Data Analyst experience: {YEARS_DATA_ANALYST:g} years (SQL, Power BI, Python, Excel)
Currently: {DATA_SCIENCE_STATUS} - projects building toward {DATA_SCIENCE_PROJECT_AREAS}
Skills: SQL, Power BI, Python, Excel
Notice Period: Immediate
Location: {LOCATION}
Work arrangement: {WORK_PREFERENCE}
""".strip()
    return (base + _shared_apply_footer(job_dict)).strip()


def generate_quick_answers_ds(job=None):
    """Use when applying to Data Scientist / ML / AI roles."""
    job_dict = _job_to_dict(job)
    base = f"""
Name: {NAME}
Total experience: {TOTAL_YEARS_EXPERIENCE:g} years
Foundation: {YEARS_DATA_ANALYST:g} years as Data Analyst (SQL, Power BI, Python, Excel, stakeholder delivery)
Currently: {DATA_SCIENCE_STATUS}
Hands-on project areas: {DATA_SCIENCE_PROJECT_AREAS}
Skills: SQL, Python, Power BI, Excel; plus ML / Gen AI / NLP / DL through internship projects
Notice Period: Immediate
Location: {LOCATION}
Work arrangement: {WORK_PREFERENCE}
""".strip()
    return (base + _shared_apply_footer(job_dict)).strip()


def generate_cover_letter_da(job):
    job_dict = _job_to_dict(job)
    desc = _description_text(job_dict)
    jd_extra = ""
    if desc:
        jd_extra = "\n\n" + jd_fit_paragraph(desc, for_data_science=False) + "\n"

    return f"""
Dear Hiring Manager,

I am applying for the {_field_text(job_dict.get("title"))} role at {_field_text(job_dict.get("company"))}.

I am based in {LOCATION} and am interested in hybrid and fully remote roles in {STATE}.

I have {TOTAL_YEARS_EXPERIENCE:g} years of overall professional experience, including {YEARS_DATA_ANALYST:g} years focused on Data Analysis
with strong delivery in SQL, Power BI, Python, and Excel. I am currently in a {DATA_SCIENCE_STATUS}, developing hands-on work in {DATA_SCIENCE_PROJECT_AREAS} in addition to analytics delivery.{jd_extra}
I am open to {WORK_PREFERENCE.lower()} arrangements and can align with your team's working model.

I am confident I can contribute effectively to your team.

Regards,
{NAME}
""".strip()


def generate_cover_letter_ds(job):
    job_dict = _job_to_dict(job)
    desc = _description_text(job_dict)
    jd_extra = ""
    if desc:
        jd_extra = "\n\n" + jd_fit_paragraph(desc, for_data_science=True) + "\n"

    return f"""
Dear Hiring Manager,

I am applying for the {_field_text(job_dict.get("title"))} role at {_field_text(job_dict.get("company"))}.

I am based in {LOCATION} and am interested in hybrid and fully remote roles in {STATE}.

With {TOTAL_YEARS_EXPERIENCE:g} years in industry and {YEARS_DATA_ANALYST:g} years as a Data Analyst, I bring a solid track record in SQL, Python, visualization, and stakeholder-facing analytics.
I am now in a {DATA_SCIENCE_STATUS}, applying {DATA_SCIENCE_PROJECT_AREAS} through structured projects and experiments, alongside stakeholder-ready analytics from my analyst background.{jd_extra}
I am open to {WORK_PREFERENCE.lower()} arrangements and can align with your team's working model.

I am confident I can contribute effectively to your team.

Regards,
{NAME}
""".strip()


def generate_quick_answers(job=None):
    """Picks DA vs DS wording using the job title/description when ``job`` is provided."""
    if job is None:
        return generate_quick_answers_da(None)
    if infer_application_role(job) == "data_science":
        return generate_quick_answers_ds(job)
    return generate_quick_answers_da(job)


def generate_cover_letter(job):
    if job is None:
        return generate_cover_letter_da(None)
    if infer_application_role(job) == "data_science":
        return generate_cover_letter_ds(job)
    return generate_cover_letter_da(job)


def generate_real_workflow():
    return """
HOW YOU USE THIS (REAL WORKFLOW)
Step 1:
python main.py
Step 2 (optional auto-assist, Playwright installed):
python main.py --auto-apply
Step 3:
Review Easy Apply forms - automation may need manual fixes per employer
Step 4:
Paste or confirm:
Quick answers
Cover letter

Done in a few minutes
""".strip()


def generate_pro_tips():
    return """
PRO TIPS (THIS MAKES YOU WIN)
Always filter:
Easy Apply jobs only
Apply within:
First 30-60 minutes of posting
Use:
DA resume (70%)
DS resume (30%)
""".strip()
