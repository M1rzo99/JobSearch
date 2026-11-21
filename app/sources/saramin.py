"""Saramin - kalit bo'lsa rasmiy Open API, bo'lmasa qidiruv sahifasi."""
import logging
import re
from datetime import datetime

from bs4 import BeautifulSoup

from ..models import Job
from .base import client, find_apply_email, polite_sleep

log = logging.getLogger(__name__)
BASE = "https://www.saramin.co.kr"
REC_RE = re.compile(r"rec_idx=(\d+)")


async def _search_api(c, q: str, key: str) -> list[Job]:
    r = await c.get(
        "https://oapi.saramin.co.kr/job-search",
        params={"access-key": key, "keywords": q, "count": 50, "sort": "pd"},
        headers={"Accept": "application/json"},
    )
    out = []
    for d in (r.json().get("jobs") or {}).get("job", []):
        pos = d.get("position") or {}
        exp = d.get("expiration-timestamp")
        out.append(Job(
            source="saramin",
            source_id=str(d.get("id")),
            url=d.get("url") or f"{BASE}/zf_user/jobs/relay/view?rec_idx={d.get('id')}",
            title=pos.get("title", ""),
            company=((d.get("company") or {}).get("detail") or {}).get("name", ""),
            location=(pos.get("location") or {}).get("name", "").replace("&gt;", ">"),
            salary=(d.get("salary") or {}).get("name", ""),
            job_type=(pos.get("job-type") or {}).get("name", ""),
            career=(pos.get("experience-level") or {}).get("name", ""),
            deadline=datetime.fromtimestamp(int(exp)).strftime("%Y-%m-%d") if exp else "",
            tags=[(d.get("keyword") or "")],
        ))
    return out


async def _search_html(c, q: str) -> list[Job]:
    r = await c.get(f"{BASE}/zf_user/search/recruit", params={"searchword": q, "recruitPageCount": 40, "recruitSort": "reg_dt"})
    soup = BeautifulSoup(r.text, "lxml")
    out = []
    for item in soup.select("div.item_recruit"):
        a = item.select_one("h2.job_tit a")
        if not a:
            continue
        m = REC_RE.search(a.get("href", ""))
        rec = item.get("value") or (m.group(1) if m else "")
        if not rec:
            continue
        corp = item.select_one("strong.corp_name a")
        cond = [s.get_text(strip=True) for s in item.select("div.job_condition span")]
        date = item.select_one("div.job_date span.date")
        out.append(Job(
            source="saramin",
            source_id=rec,
            url=f"{BASE}/zf_user/jobs/relay/view?rec_idx={rec}",
            title=a.get("title") or a.get_text(strip=True),
            company=corp.get_text(strip=True) if corp else "",
            location=cond[0] if len(cond) > 0 else "",
            career=cond[1] if len(cond) > 1 else "",
            job_type=cond[3] if len(cond) > 3 else "",
            deadline=date.get_text(strip=True) if date else "",
            tags=[s.get_text(strip=True) for s in item.select("div.job_sector a")],
        ))
    return out


async def search(queries: list[str], api_key: str = "") -> list[Job]:
    jobs: dict[str, Job] = {}
    async with client() as c:
        for q in queries:
            try:
                found = await (_search_api(c, q, api_key) if api_key else _search_html(c, q))
            except Exception as e:  # noqa: BLE001
                log.warning("saramin search %r failed: %s", q, e)
                continue
            for j in found:
                jobs.setdefault(j.source_id, j)
            await polite_sleep()
    return list(jobs.values())


async def enrich(job: Job) -> Job:
    async with client() as c:
        try:
            r = await c.get(f"{BASE}/zf_user/jobs/relay/view-detail", params={"rec_idx": job.source_id})
            text = BeautifulSoup(r.text, "lxml").get_text("\n", strip=True)
            job.description = text[:6000]
        except Exception as e:  # noqa: BLE001
            log.warning("saramin enrich %s failed: %s", job.uid, e)
    job.apply_email = find_apply_email(job.description)
    return job
