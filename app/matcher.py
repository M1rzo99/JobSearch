"""E'lon sizga qanchalik mosligini baholash."""
from .models import Job


def score_job(job: Job, profile: dict) -> Job:
    text = " ".join([job.title, job.company, job.description, " ".join(job.tags)]).lower()
    for bad in profile.get("exclude", []):
        if bad.lower() in text:
            job.score = -1
            return job
    score, matched = 0, []
    for kw, pts in (profile.get("keywords") or {}).items():
        if kw.lower() in text:
            # sarlavhada bo'lsa ikki barobar
            mult = 2 if kw.lower() in job.title.lower() else 1
            score += int(pts) * mult
            matched.append(kw)
    types = profile.get("job_types") or []
    if types and job.job_type and not any(t in job.job_type for t in types):
        score -= 3
    job.score, job.matched = score, matched
    return job
