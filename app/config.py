import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


@dataclass
class Settings:
    bot_token: str
    owner_id: int
    smtp_user: str
    smtp_password: str
    smtp_host: str
    smtp_port: int
    saramin_api_key: str
    interval_min: int
    min_score: int
    db_path: Path
    apply_mode: str


def load_settings() -> Settings:
    return Settings(
        bot_token=os.environ.get("BOT_TOKEN", ""),
        owner_id=int(os.environ.get("OWNER_ID") or 0),
        smtp_user=os.environ.get("SMTP_USER", ""),
        smtp_password=os.environ.get("SMTP_PASSWORD", ""),
        smtp_host=os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(os.environ.get("SMTP_PORT") or 465),
        saramin_api_key=os.environ.get("SARAMIN_API_KEY", ""),
        interval_min=int(os.environ.get("SEARCH_INTERVAL_MIN") or 30),
        min_score=int(os.environ.get("MIN_SCORE") or 4),
        db_path=ROOT / os.environ.get("DB_PATH", "data/jobs.db"),
        apply_mode=os.environ.get("APPLY_MODE", "platform").strip().lower(),
    )


def load_profile() -> dict:
    with open(ROOT / "profile.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)
