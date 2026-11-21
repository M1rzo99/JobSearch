"""E'lon sizga mosmi? Faqat profile.yaml dagi toifalardan biriga tushgan e'lonlar o'tadi."""
import re

from .models import Job

_LATIN = re.compile(r"^[A-Za-z0-9 .+#/-]+$")


def _has(text: str, kw: str) -> bool:
    """Lotin so'zlar butun so'z sifatida (masalan 'IT' 'with' ichida topilmasin), koreyscha esa matn ichida."""
    if _LATIN.match(kw):
        return re.search(rf"(?<![A-Za-z]){re.escape(kw)}(?![A-Za-z])", text, re.IGNORECASE) is not None
    return kw.lower() in text.lower()


def _any(text: str, words: list[str]) -> list[str]:
    return [w for w in words if _has(text, w)]


def match_category(job: Job, profile: dict) -> tuple[str, list[str]]:
    """Mos toifa nomi va topilgan so'zlar. Mos bo'lmasa ("", [])."""
    title = job.title
    full = " ".join([job.title, job.company, " ".join(job.tags), job.description])
    for name, rule in (profile.get("categories") or {}).items():
        where = title if rule.get("title_only") else full
        groups = rule.get("all") or []
        hits: list[str] = []
        ok = True
        for group in groups:
            found = _any(where, group)
            if not found:
                ok = False
                break
            hits += found
        if ok and groups:
            return name, hits
    return "", []


def score_job(job: Job, profile: dict) -> Job:
    head = " ".join([job.title, " ".join(job.tags)])
    if _any(head, profile.get("exclude") or []):
        job.score, job.matched = -1, []
        return job
    cat, hits = match_category(job, profile)
    if not cat:
        job.score, job.matched = 0, []
        return job
    score = 0
    for kw, pts in (profile.get("keywords") or {}).items():
        if _has(job.title, kw):
            score += int(pts) * 2
        elif _has(job.description, kw) or _has(head, kw):
            score += int(pts)
    job.score = max(score, 4)
    job.matched = [cat] + [h for h in dict.fromkeys(hits)][:5]
    return job
