"""Bir martalik qidiruv: GitHub Actions har 30 daqiqada shu faylni ishga tushiradi.

1. Saytlardan yangi e'lonlarni yig'adi (dublikatlarsiz, data/jobs.db bo'yicha).
2. Ularni Telegramga yuboradi.
3. Tugmalar (Topshirish / Rad etish) uchun Vercel webhook manzilini Telegramga eslatib qo'yadi.
"""
import asyncio
import hashlib
import logging
import os

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import LinkPreviewOptions

from .cards import job_keyboard, job_text
from .config import load_profile, load_settings
from .db import DB
from .pipeline import collect

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("run_once")

WELCOME = (
    "👋 <b>Ish Topish</b> ishga tushdi!\n\n"
    "Har 30 daqiqada Wanted, Saramin va JobKorea'dan sizga mos ishlarni topib, shu yerga yuboraman.\n\n"
    "✅ <b>Topshirish</b> — e'lon belgilanadi va saytning 즉시지원 sahifasi tugmasi chiqadi\n"
    "✕ <b>Rad etish</b> — e'lon o'chib ketadi\n\n"
    "Bir e'lon bir nechta saytda bo'lsa ham, sizga faqat bir marta keladi."
)


def webhook_secret(token: str) -> str:
    return hashlib.sha256(f"ishtopish:{token}".encode()).hexdigest()[:48]


async def main() -> None:
    settings = load_settings()
    chat_id = int(os.environ.get("CHAT_ID") or settings.owner_id or 0)
    if not settings.bot_token or not chat_id:
        raise SystemExit("BOT_TOKEN va CHAT_ID GitHub Secrets'da bo'lishi kerak")
    db = DB(settings.db_path)
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    try:
        hook = (os.environ.get("WEBHOOK_URL") or "").strip().rstrip("/")
        if hook:
            if not hook.startswith("http"):
                hook = "https://" + hook
            await bot.set_webhook(
                url=f"{hook}/api/telegram",
                secret_token=webhook_secret(settings.bot_token),
                allowed_updates=["message", "callback_query"],
            )
        if db.kv_get("welcomed") != "1":
            await bot.send_message(chat_id, WELCOME)
            db.kv_set("welcomed", "1")

        jobs = await collect(settings, load_profile(), db)
        log.info("yangi mos e'lonlar: %d", len(jobs))
        for job in jobs:
            msg = await bot.send_message(
                chat_id,
                job_text(job),
                reply_markup=job_keyboard(job.uid, job.url),
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
            db.set_message(job.uid, chat_id, msg.message_id)
            await asyncio.sleep(0.5)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
