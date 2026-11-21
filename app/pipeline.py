"""Barcha saytlardan e'lon yig'ish, baholash va dublikatlarni ajratish."""
import asyncio
import logging

from .config import Settings
from .db import DB
from .matcher import score_job
from .models import Job
from .sources import jobkorea, saramin, wanted

log = logging.getLogger(__name__)
ENRICH = {"wanted": wanted.enrich, "saramin": saramin.enrich, "jobkorea": jobkorea.enrich}


async def collect(settings: Settings, profile: dict, db: DB) -> list[Job]:
    queries = profile.get("search_queries") or []
    results = await asyncio.gather(
        wanted.search(queries),
        saramin.search(queries, settings.saramin_api_key),
        jobkorea.search(queries),
        return_exceptions=True,
    )
    found: list[Job] = []
    for name, res in zip(("wanted", "saramin", "jobkorea"), results):
        if isinstance(res, Exception):
            log.warning("%s failed: %s", name, res)
            continue
        log.info("%s: %d e'lon", name, len(res))
        found.extend(res)

    fresh: list[Job] = []
    for job in found:
        if not job.title or db.find_duplicate(job):
            continue
        # Shu yig'ish ichida ham boshqa saytdagi nusxa bo'lishi mumkin
        db.add(job, "new")
        score_job(job, profile)                    # sarlavha bo'yicha tez baho
        if job.score < 0:
            db.set_status(job.uid, "skipped")
            continue
        try:
            await ENRICH[job.source](job)
        except Exception as e:  # noqa: BLE001
            log.warning("enrich %s: %s", job.uid, e)
        score_job(job, profile)                    # to'liq matn bo'yicha qayta baho
        if job.score < settings.min_score:
            db.set_status(job.uid, "skipped")
            continue
        db.conn.execute("UPDATE jobs SET score=?, apply_email=? WHERE uid=?", (job.score, job.apply_email, job.uid))
        db.conn.commit()
        fresh.append(job)
    fresh.sort(key=lambda j: j.score, reverse=True)
    return fresh
