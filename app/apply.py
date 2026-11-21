"""Accept bosilganda ariza yuborish: email orqali (rezyume biriktirilgan holda)."""
import asyncio
import mimetypes
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path

from .config import ROOT, Settings


def cover_letter(profile: dict, company: str, title: str) -> str:
    return f"""안녕하세요, {company} 채용 담당자님.

{title} 포지션에 지원하는 {profile.get('name_ko', '')}({profile.get('name_en', '')})입니다.

{(profile.get('summary_ko') or '').strip()}

- 언어: {', '.join(profile.get('languages') or [])}
- TOPIK: {profile.get('topik', '')}
- 체류자격: {profile.get('visa', '')}
- 거주지: {profile.get('location', '')}

이력서를 첨부드리오니 검토 부탁드립니다.
면접 기회를 주신다면 감사하겠습니다.

{profile.get('name_ko', '')} 드림
연락처: {profile.get('phone', '')} / {profile.get('email', '')}
"""


def attachments(profile: dict) -> list[Path]:
    out = []
    for p in profile.get("attachments") or []:
        path = (ROOT / p) if not Path(p).is_absolute() else Path(p)
        if path.exists():
            out.append(path)
    return out


def _send(settings: Settings, to: str, subject: str, body: str, files: list[Path]) -> None:
    msg = EmailMessage()
    msg["From"] = settings.smtp_user
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    for f in files:
        ctype, _ = mimetypes.guess_type(f.name)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        msg.add_attachment(f.read_bytes(), maintype=maintype, subtype=subtype, filename=f.name)
    with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=ssl.create_default_context()) as s:
        s.login(settings.smtp_user, settings.smtp_password)
        s.send_message(msg)


async def apply_by_email(settings: Settings, profile: dict, to: str, company: str, title: str) -> None:
    files = attachments(profile)
    if not files:
        raise RuntimeError("Rezyume fayli topilmadi (profile.yaml > attachments)")
    if not (settings.smtp_user and settings.smtp_password):
        raise RuntimeError("SMTP_USER / SMTP_PASSWORD sozlanmagan")
    subject = f"[입사지원] {title} - {profile.get('name_ko', '')}"
    body = cover_letter(profile, company, title)
    await asyncio.to_thread(_send, settings, to, subject, body, files)
