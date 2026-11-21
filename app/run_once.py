"""Bir martalik qidiruv: GitHub Actions har 30 daqiqada shu faylni ishga tushiradi.

1. Saytlardan yangi e'lonlarni yig'adi (dublikatlarsiz, data/jobs.db bo'yicha).
2. Ularni Telegramga yuboradi.
3. Tugmalar (Topshirish / Rad etish) uchun Vercel webhook manzilini Telegramga eslatib qo'yadi.
"""
import asyncio
import hashlib
import logging
import os
import re

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramForbiddenError, TelegramNotFound, TelegramUnauthorizedError
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
    "🔗 <b>E'lonni ochish</b> — saytda o'zingiz topshirasiz\n"
    "✕ <b>Rad etish</b> — e'lon o'chib ketadi\n\n"
    "Bir e'lon bir nechta saytda bo'lsa ham, sizga faqat bir marta keladi."
)


def webhook_secret(token: str) -> str:
    return hashlib.sha256(f"ishtopish:{token}".encode()).hexdigest()[:48]


async def main() -> None:
    settings = load_settings()
    chat_raw = (os.environ.get("CHAT_ID") or "").strip()
    if not settings.bot_token:
        raise SystemExit("❌ BOT_TOKEN GitHub Secrets'da yo'q")
    if not re.fullmatch(r"\d{6,12}:[A-Za-z0-9_-]{30,}", settings.bot_token):
        raise SystemExit(
            "❌ BOT_TOKEN noto'g'ri ko'rinishda. U '123456789:AAH...' shaklida bo'lishi kerak "
            f"(hozir {len(settings.bot_token)} belgi). @BotFather > /mybots > bot > API Token dan qayta nusxalang."
        )
    if not re.fullmatch(r"-?\d{5,15}", chat_raw):
        raise SystemExit("❌ CHAT_ID faqat raqamlardan iborat bo'lishi kerak (@userinfobot ko'rsatgan Id)")
    chat_id = int(chat_raw)
    db = DB(settings.db_path)
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    try:
        try:
            me = await bot.get_me()
            log.info("bot: @%s", me.username)
        except (TelegramNotFound, TelegramUnauthorizedError):
            raise SystemExit(
                "❌ Telegram bu BOT_TOKEN ni tanimadi. @BotFather > /mybots > bot > API Token dan "
                "tokenni to'liq qayta nusxalab, GitHub Secrets'dagi BOT_TOKEN ni yangilang."
            ) from None
        try:
            await bot.send_chat_action(chat_id, "typing")
        except (TelegramForbiddenError, Exception) as e:  # noqa: BLE001
            raise SystemExit(
                f"❌ Bot sizga yoza olmayapti ({e}). Telegramda @{me.username} ni ochib Start bosing "
                "va CHAT_ID @userinfobot ko'rsatgan raqam ekanini tekshiring."
            ) from None
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

        profile = load_profile()
        jobs = await collect(settings, profile, db)
        limit = int(profile.get("max_per_run") or 0)
        if limit and len(jobs) > limit:
            # Qolganlarini bazadan o'chiramiz: keyingi qidiruvda yana topilib, yuboriladi
            for extra in jobs[limit:]:
                db.conn.execute("DELETE FROM jobs WHERE uid=?", (extra.uid,))
            db.conn.commit()
            jobs = jobs[:limit]
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
