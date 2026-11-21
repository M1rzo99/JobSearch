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


_NUM = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(억|만\s*원|만원|만|천만)?")


def max_salary_manwon(text: str) -> int | None:
    """Maosh matnidan eng katta yillik summani 만원 da topish. Topilmasa None."""
    if not text or any(k in text for k in ("면접", "내규", "협의", "결정")) and not re.search(r"\d", text):
        return None
    monthly = "월" in text and "연봉" not in text
    best = None
    for num, unit in _NUM.findall(text):
        try:
            v = float(num.replace(",", ""))
        except ValueError:
            continue
        unit = (unit or "").replace(" ", "")
        if unit == "억":
            v *= 10000
        elif unit == "천만":
            v *= 1000
        elif not unit:
            if v >= 100000:        # won bilan yozilgan: 35,000,000
                v /= 10000
            elif v < 100:          # 시급/일당 yoki boshqa raqam
                continue
        if monthly:
            v *= 12
        best = v if best is None else max(best, v)
    return int(best) if best else None


def passes_filters(job: Job, profile: dict) -> bool:
    locs = profile.get("locations") or []
    if locs and job.location and not _any(job.location, locs):
        return False
    bad_types = profile.get("not_full_time") or []
    kind = f"{job.job_type} {job.title}"
    if bad_types and _any(kind, bad_types) and "정규직" not in job.job_type:
        return False
    min_sal = profile.get("min_salary_manwon")
    if min_sal:
        top = max_salary_manwon(job.salary)
        if top is not None and top < int(min_sal):
            return False
    return True


def score_job(job: Job, profile: dict) -> Job:
    head = " ".join([job.title, " ".join(job.tags)])
    if _any(head, profile.get("exclude") or []) or not passes_filters(job, profile):
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
