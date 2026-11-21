import asyncio
import logging
import random
import re

import httpx

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_EMAIL_SKIP = ("example.", "saramin", "jobkorea", "wanted.co.kr", "noreply", "no-reply", "privacy", ".png", ".jpg")


def find_apply_email(text: str) -> str:
    for m in EMAIL_RE.findall(text or ""):
        low = m.lower()
        if not any(s in low for s in _EMAIL_SKIP):
            return m
    return ""


def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True)


async def polite_sleep() -> None:
    # Saytlarga yuk tushirmaslik uchun so'rovlar orasida tanaffus
    await asyncio.sleep(random.uniform(1.5, 3.5))
