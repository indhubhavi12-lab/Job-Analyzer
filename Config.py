# config.py
import os
from dotenv import load_dotenv
load_dotenv()

# Substrings for job-description matching (keep lowercase; longer phrases help Gen AI / LLM ads).
MY_SKILLS = [
    "sql",
    "power bi",
    "python",
    "excel",
    "machine learning",
    "nlp",
    "deep learning",
    "generative ai",
    "gen ai",
    "large language model",
    "llm",
]

NAME = "Indhu S"
EMAIL = "indhubhavi12@gmail.com"


# Email reports (main.py --email). Prefer environment: SMTP_PASSWORD, SMTP_USER, EMAIL_TO
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USE_TLS = True
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = ""  # sender; defaults to SMTP_USER if empty
EMAIL_TO = ""  # inbox for run summaries; defaults to EMAIL above if empty

# Experience (used in quick answers + cover letters)
TOTAL_YEARS_EXPERIENCE = 9
YEARS_DATA_ANALYST = 4.5
DATA_SCIENCE_STATUS = "Data Science internship (in progress)"

# DS internship / portfolio focus (shown in Data Science applications)
DATA_SCIENCE_PROJECT_AREAS = "Machine Learning, Python, Gen AI, NLP, and Deep Learning"

# Job search + application forms (LinkedIn location string)
CITY = "Coimbatore"
STATE = "Tamil Nadu"
LOCATION = f"{CITY}, {STATE}, India"

# How you want to work (used in quick answers + cover letter)
WORK_PREFERENCE = "Hybrid and remote"

# Job search (passed from main / CLI)
SEARCH_KEYWORD = "data analyst"

# Fetch full job posting text for top N results (then re-rank). Slower; more accurate matching.
DESCRIPTION_FETCH_LIMIT = 12
REQUEST_DELAY_SEC = 1.5

# Optional Playwright Easy Apply (see linkedin_apply.py). Use a dedicated profile dir to stay logged in.
LINKEDIN_USER_DATA_DIR = ""  # e.g. r"C:\Users\You\linkedin_pw_profile"

# Application history: each --auto-apply run appends to applications_log.jsonl (see application_tracker.py).
# Daily summary: schedule run_daily_report.bat or: python daily_report.py

ROLE_PRIORITY = {
    "data analyst": 5,
    "senior data analyst": 4,
    "data scientist": 2,
}

# Telegram (main.py --telegram). From @BotFather: TELEGRAM_TOKEN; chat id from @userinfobot
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
CHAT_ID = ""  # legacy alias for chat id (numeric or @channel)
