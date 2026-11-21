"""Wanted (wanted.co.kr) - saytning o'z JSON API'si orqali."""
import logging

from bs4 import BeautifulSoup

from ..models import Job
from .base import client, find_apply_email, polite_sleep

log = logging.getLogger(__name__)
BASE = "https://www.wanted.co.kr"


async def search(queries: list[str]) -> list[Job]:
    jobs: dict[str, Job] = {}
    async with client() as c:
        for q in queries:
            try:
                r = await c.get(
                    f"{BASE}/api/chaos/search/v1/results",
                    params={"query": q, "country": "kr", "job_sort": "job.latest_order", "limit": 30},
                )
                data = r.json().get("data", []) if r.status_code == 200 else []
                if not data:
                    r = await c.get(f"{BASE}/api/v4/jobs", params={"query": q, "country": "kr", "limit": 30})
                    data = r.json().get("data", []) if r.status_code == 200 else []
            except Exception as e:  # noqa: BLE001
                log.warning("wanted search %r failed: %s", q, e)
                continue
            for d in data:
                jid = str(d.get("id") or "")
                if not jid or jid in jobs:
                    continue
                comp = d.get("company") or {}
                addr = d.get("address") or {}
                jobs[jid] = Job(
                    source="wanted",
                    source_id=jid,
                    url=f"{BASE}/wd/{jid}",
                    title=d.get("position") or d.get("title") or "",
                    company=comp.get("name") or d.get("company_name") or "",
                    location=" ".join(filter(None, [addr.get("location"), addr.get("district")])),
                    deadline=d.get("due_time") or "상시채용",
                    tags=[t.get("title", "") for t in (d.get("category_tags") or []) if isinstance(t, dict)],
                )
            await polite_sleep()
    return list(jobs.values())


async def enrich(job: Job) -> Job:
    """E'lon tafsilotlari va ariza emailini olish."""
    async with client() as c:
        try:
            r = await c.get(f"{BASE}/api/v4/jobs/{job.source_id}")
            d = (r.json().get("job") or {}).get("detail") or {}
            parts = [d.get(k, "") for k in ("intro", "main_tasks", "requirements", "preferred_points", "benefits")]
            job.description = "\n\n".join(p for p in parts if p)
            job.career = str((r.json().get("job") or {}).get("annual_from", "") or "")
        except Exception:  # noqa: BLE001
            try:
                r = await c.get(job.url)
                job.description = BeautifulSoup(r.text, "lxml").get_text(" ", strip=True)[:4000]
            except Exception as e:  # noqa: BLE001
                log.warning("wanted enrich %s failed: %s", job.uid, e)
    job.apply_email = find_apply_email(job.description)
    return job
