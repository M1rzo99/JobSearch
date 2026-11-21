"""Telegram xabar dizayni."""
import html
from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .models import Job

SOURCE = {
    "wanted": ("🟦", "Wanted"),
    "saramin": ("🟩", "Saramin"),
    "jobkorea": ("🟪", "JobKorea"),
}


def _e(s: str) -> str:
    return html.escape(s or "", quote=False)


def _stars(score: int) -> str:
    n = 5 if score >= 16 else 4 if score >= 11 else 3 if score >= 7 else 2 if score >= 4 else 1
    return "★" * n + "☆" * (5 - n)


APPLY_LABEL = {
    "saramin": "🚀 Saramin'da 즉시지원",
    "jobkorea": "🚀 JobKorea'da 즉시지원",
    "wanted": "🚀 Wanted'da 지원하기",
}


def job_text(job: Job, accepted_note: str = "", email_mode: bool = False) -> str:
    icon, src = SOURCE.get(job.source, ("▫️", job.source))
    lines = []
    if accepted_note:
        lines.append(f"✅ <b>TOPSHIRILDI</b> · {_e(accepted_note)}\n")
    lines.append(f"<b>{_e(job.title)}</b>")
    lines.append(f"🏢 {_e(job.company) or '—'}")
    meta = []
    if job.location:
        meta.append(f"📍 {_e(job.location)}")
    if job.job_type:
        meta.append(f"💼 {_e(job.job_type)}")
    if job.career:
        meta.append(f"🎓 {_e(job.career)}")
    if job.salary:
        meta.append(f"💰 {_e(job.salary)}")
    if meta:
        lines.append("  ".join(meta))
    if job.deadline:
        lines.append(f"⏳ {_e(job.deadline)}")
    lines.append("")
    lines.append(f"🎯 Moslik: <b>{_stars(job.score)}</b>")
    if job.matched:
        lines.append(" ".join(f"#{_e(m.replace(' ', '_'))}" for m in job.matched[:6]))
    if job.description:
        desc = _e(job.description.strip()[:900])
        lines.append(f"\n<blockquote expandable>{desc}</blockquote>")
    if email_mode and job.apply_email:
        how = "📧 Email orqali avtomatik topshiriladi"
    else:
        how = f"🚀 {src} rezyumeingiz bilan topshiriladi"
    lines.append(f"\n{icon} <i>{src}</i> · {how}")
    return "\n".join(lines)


def job_keyboard(uid: str, url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Topshirish", callback_data=f"acc|{uid}"),
            InlineKeyboardButton(text="✕ Rad etish", callback_data=f"rej|{uid}"),
        ],
        [InlineKeyboardButton(text="🔗 E'lonni ochish", url=url)],
    ])


def accepted_keyboard(url: str, source: str = "") -> InlineKeyboardMarkup:
    label = APPLY_LABEL.get(source, "🔗 E'lonni ochish")
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=label, url=url)]])


def now_str() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M")
