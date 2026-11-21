"""JobKorea - qidiruv sahifasi. Sayt tuzilishi tez-tez o'zgaradi, shuning uchun
e'lon havolalari (/Recruit/GI_Read/<id>) bo'yicha o'qiymiz."""
import logging
import re

from bs4 import BeautifulSoup

from ..models import Job
from .base import client, find_apply_email, polite_sleep

log = logging.getLogger(__name__)
BASE = "https://www.jobkorea.co.kr"
GI_RE = re.compile(r"/Recruit/GI_Read/(\d+)")


def _card_of(a):
    node = a
    for _ in range(6):
        node = node.parent
        if node is None:
            return a
        if len(node.select('a[href*="/Recruit/GI_Read/"]')) >= 1 and len(node.get_text(" ", strip=True)) > 40:
            return node
    return node or a


async def search(queries: list[str]) -> list[Job]:
    jobs: dict[str, Job] = {}
    async with client() as c:
        for q in queries:
            try:
                r = await c.get(f"{BASE}/Search/", params={"stext": q, "tabType": "recruit", "Page_No": 1})
            except Exception as e:  # noqa: BLE001
                log.warning("jobkorea search %r failed: %s", q, e)
                continue
            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.select('a[href*="/Recruit/GI_Read/"]'):
                m = GI_RE.search(a.get("href", ""))
                title = (a.get("title") or a.get_text(" ", strip=True)).strip()
                if not m or len(title) < 4 or m.group(1) in jobs:
                    continue
                card = _card_of(a)
                corp = card.select_one('a[href*="/Recruit/Co_Read/"], a[href*="/company/"], .corp-name a, .name')
                spans = [s.get_text(strip=True) for s in card.select("span, li") if 1 < len(s.get_text(strip=True)) < 30]
                jobs[m.group(1)] = Job(
                    source="jobkorea",
                    source_id=m.group(1),
                    url=f"{BASE}/Recruit/GI_Read/{m.group(1)}",
                    title=title,
                    company=corp.get_text(strip=True) if corp else "",
                    location=next((s for s in spans if any(k in s for k in ("서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "강원", "충", "전", "경", "제주", "해외"))), ""),
                    deadline=next((s for s in spans if "~" in s or "마감" in s or "상시" in s), ""),
                )
            await polite_sleep()
    return list(jobs.values())


async def enrich(job: Job) -> Job:
    async with client() as c:
        try:
            r = await c.get(job.url)
            soup = BeautifulSoup(r.text, "lxml")
            if not job.company:
                og = soup.select_one('meta[property="og:title"]')
                if og and "|" in og.get("content", ""):
                    job.company = og["content"].split("|")[0].strip()
            job.description = soup.get_text("\n", strip=True)[:6000]
        except Exception as e:  # noqa: BLE001
            log.warning("jobkorea enrich %s failed: %s", job.uid, e)
    job.apply_email = find_apply_email(job.description)
    return job
